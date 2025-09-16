"""
データ処理パイプラインの統合クラス
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import time

from src.core.data.collector import EGovDataCollector, DownloadResult
from src.core.data.parser import XMLParser, DataPreprocessor, LawDocument
from src.core.data.embedding_generator import EmbeddingGenerator, EmbeddingResult
from src.core.data.database_manager import DatabaseManager
from src.core.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class DataProcessor:
    """データ処理パイプラインの統合クラス"""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        初期化
        
        Args:
            config: 設定ローダー
        """
        self.config = config or ConfigLoader()
        
        # 各コンポーネントの初期化
        self.collector = EGovDataCollector(self.config)
        self.parser = XMLParser()
        self.preprocessor = DataPreprocessor()
        self.embedding_generator = EmbeddingGenerator(self.config)
        self.database_manager = DatabaseManager(self.config)
        
        # 処理統計
        self.stats = {
            'total_processed': 0,
            'successful_processed': 0,
            'failed_processed': 0,
            'total_articles': 0,
            'total_embeddings': 0,
            'processing_time': 0
        }
    
    def process_all_tax_laws(self) -> Dict[str, Any]:
        """
        全ての税法データを処理
        
        Returns:
            処理結果
        """
        logger.info("税法データの一括処理を開始")
        start_time = time.time()
        
        try:
            # 1. データ収集
            logger.info("ステップ1: データ収集")
            download_results = self.collector.download_all_tax_laws()
            
            # 2. データ処理
            logger.info("ステップ2: データ処理")
            processing_results = []
            
            for download_result in download_results:
                if download_result.success:
                    result = self.process_single_law(download_result.law_id, download_result.file_path)
                    processing_results.append(result)
                else:
                    logger.warning(f"ダウンロード失敗のためスキップ: {download_result.law_id}")
            
            # 3. 統計の計算
            total_time = time.time() - start_time
            self.stats['processing_time'] = total_time
            
            # 結果の集計
            result_summary = {
                'total_laws': len(download_results),
                'successful_downloads': sum(1 for r in download_results if r.success),
                'successful_processing': len(processing_results),
                'total_articles': sum(r.get('articles_count', 0) for r in processing_results),
                'total_embeddings': sum(r.get('embeddings_count', 0) for r in processing_results),
                'total_time': total_time,
                'download_results': download_results,
                'processing_results': processing_results,
                'stats': self.stats
            }
            
            logger.info(f"税法データの一括処理完了: {result_summary}")
            return result_summary
            
        except Exception as e:
            logger.error(f"税法データの一括処理エラー: {str(e)}")
            raise
    
    def process_single_law(self, law_id: str, xml_file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        単一の法律データを処理
        
        Args:
            law_id: 法律ID
            xml_file_path: XMLファイルのパス（省略時は自動検索）
            
        Returns:
            処理結果
        """
        logger.info(f"法律データの処理を開始: {law_id}")
        start_time = time.time()
        
        try:
            # ファイルパスの決定
            if xml_file_path is None:
                xml_file_path = self.collector.data_dir / f"{law_id}.xml"
                if not xml_file_path.exists():
                    raise FileNotFoundError(f"XMLファイルが見つかりません: {xml_file_path}")
            
            # 1. XMLパース
            logger.info(f"XMLパース: {law_id}")
            law_document = self.parser.parse_law_xml(str(xml_file_path))
            if not law_document:
                raise ValueError(f"XMLパースに失敗: {law_id}")
            
            # 2. データ前処理
            logger.info(f"データ前処理: {law_id}")
            processed_document = self.preprocessor.process_law_document(law_document)
            
            # 3. 埋め込み生成
            logger.info(f"埋め込み生成: {law_id}")
            embeddings = self.embedding_generator.generate_embeddings_for_law_document(processed_document)
            
            # 4. データベース保存
            logger.info(f"データベース保存: {law_id}")
            saved_keys = self.database_manager.insert_documents_batch(embeddings)
            
            # 処理時間の計算
            processing_time = time.time() - start_time
            
            # 結果の作成
            result = {
                'law_id': law_id,
                'success': True,
                'processing_time': processing_time,
                'articles_count': len(processed_document.articles),
                'embeddings_count': len(embeddings),
                'saved_documents': len(saved_keys),
                'law_info': {
                    'law_name': processed_document.law_name,
                    'law_number': processed_document.law_number,
                    'category': processed_document.category,
                    'effective_date': processed_document.effective_date
                },
                'metadata': {
                    'xml_file_path': str(xml_file_path),
                    'processed_at': datetime.now().isoformat(),
                    'model_name': self.embedding_generator.model_name
                }
            }
            
            # 統計の更新
            self.stats['total_processed'] += 1
            self.stats['successful_processed'] += 1
            self.stats['total_articles'] += len(processed_document.articles)
            self.stats['total_embeddings'] += len(embeddings)
            
            logger.info(f"法律データの処理完了: {law_id}, 条文数: {len(processed_document.articles)}, "
                       f"埋め込み数: {len(embeddings)}, 時間: {processing_time:.2f}秒")
            
            return result
            
        except Exception as e:
            logger.error(f"法律データの処理エラー: {law_id}, {str(e)}")
            
            # 統計の更新
            self.stats['total_processed'] += 1
            self.stats['failed_processed'] += 1
            
            return {
                'law_id': law_id,
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time,
                'articles_count': 0,
                'embeddings_count': 0,
                'saved_documents': 0
            }
    
    def initialize_database(self) -> bool:
        """
        データベースを初期化
        
        Returns:
            初期化成功フラグ
        """
        try:
            logger.info("データベースの初期化を開始")
            
            # コレクションの作成
            if not self.database_manager.create_collections():
                logger.error("コレクションの作成に失敗")
                return False
            
            # インデックスの作成
            if not self.database_manager.create_indexes():
                logger.error("インデックスの作成に失敗")
                return False
            
            logger.info("データベースの初期化が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"データベース初期化エラー: {str(e)}")
            return False
    
    def get_processing_status(self) -> Dict[str, Any]:
        """
        処理状況を取得
        
        Returns:
            処理状況
        """
        try:
            # データ収集状況
            collection_status = self.collector.get_collection_status()
            
            # データベース統計
            db_stats = self.database_manager.get_database_stats()
            
            # 処理統計
            processing_stats = self.stats.copy()
            
            status = {
                'collection_status': collection_status,
                'database_stats': db_stats,
                'processing_stats': processing_stats,
                'timestamp': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"処理状況取得エラー: {str(e)}")
            return {}
    
    def validate_processing(self) -> Dict[str, Any]:
        """
        処理結果の妥当性を検証
        
        Returns:
            検証結果
        """
        try:
            logger.info("処理結果の妥当性を検証中")
            
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': [],
                'checks': {}
            }
            
            # 1. データベース接続チェック
            try:
                db_stats = self.database_manager.get_database_stats()
                validation_result['checks']['database_connection'] = 'OK'
            except Exception as e:
                validation_result['errors'].append(f"データベース接続エラー: {str(e)}")
                validation_result['valid'] = False
            
            # 2. コレクション存在チェック
            try:
                if self.database_manager.db.has_collection(self.database_manager.documents_collection):
                    validation_result['checks']['documents_collection'] = 'OK'
                else:
                    validation_result['errors'].append("documentsコレクションが存在しません")
                    validation_result['valid'] = False
            except Exception as e:
                validation_result['errors'].append(f"コレクション確認エラー: {str(e)}")
                validation_result['valid'] = False
            
            # 3. インデックス存在チェック
            try:
                indexes = self.database_manager.db.collection(self.database_manager.documents_collection).indexes()
                if len(indexes) > 1:  # プライマリインデックス以外
                    validation_result['checks']['indexes'] = f'OK ({len(indexes)}個)'
                else:
                    validation_result['warnings'].append("インデックスが不足している可能性があります")
            except Exception as e:
                validation_result['warnings'].append(f"インデックス確認エラー: {str(e)}")
            
            # 4. データ存在チェック
            try:
                documents_count = self.database_manager.db.collection(self.database_manager.documents_collection).count()
                if documents_count > 0:
                    validation_result['checks']['data_exists'] = f'OK ({documents_count}件)'
                else:
                    validation_result['warnings'].append("データが存在しません")
            except Exception as e:
                validation_result['warnings'].append(f"データ確認エラー: {str(e)}")
            
            # 5. 埋め込みモデルチェック
            try:
                if self.embedding_generator.model:
                    validation_result['checks']['embedding_model'] = 'OK'
                else:
                    validation_result['errors'].append("埋め込みモデルが初期化されていません")
                    validation_result['valid'] = False
            except Exception as e:
                validation_result['errors'].append(f"埋め込みモデル確認エラー: {str(e)}")
                validation_result['valid'] = False
            
            logger.info(f"妥当性検証完了: 有効={validation_result['valid']}, "
                       f"エラー={len(validation_result['errors'])}, "
                       f"警告={len(validation_result['warnings'])}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"妥当性検証エラー: {str(e)}")
            return {
                'valid': False,
                'errors': [f"検証エラー: {str(e)}"],
                'warnings': [],
                'checks': {}
            }
    
    def cleanup_resources(self):
        """リソースのクリーンアップ"""
        try:
            logger.info("リソースのクリーンアップを開始")
            
            if self.collector:
                self.collector.close()
            
            if self.embedding_generator:
                self.embedding_generator.close()
            
            if self.database_manager:
                self.database_manager.close()
            
            logger.info("リソースのクリーンアップが完了しました")
            
        except Exception as e:
            logger.error(f"リソースクリーンアップエラー: {str(e)}")
    
    def __enter__(self):
        """コンテキストマネージャーの開始"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """コンテキストマネージャーの終了"""
        self.cleanup_resources()


def main():
    """メイン関数（テスト用）"""
    import sys
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        # データプロセッサーの作成
        with DataProcessor() as processor:
            # データベースの初期化
            if not processor.initialize_database():
                logger.error("データベースの初期化に失敗")
                sys.exit(1)
            
            # 処理の実行
            if len(sys.argv) > 1 and sys.argv[1] == "all":
                # 全税法データの処理
                result = processor.process_all_tax_laws()
                logger.info(f"処理結果: {result}")
            else:
                # 単一法律の処理（テスト用）
                test_law_id = "M32HO089"  # 所得税法
                result = processor.process_single_law(test_law_id)
                logger.info(f"処理結果: {result}")
            
            # 妥当性検証
            validation = processor.validate_processing()
            logger.info(f"妥当性検証: {validation}")
            
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
