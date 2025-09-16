#!/usr/bin/env python3
"""
データパイプラインのCLIスクリプト
"""

import sys
import argparse
import logging
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.data.processor import DataProcessor
from src.core.utils.config_loader import ConfigLoader


def setup_logging(level: str = "INFO"):
    """ログ設定"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/data_pipeline.log', encoding='utf-8')
        ]
    )


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="法律検索システム データパイプライン")
    
    parser.add_argument(
        "command",
        choices=["init", "collect", "process", "validate", "status", "cleanup"],
        help="実行するコマンド"
    )
    
    parser.add_argument(
        "--law-id",
        help="処理する法律ID（processコマンド用）"
    )
    
    parser.add_argument(
        "--xml-file",
        help="XMLファイルのパス（processコマンド用）"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="ログレベル"
    )
    
    parser.add_argument(
        "--config",
        help="設定ファイルのパス"
    )
    
    args = parser.parse_args()
    
    # ログ設定
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # 設定の読み込み
        config = ConfigLoader(args.config) if args.config else ConfigLoader()
        
        # データプロセッサーの作成
        with DataProcessor(config) as processor:
            
            if args.command == "init":
                # データベース初期化
                logger.info("データベースを初期化中...")
                if processor.initialize_database():
                    logger.info("✅ データベースの初期化が完了しました")
                else:
                    logger.error("❌ データベースの初期化に失敗しました")
                    sys.exit(1)
            
            elif args.command == "collect":
                # データ収集
                logger.info("e-Govデータを収集中...")
                download_results = processor.collector.download_all_tax_laws()
                
                success_count = sum(1 for r in download_results if r.success)
                total_count = len(download_results)
                
                logger.info(f"✅ データ収集完了: {success_count}/{total_count}件成功")
                
                # 失敗したものの詳細表示
                for result in download_results:
                    if not result.success:
                        logger.warning(f"❌ ダウンロード失敗: {result.law_id} - {result.error_message}")
            
            elif args.command == "process":
                if args.law_id:
                    # 単一法律の処理
                    logger.info(f"法律データを処理中: {args.law_id}")
                    result = processor.process_single_law(args.law_id, args.xml_file)
                    
                    if result["success"]:
                        logger.info(f"✅ 処理完了: {args.law_id}")
                        logger.info(f"  - 条文数: {result['articles_count']}")
                        logger.info(f"  - 埋め込み数: {result['embeddings_count']}")
                        logger.info(f"  - 保存文書数: {result['saved_documents']}")
                        logger.info(f"  - 処理時間: {result['processing_time']:.2f}秒")
                    else:
                        logger.error(f"❌ 処理失敗: {args.law_id} - {result['error']}")
                        sys.exit(1)
                else:
                    # 全税法の処理
                    logger.info("全税法データを処理中...")
                    result = processor.process_all_tax_laws()
                    
                    logger.info(f"✅ 処理完了:")
                    logger.info(f"  - 総法律数: {result['total_laws']}")
                    logger.info(f"  - 成功ダウンロード: {result['successful_downloads']}")
                    logger.info(f"  - 成功処理: {result['successful_processing']}")
                    logger.info(f"  - 総条文数: {result['total_articles']}")
                    logger.info(f"  - 総埋め込み数: {result['total_embeddings']}")
                    logger.info(f"  - 総処理時間: {result['total_time']:.2f}秒")
            
            elif args.command == "validate":
                # 妥当性検証
                logger.info("処理結果の妥当性を検証中...")
                validation = processor.validate_processing()
                
                if validation["valid"]:
                    logger.info("✅ 妥当性検証成功")
                    for check, status in validation["checks"].items():
                        logger.info(f"  - {check}: {status}")
                else:
                    logger.error("❌ 妥当性検証失敗")
                    for error in validation["errors"]:
                        logger.error(f"  - エラー: {error}")
                    for warning in validation["warnings"]:
                        logger.warning(f"  - 警告: {warning}")
                    sys.exit(1)
            
            elif args.command == "status":
                # 状況表示
                logger.info("処理状況を取得中...")
                status = processor.get_processing_status()
                
                # データ収集状況
                collection_status = status["collection_status"]
                logger.info("📊 データ収集状況:")
                logger.info(f"  - 総法律数: {collection_status['total_laws']}")
                logger.info(f"  - ダウンロード済み: {collection_status['downloaded_laws']}")
                logger.info(f"  - 不足: {len(collection_status['missing_laws'])}")
                logger.info(f"  - 総ファイルサイズ: {collection_status['total_file_size']:,} bytes")
                
                # データベース統計
                db_stats = status["database_stats"]
                if db_stats:
                    logger.info("🗄️ データベース統計:")
                    for collection, stats in db_stats["collections"].items():
                        logger.info(f"  - {collection}: {stats['count']}件 ({stats['size']:,} bytes)")
                
                # 処理統計
                processing_stats = status["processing_stats"]
                logger.info("⚙️ 処理統計:")
                logger.info(f"  - 総処理数: {processing_stats['total_processed']}")
                logger.info(f"  - 成功: {processing_stats['successful_processed']}")
                logger.info(f"  - 失敗: {processing_stats['failed_processed']}")
                logger.info(f"  - 総条文数: {processing_stats['total_articles']}")
                logger.info(f"  - 総埋め込み数: {processing_stats['total_embeddings']}")
                logger.info(f"  - 総処理時間: {processing_stats['processing_time']:.2f}秒")
            
            elif args.command == "cleanup":
                # クリーンアップ
                logger.info("古いデータをクリーンアップ中...")
                
                # 古いファイルの削除
                deleted_files = processor.collector.cleanup_old_files(days=30)
                logger.info(f"✅ 古いファイルを削除: {deleted_files}件")
                
                # 古い文書の削除
                deleted_docs = processor.database_manager.cleanup_old_documents(days=30)
                logger.info(f"✅ 古い文書を削除: {deleted_docs}件")
    
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"予期しないエラー: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
