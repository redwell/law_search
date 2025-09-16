"""
e-Govデータ収集モジュール
"""

import os
import requests
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

from src.core.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class LawMetadata:
    """法律メタデータ"""
    law_id: str
    law_name: str
    law_name_kana: Optional[str] = None
    law_number: Optional[str] = None
    promulgation_date: Optional[str] = None
    effective_date: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


@dataclass
class DownloadResult:
    """ダウンロード結果"""
    law_id: str
    success: bool
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    download_time: Optional[float] = None


class EGovDataCollector:
    """e-Govデータ収集クラス"""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        初期化
        
        Args:
            config: 設定ローダー
        """
        self.config = config or ConfigLoader()
        self.egov_config = self.config.get_egov_config()
        self.base_url = self.egov_config["base_url"]
        self.data_dir = Path(self.egov_config["data_dir"])
        self.timeout = self.egov_config.get("timeout", 60)
        
        # データディレクトリの作成
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # セッションの作成
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'LawSearch/1.0 (https://github.com/redwell/law_search)'
        })
        
        # 税法関連の法律ID（MVP用）
        self.tax_law_ids = [
            "M32HO089",  # 所得税法
            "M40HO034",  # 法人税法
            "M63HO108",  # 消費税法
            "M25HO073",  # 相続税法
            "M37HO028",  # 国税通則法
            "M37HO029",  # 国税徴収法
            "M37HO030",  # 国税犯則取締法
            "M37HO031",  # 国税犯則取締法施行令
            "M37HO032",  # 国税犯則取締法施行規則
            "M37HO033",  # 国税犯則取締法施行細則
        ]
    
    def get_law_metadata(self, law_id: str) -> Optional[LawMetadata]:
        """
        法律のメタデータを取得
        
        Args:
            law_id: 法律ID
            
        Returns:
            法律メタデータ
        """
        try:
            # 法律情報APIのエンドポイント
            metadata_url = f"{self.base_url}/api/opendata/{law_id}/metadata"
            
            response = self.session.get(metadata_url, timeout=self.timeout)
            response.raise_for_status()
            
            metadata = response.json()
            
            return LawMetadata(
                law_id=law_id,
                law_name=metadata.get("law_name", ""),
                law_name_kana=metadata.get("law_name_kana"),
                law_number=metadata.get("law_number"),
                promulgation_date=metadata.get("promulgation_date"),
                effective_date=metadata.get("effective_date"),
                category=metadata.get("category"),
                description=metadata.get("description")
            )
            
        except Exception as e:
            logger.error(f"法律メタデータの取得に失敗: {law_id}, エラー: {str(e)}")
            return None
    
    def download_law_xml(self, law_id: str) -> DownloadResult:
        """
        法律のXMLデータをダウンロード
        
        Args:
            law_id: 法律ID
            
        Returns:
            ダウンロード結果
        """
        start_time = time.time()
        
        try:
            # XMLデータのURL
            xml_url = f"{self.base_url}/api/opendata/{law_id}.xml"
            
            logger.info(f"法律データをダウンロード中: {law_id}")
            
            response = self.session.get(xml_url, timeout=self.timeout)
            response.raise_for_status()
            
            # ファイルパスの決定
            file_path = self.data_dir / f"{law_id}.xml"
            
            # ファイルの保存
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # ファイルサイズの取得
            file_size = file_path.stat().st_size
            download_time = time.time() - start_time
            
            logger.info(f"ダウンロード完了: {law_id}, サイズ: {file_size} bytes, 時間: {download_time:.2f}秒")
            
            return DownloadResult(
                law_id=law_id,
                success=True,
                file_path=str(file_path),
                file_size=file_size,
                download_time=download_time
            )
            
        except requests.exceptions.RequestException as e:
            error_message = f"HTTPエラー: {str(e)}"
            logger.error(f"ダウンロード失敗: {law_id}, {error_message}")
            
            return DownloadResult(
                law_id=law_id,
                success=False,
                error_message=error_message,
                download_time=time.time() - start_time
            )
            
        except Exception as e:
            error_message = f"予期しないエラー: {str(e)}"
            logger.error(f"ダウンロード失敗: {law_id}, {error_message}")
            
            return DownloadResult(
                law_id=law_id,
                success=False,
                error_message=error_message,
                download_time=time.time() - start_time
            )
    
    def download_all_tax_laws(self) -> List[DownloadResult]:
        """
        全ての税法データをダウンロード
        
        Returns:
            ダウンロード結果のリスト
        """
        logger.info(f"税法データの一括ダウンロードを開始: {len(self.tax_law_ids)}件")
        
        results = []
        
        for i, law_id in enumerate(self.tax_law_ids, 1):
            logger.info(f"進捗: {i}/{len(self.tax_law_ids)} - {law_id}")
            
            # ダウンロード実行
            result = self.download_law_xml(law_id)
            results.append(result)
            
            # サーバーへの負荷軽減のため待機
            if i < len(self.tax_law_ids):
                time.sleep(1)
        
        # 結果の集計
        success_count = sum(1 for r in results if r.success)
        total_size = sum(r.file_size for r in results if r.file_size)
        total_time = sum(r.download_time for r in results if r.download_time)
        
        logger.info(f"ダウンロード完了: 成功 {success_count}/{len(results)}件, "
                   f"総サイズ: {total_size:,} bytes, 総時間: {total_time:.2f}秒")
        
        return results
    
    def get_downloaded_files(self) -> List[Dict[str, Any]]:
        """
        ダウンロード済みファイルの一覧を取得
        
        Returns:
            ファイル情報のリスト
        """
        files = []
        
        for file_path in self.data_dir.glob("*.xml"):
            stat = file_path.stat()
            files.append({
                "filename": file_path.name,
                "law_id": file_path.stem,
                "file_path": str(file_path),
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        return sorted(files, key=lambda x: x["filename"])
    
    def cleanup_old_files(self, days: int = 30) -> int:
        """
        古いファイルを削除
        
        Args:
            days: 削除対象の日数
            
        Returns:
            削除されたファイル数
        """
        cutoff_time = time.time() - (days * 24 * 60 * 60)
        deleted_count = 0
        
        for file_path in self.data_dir.glob("*.xml"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    deleted_count += 1
                    logger.info(f"古いファイルを削除: {file_path.name}")
                except Exception as e:
                    logger.error(f"ファイル削除エラー: {file_path.name}, {str(e)}")
        
        logger.info(f"古いファイルの削除完了: {deleted_count}件")
        return deleted_count
    
    def validate_downloaded_file(self, law_id: str) -> bool:
        """
        ダウンロード済みファイルの妥当性を検証
        
        Args:
            law_id: 法律ID
            
        Returns:
            妥当性
        """
        file_path = self.data_dir / f"{law_id}.xml"
        
        if not file_path.exists():
            logger.warning(f"ファイルが存在しません: {law_id}")
            return False
        
        try:
            # ファイルサイズのチェック
            file_size = file_path.stat().st_size
            if file_size < 100:  # 100バイト未満は異常
                logger.warning(f"ファイルサイズが小さすぎます: {law_id}, {file_size} bytes")
                return False
            
            # XMLの基本構文チェック
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read(1000)  # 最初の1000文字をチェック
                
                if not content.strip().startswith('<?xml'):
                    logger.warning(f"XMLファイルではありません: {law_id}")
                    return False
                
                if '<law' not in content and '<Law' not in content:
                    logger.warning(f"法律データの形式が正しくありません: {law_id}")
                    return False
            
            logger.info(f"ファイル検証成功: {law_id}")
            return True
            
        except Exception as e:
            logger.error(f"ファイル検証エラー: {law_id}, {str(e)}")
            return False
    
    def get_collection_status(self) -> Dict[str, Any]:
        """
        データ収集の状況を取得
        
        Returns:
            収集状況
        """
        downloaded_files = self.get_downloaded_files()
        downloaded_law_ids = {f["law_id"] for f in downloaded_files}
        
        status = {
            "total_laws": len(self.tax_law_ids),
            "downloaded_laws": len(downloaded_law_ids),
            "missing_laws": [law_id for law_id in self.tax_law_ids if law_id not in downloaded_law_ids],
            "total_file_size": sum(f["file_size"] for f in downloaded_files),
            "last_update": max((f["modified_time"] for f in downloaded_files), default=None),
            "files": downloaded_files
        }
        
        return status
    
    def close(self):
        """リソースのクリーンアップ"""
        self.session.close()
        logger.info("データ収集セッションをクローズしました")
