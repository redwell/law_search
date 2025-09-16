"""
データ収集モジュールのテスト
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import requests

from src.core.data.collector import EGovDataCollector, LawMetadata, DownloadResult


class TestEGovDataCollector:
    """EGovDataCollectorのテストクラス"""
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリのフィクスチャ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_config(self):
        """モック設定のフィクスチャ"""
        config = Mock()
        config.get_egov_config.return_value = {
            "base_url": "https://elaws.e-gov.go.jp",
            "data_dir": "./data/egov",
            "timeout": 60
        }
        return config
    
    @pytest.fixture
    def collector(self, mock_config, temp_dir):
        """データ収集器のフィクスチャ"""
        with patch('src.core.data.collector.ConfigLoader', return_value=mock_config):
            collector = EGovDataCollector(mock_config)
            collector.data_dir = temp_dir
            return collector
    
    def test_init(self, mock_config):
        """初期化テスト"""
        with patch('src.core.data.collector.ConfigLoader', return_value=mock_config):
            collector = EGovDataCollector(mock_config)
            
            assert collector.config == mock_config
            assert collector.base_url == "https://elaws.e-gov.go.jp"
            assert collector.timeout == 60
            assert collector.session is not None
    
    def test_get_law_metadata_success(self, collector):
        """法律メタデータ取得成功テスト"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "law_name": "所得税法",
            "law_name_kana": "しょとくぜいほう",
            "law_number": "昭和32年法律第89号",
            "promulgation_date": "1957-03-31",
            "effective_date": "1957-04-01",
            "category": "税法",
            "description": "個人の所得に係る税金について定める法律"
        }
        mock_response.raise_for_status.return_value = None
        
        with patch.object(collector.session, 'get', return_value=mock_response):
            result = collector.get_law_metadata("M32HO089")
            
            assert result is not None
            assert result.law_id == "M32HO089"
            assert result.law_name == "所得税法"
            assert result.law_name_kana == "しょとくぜいほう"
            assert result.law_number == "昭和32年法律第89号"
    
    def test_get_law_metadata_failure(self, collector):
        """法律メタデータ取得失敗テスト"""
        with patch.object(collector.session, 'get', side_effect=requests.RequestException("Connection error")):
            result = collector.get_law_metadata("INVALID_ID")
            
            assert result is None
    
    def test_download_law_xml_success(self, collector):
        """法律XMLダウンロード成功テスト"""
        mock_response = Mock()
        mock_response.content = b'<?xml version="1.0"?><law>test content</law>'
        mock_response.raise_for_status.return_value = None
        
        with patch.object(collector.session, 'get', return_value=mock_response):
            result = collector.download_law_xml("M32HO089")
            
            assert result.success is True
            assert result.law_id == "M32HO089"
            assert result.file_path is not None
            assert result.file_size > 0
            assert result.error_message is None
            
            # ファイルが実際に作成されているかチェック
            file_path = Path(result.file_path)
            assert file_path.exists()
            assert file_path.stat().st_size > 0
    
    def test_download_law_xml_failure(self, collector):
        """法律XMLダウンロード失敗テスト"""
        with patch.object(collector.session, 'get', side_effect=requests.RequestException("Connection error")):
            result = collector.download_law_xml("INVALID_ID")
            
            assert result.success is False
            assert result.law_id == "INVALID_ID"
            assert result.file_path is None
            assert result.error_message is not None
            assert "Connection error" in result.error_message
    
    def test_download_all_tax_laws(self, collector):
        """全税法ダウンロードテスト"""
        mock_response = Mock()
        mock_response.content = b'<?xml version="1.0"?><law>test content</law>'
        mock_response.raise_for_status.return_value = None
        
        with patch.object(collector.session, 'get', return_value=mock_response):
            results = collector.download_all_tax_laws()
            
            assert len(results) == len(collector.tax_law_ids)
            assert all(result.success for result in results)
            assert all(result.file_path is not None for result in results)
    
    def test_get_downloaded_files(self, collector, temp_dir):
        """ダウンロード済みファイル一覧取得テスト"""
        # テストファイルを作成
        test_file = temp_dir / "M32HO089.xml"
        test_file.write_text("<?xml version='1.0'?><law>test</law>")
        
        files = collector.get_downloaded_files()
        
        assert len(files) == 1
        assert files[0]["filename"] == "M32HO089.xml"
        assert files[0]["law_id"] == "M32HO089"
        assert files[0]["file_size"] > 0
    
    def test_cleanup_old_files(self, collector, temp_dir):
        """古いファイル削除テスト"""
        import time
        
        # 古いファイルを作成
        old_file = temp_dir / "old_file.xml"
        old_file.write_text("old content")
        
        # ファイルの更新時間を古くする
        old_time = time.time() - (31 * 24 * 60 * 60)  # 31日前
        os.utime(old_file, (old_time, old_time))
        
        # 新しいファイルを作成
        new_file = temp_dir / "new_file.xml"
        new_file.write_text("new content")
        
        # 古いファイルの削除
        deleted_count = collector.cleanup_old_files(days=30)
        
        assert deleted_count == 1
        assert not old_file.exists()
        assert new_file.exists()
    
    def test_validate_downloaded_file_valid(self, collector, temp_dir):
        """ダウンロード済みファイル検証テスト（有効）"""
        # 有効なXMLファイルを作成（サイズを大きくする）
        xml_content = '''<?xml version="1.0"?>
<law>
    <Article>
        <ArticleNum>第1条</ArticleNum>
        <ArticleCaption>この法律は、個人の所得に係る税金について定める。</ArticleCaption>
    </Article>
    <Article>
        <ArticleNum>第2条</ArticleNum>
        <ArticleCaption>所得とは、個人の収入から必要経費を差し引いた金額をいう。</ArticleCaption>
    </Article>
</law>'''
        valid_file = temp_dir / "M32HO089.xml"
        valid_file.write_text(xml_content)
        
        result = collector.validate_downloaded_file("M32HO089")
        
        assert result is True
    
    def test_validate_downloaded_file_invalid(self, collector, temp_dir):
        """ダウンロード済みファイル検証テスト（無効）"""
        # 無効なファイルを作成
        invalid_file = temp_dir / "INVALID.xml"
        invalid_file.write_text("not xml content")
        
        result = collector.validate_downloaded_file("INVALID")
        
        assert result is False
    
    def test_validate_downloaded_file_not_exists(self, collector):
        """ダウンロード済みファイル検証テスト（存在しない）"""
        result = collector.validate_downloaded_file("NOTEXISTS")
        
        assert result is False
    
    def test_get_collection_status(self, collector, temp_dir):
        """データ収集状況取得テスト"""
        # テストファイルを作成
        test_file = temp_dir / "M32HO089.xml"
        test_file.write_text("<?xml version='1.0'?><law>test</law>")
        
        status = collector.get_collection_status()
        
        assert status["total_laws"] == len(collector.tax_law_ids)
        assert status["downloaded_laws"] == 1
        assert "M32HO089" not in status["missing_laws"]
        assert status["total_file_size"] > 0
        assert len(status["files"]) == 1
    
    def test_close(self, collector):
        """リソースクリーンアップテスト"""
        collector.close()
        
        # セッションがクローズされているかチェック
        # （実際のクローズ確認は難しいため、エラーが発生しないことを確認）
        assert True  # エラーが発生しなければ成功
