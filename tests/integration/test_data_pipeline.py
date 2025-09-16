"""
データパイプラインの統合テスト
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.core.data.processor import DataProcessor
from src.core.data.collector import EGovDataCollector, DownloadResult
from src.core.data.parser import LawDocument, Article
from src.core.data.embedding_generator import EmbeddingResult
from src.core.data.database_manager import DatabaseManager


class TestDataPipeline:
    """データパイプラインの統合テストクラス"""
    
    @pytest.fixture
    def mock_config(self):
        """モック設定のフィクスチャ"""
        config = Mock()
        config.get_egov_config.return_value = {
            "base_url": "https://elaws.e-gov.go.jp",
            "data_dir": "./data/egov",
            "timeout": 60
        }
        config.get_embedding_model.return_value = "jinaai/jina-embeddings-v3"
        config.get_database_url.return_value = "arangodb://root:password@localhost:8529"
        config.get.return_value = None
        return config
    
    @pytest.fixture
    def temp_dir(self):
        """一時ディレクトリのフィクスチャ"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_law_document(self):
        """サンプル法律文書のフィクスチャ"""
        articles = [
            Article(
                law_id="M32HO089",
                article_number="第1条",
                content="この法律は、個人の所得に係る税金について定める。",
                metadata={"original": "test"}
            ),
            Article(
                law_id="M32HO089",
                article_number="第2条",
                content="所得とは、個人の収入から必要経費を差し引いた金額をいう。",
                metadata={"original": "test"}
            )
        ]
        
        return LawDocument(
            law_id="M32HO089",
            law_name="所得税法",
            law_name_kana="しょとくぜいほう",
            law_number="昭和32年法律第89号",
            promulgation_date="1957-03-31",
            effective_date="1957-04-01",
            category="税法",
            description="個人の所得に係る税金について定める法律",
            articles=articles
        )
    
    @pytest.fixture
    def sample_embedding_results(self):
        """サンプル埋め込み結果のフィクスチャ"""
        return [
            EmbeddingResult(
                law_id="M32HO089",
                article_number="第1条",
                content="この法律は、個人の所得に係る税金について定める。",
                embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
                model_name="jinaai/jina-embeddings-v3",
                generation_time=0.1,
                metadata={"test": "data"}
            ),
            EmbeddingResult(
                law_id="M32HO089",
                article_number="第2条",
                content="所得とは、個人の収入から必要経費を差し引いた金額をいう。",
                embedding=[0.6, 0.7, 0.8, 0.9, 1.0],
                model_name="jinaai/jina-embeddings-v3",
                generation_time=0.1,
                metadata={"test": "data"}
            )
        ]
    
    @pytest.fixture
    def processor(self, mock_config):
        """データプロセッサーのフィクスチャ"""
        with patch('src.core.data.processor.ConfigLoader', return_value=mock_config):
            with patch('src.core.data.processor.EGovDataCollector'):
                with patch('src.core.data.processor.XMLParser'):
                    with patch('src.core.data.processor.DataPreprocessor'):
                        with patch('src.core.data.processor.EmbeddingGenerator'):
                            with patch('src.core.data.processor.DatabaseManager'):
                                processor = DataProcessor(mock_config)
                                return processor
    
    def test_processor_init(self, mock_config):
        """データプロセッサー初期化テスト"""
        with patch('src.core.data.processor.ConfigLoader', return_value=mock_config):
            with patch('src.core.data.processor.EGovDataCollector'):
                with patch('src.core.data.processor.XMLParser'):
                    with patch('src.core.data.processor.DataPreprocessor'):
                        with patch('src.core.data.processor.EmbeddingGenerator'):
                            with patch('src.core.data.processor.DatabaseManager'):
                                processor = DataProcessor(mock_config)
                                
                                assert processor.config == mock_config
                                assert processor.collector is not None
                                assert processor.parser is not None
                                assert processor.preprocessor is not None
                                assert processor.embedding_generator is not None
                                assert processor.database_manager is not None
                                assert processor.stats is not None
    
    def test_initialize_database_success(self, processor):
        """データベース初期化成功テスト"""
        processor.database_manager.create_collections.return_value = True
        processor.database_manager.create_indexes.return_value = True
        
        result = processor.initialize_database()
        
        assert result is True
        processor.database_manager.create_collections.assert_called_once()
        processor.database_manager.create_indexes.assert_called_once()
    
    def test_initialize_database_failure(self, processor):
        """データベース初期化失敗テスト"""
        processor.database_manager.create_collections.return_value = False
        
        result = processor.initialize_database()
        
        assert result is False
        processor.database_manager.create_collections.assert_called_once()
        processor.database_manager.create_indexes.assert_not_called()
    
    def test_process_single_law_success(self, processor, sample_law_document, sample_embedding_results):
        """単一法律処理成功テスト"""
        # モックの設定
        processor.parser.parse_law_xml.return_value = sample_law_document
        processor.preprocessor.process_law_document.return_value = sample_law_document
        processor.embedding_generator.generate_embeddings_for_law_document.return_value = sample_embedding_results
        processor.database_manager.insert_documents_batch.return_value = ["key1", "key2"]
        
        result = processor.process_single_law("M32HO089", "test.xml")
        
        assert result["success"] is True
        assert result["law_id"] == "M32HO089"
        assert result["articles_count"] == 2
        assert result["embeddings_count"] == 2
        assert result["saved_documents"] == 2
        assert result["law_info"]["law_name"] == "所得税法"
        assert result["law_info"]["category"] == "税法"
        
        # 統計の確認
        assert processor.stats["total_processed"] == 1
        assert processor.stats["successful_processed"] == 1
        assert processor.stats["total_articles"] == 2
        assert processor.stats["total_embeddings"] == 2
    
    def test_process_single_law_failure(self, processor):
        """単一法律処理失敗テスト"""
        processor.parser.parse_law_xml.return_value = None
        
        result = processor.process_single_law("INVALID_ID", "test.xml")
        
        assert result["success"] is False
        assert result["law_id"] == "INVALID_ID"
        assert result["articles_count"] == 0
        assert result["embeddings_count"] == 0
        assert result["saved_documents"] == 0
        assert "error" in result
        
        # 統計の確認
        assert processor.stats["total_processed"] == 1
        assert processor.stats["failed_processed"] == 1
    
    def test_process_all_tax_laws_success(self, processor, sample_law_document, sample_embedding_results):
        """全税法処理成功テスト"""
        # ダウンロード結果のモック
        download_results = [
            DownloadResult("M32HO089", True, "test1.xml", 1000, None, 1.0),
            DownloadResult("M40HO034", True, "test2.xml", 1000, None, 1.0)
        ]
        
        processor.collector.download_all_tax_laws.return_value = download_results
        processor.parser.parse_law_xml.return_value = sample_law_document
        processor.preprocessor.process_law_document.return_value = sample_law_document
        processor.embedding_generator.generate_embeddings_for_law_document.return_value = sample_embedding_results
        processor.database_manager.insert_documents_batch.return_value = ["key1", "key2"]
        
        result = processor.process_all_tax_laws()
        
        assert result["total_laws"] == 2
        assert result["successful_downloads"] == 2
        assert result["successful_processing"] == 2
        assert result["total_articles"] == 4  # 2法律 × 2条文
        assert result["total_embeddings"] == 4  # 2法律 × 2埋め込み
        assert result["total_time"] > 0
        assert len(result["download_results"]) == 2
        assert len(result["processing_results"]) == 2
    
    def test_get_processing_status(self, processor):
        """処理状況取得テスト"""
        # モックの設定
        processor.collector.get_collection_status.return_value = {"test": "collection"}
        processor.database_manager.get_database_stats.return_value = {"test": "database"}
        
        status = processor.get_processing_status()
        
        assert "collection_status" in status
        assert "database_stats" in status
        assert "processing_stats" in status
        assert "timestamp" in status
        assert status["collection_status"] == {"test": "collection"}
        assert status["database_stats"] == {"test": "database"}
    
    def test_validate_processing_success(self, processor):
        """処理妥当性検証成功テスト"""
        # モックの設定
        processor.database_manager.get_database_stats.return_value = {"test": "stats"}
        processor.database_manager.db.has_collection.return_value = True
        processor.database_manager.db.collection.return_value.indexes.return_value = [{"type": "primary"}, {"type": "fulltext"}]
        processor.database_manager.db.collection.return_value.count.return_value = 100
        processor.embedding_generator.model = Mock()
        
        result = processor.validate_processing()
        
        assert result["valid"] is True
        assert len(result["errors"]) == 0
        assert len(result["warnings"]) == 0
        assert "database_connection" in result["checks"]
        assert "documents_collection" in result["checks"]
        assert "indexes" in result["checks"]
        assert "data_exists" in result["checks"]
        assert "embedding_model" in result["checks"]
    
    def test_validate_processing_failure(self, processor):
        """処理妥当性検証失敗テスト"""
        # モックの設定（エラーケース）
        processor.database_manager.get_database_stats.side_effect = Exception("Connection error")
        processor.embedding_generator.model = None
        
        result = processor.validate_processing()
        
        assert result["valid"] is False
        assert len(result["errors"]) > 0
        assert "Connection error" in result["errors"][0]
        assert "埋め込みモデルが初期化されていません" in result["errors"]
    
    def test_cleanup_resources(self, processor):
        """リソースクリーンアップテスト"""
        processor.cleanup_resources()
        
        processor.collector.close.assert_called_once()
        processor.embedding_generator.close.assert_called_once()
        processor.database_manager.close.assert_called_once()
    
    def test_context_manager(self, mock_config):
        """コンテキストマネージャーテスト"""
        with patch('src.core.data.processor.ConfigLoader', return_value=mock_config):
            with patch('src.core.data.processor.EGovDataCollector'):
                with patch('src.core.data.processor.XMLParser'):
                    with patch('src.core.data.processor.DataPreprocessor'):
                        with patch('src.core.data.processor.EmbeddingGenerator'):
                            with patch('src.core.data.processor.DatabaseManager'):
                                with DataProcessor(mock_config) as processor:
                                    assert processor is not None
                                    assert processor.config == mock_config
                                
                                # クリーンアップが呼ばれることを確認
                                processor.collector.close.assert_called_once()
                                processor.embedding_generator.close.assert_called_once()
                                processor.database_manager.close.assert_called_once()
    
    def test_stats_tracking(self, processor, sample_law_document, sample_embedding_results):
        """統計追跡テスト"""
        # 初期統計の確認
        assert processor.stats["total_processed"] == 0
        assert processor.stats["successful_processed"] == 0
        assert processor.stats["failed_processed"] == 0
        assert processor.stats["total_articles"] == 0
        assert processor.stats["total_embeddings"] == 0
        
        # 成功ケースの処理
        processor.parser.parse_law_xml.return_value = sample_law_document
        processor.preprocessor.process_law_document.return_value = sample_law_document
        processor.embedding_generator.generate_embeddings_for_law_document.return_value = sample_embedding_results
        processor.database_manager.insert_documents_batch.return_value = ["key1", "key2"]
        
        processor.process_single_law("M32HO089", "test.xml")
        
        # 統計の更新確認
        assert processor.stats["total_processed"] == 1
        assert processor.stats["successful_processed"] == 1
        assert processor.stats["failed_processed"] == 0
        assert processor.stats["total_articles"] == 2
        assert processor.stats["total_embeddings"] == 2
        
        # 失敗ケースの処理
        processor.parser.parse_law_xml.return_value = None
        
        processor.process_single_law("INVALID_ID", "test.xml")
        
        # 統計の更新確認
        assert processor.stats["total_processed"] == 2
        assert processor.stats["successful_processed"] == 1
        assert processor.stats["failed_processed"] == 1
        assert processor.stats["total_articles"] == 2  # 失敗したので増えない
        assert processor.stats["total_embeddings"] == 2  # 失敗したので増えない
