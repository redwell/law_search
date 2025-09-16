"""
ArangoDB操作モジュール
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import json

from arango import ArangoClient
from arango.database import StandardDatabase
from arango.collection import StandardCollection
from arango.exceptions import ArangoError

from src.core.data.parser import Article, LawDocument
from src.core.data.embedding_generator import EmbeddingResult
from src.core.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class DatabaseManager:
    """ArangoDB管理クラス"""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        初期化
        
        Args:
            config: 設定ローダー
        """
        self.config = config or ConfigLoader()
        self.database_url = self.config.get_database_url()
        self.database_name = self.config.get("DATABASE_NAME", "law_search")
        
        # ArangoDBクライアントの初期化
        self.client = None
        self.db = None
        self._initialize_connection()
        
        # コレクション名
        self.documents_collection = "documents"
        self.law_relationships_collection = "law_relationships"
        self.article_relationships_collection = "article_relationships"
    
    def _initialize_connection(self):
        """ArangoDB接続の初期化"""
        try:
            logger.info(f"ArangoDBに接続中: {self.database_url}")
            
            # クライアントの作成
            self.client = ArangoClient(self.database_url)
            
            # データベースの取得または作成
            if not self.client.has_database(self.database_name):
                logger.info(f"データベースを作成: {self.database_name}")
                self.client.create_database(self.database_name)
            
            # データベース接続
            self.db = self.client.db(self.database_name)
            
            logger.info("ArangoDB接続が完了しました")
            
        except Exception as e:
            logger.error(f"ArangoDB接続エラー: {str(e)}")
            raise
    
    def create_collections(self) -> bool:
        """
        コレクションを作成
        
        Returns:
            作成成功フラグ
        """
        try:
            logger.info("コレクションを作成中...")
            
            # 文書コレクションの作成
            if not self.db.has_collection(self.documents_collection):
                self.db.create_collection(
                    self.documents_collection,
                    key_generator='autoincrement',
                    schema={
                        'rule': {
                            'type': 'object',
                            'properties': {
                                'law_id': {'type': 'string'},
                                'article_number': {'type': 'string'},
                                'content': {'type': 'string'},
                                'embedding': {'type': 'array', 'items': {'type': 'number'}},
                                'metadata': {'type': 'object'}
                            },
                            'required': ['law_id', 'article_number', 'content']
                        },
                        'level': 'moderate'
                    }
                )
                logger.info(f"コレクションを作成: {self.documents_collection}")
            
            # 法律関係コレクションの作成
            if not self.db.has_collection(self.law_relationships_collection):
                self.db.create_collection(
                    self.law_relationships_collection,
                    edge=True,
                    key_generator='autoincrement'
                )
                logger.info(f"コレクションを作成: {self.law_relationships_collection}")
            
            # 条文関係コレクションの作成
            if not self.db.has_collection(self.article_relationships_collection):
                self.db.create_collection(
                    self.article_relationships_collection,
                    edge=True,
                    key_generator='autoincrement'
                )
                logger.info(f"コレクションを作成: {self.article_relationships_collection}")
            
            logger.info("コレクションの作成が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"コレクション作成エラー: {str(e)}")
            return False
    
    def create_indexes(self) -> bool:
        """
        インデックスを作成
        
        Returns:
            作成成功フラグ
        """
        try:
            logger.info("インデックスを作成中...")
            
            # 全文検索インデックス
            if not self._has_fulltext_index():
                self.db.collection(self.documents_collection).add_fulltext_index(
                    fields=['content'],
                    min_length=2
                )
                logger.info("全文検索インデックスを作成")
            
            # 複合インデックス
            if not self._has_compound_index():
                self.db.collection(self.documents_collection).add_index(
                    type='persistent',
                    fields=['law_id', 'article_number'],
                    unique=False
                )
                logger.info("複合インデックスを作成")
            
            # 日付インデックス
            if not self._has_date_index():
                self.db.collection(self.documents_collection).add_index(
                    type='persistent',
                    fields=['metadata.effective_date'],
                    unique=False
                )
                logger.info("日付インデックスを作成")
            
            logger.info("インデックスの作成が完了しました")
            return True
            
        except Exception as e:
            logger.error(f"インデックス作成エラー: {str(e)}")
            return False
    
    def _has_fulltext_index(self) -> bool:
        """全文検索インデックスの存在確認"""
        try:
            indexes = self.db.collection(self.documents_collection).indexes()
            return any(idx['type'] == 'fulltext' for idx in indexes)
        except:
            return False
    
    def _has_compound_index(self) -> bool:
        """複合インデックスの存在確認"""
        try:
            indexes = self.db.collection(self.documents_collection).indexes()
            return any(
                idx['type'] == 'persistent' and 
                set(idx.get('fields', [])) == {'law_id', 'article_number'}
                for idx in indexes
            )
        except:
            return False
    
    def _has_date_index(self) -> bool:
        """日付インデックスの存在確認"""
        try:
            indexes = self.db.collection(self.documents_collection).indexes()
            return any(
                idx['type'] == 'persistent' and 
                'metadata.effective_date' in idx.get('fields', [])
                for idx in indexes
            )
        except:
            return False
    
    def insert_document(self, embedding_result: EmbeddingResult) -> Optional[str]:
        """
        文書を挿入
        
        Args:
            embedding_result: 埋め込み結果
            
        Returns:
            挿入された文書のキー
        """
        try:
            # 文書データの準備
            document = {
                'law_id': embedding_result.law_id,
                'article_number': embedding_result.article_number,
                'content': embedding_result.content,
                'embedding': embedding_result.embedding,
                'metadata': {
                    **(embedding_result.metadata or {}),
                    'model_name': embedding_result.model_name,
                    'generation_time': embedding_result.generation_time,
                    'inserted_at': datetime.now().isoformat()
                }
            }
            
            # 文書の挿入
            result = self.db.collection(self.documents_collection).insert(document)
            
            logger.debug(f"文書を挿入: {embedding_result.law_id}-{embedding_result.article_number}")
            return result['_key']
            
        except Exception as e:
            logger.error(f"文書挿入エラー: {embedding_result.law_id}-{embedding_result.article_number}, {str(e)}")
            return None
    
    def insert_documents_batch(self, embedding_results: List[EmbeddingResult]) -> List[str]:
        """
        バッチで文書を挿入
        
        Args:
            embedding_results: 埋め込み結果のリスト
            
        Returns:
            挿入された文書のキーのリスト
        """
        if not embedding_results:
            return []
        
        try:
            logger.info(f"バッチで文書を挿入中: {len(embedding_results)}件")
            
            # 文書データの準備
            documents = []
            for embedding_result in embedding_results:
                document = {
                    'law_id': embedding_result.law_id,
                    'article_number': embedding_result.article_number,
                    'content': embedding_result.content,
                    'embedding': embedding_result.embedding,
                    'metadata': {
                        **(embedding_result.metadata or {}),
                        'model_name': embedding_result.model_name,
                        'generation_time': embedding_result.generation_time,
                        'inserted_at': datetime.now().isoformat()
                    }
                }
                documents.append(document)
            
            # バッチ挿入
            results = self.db.collection(self.documents_collection).insert_many(documents)
            
            inserted_keys = [result['_key'] for result in results]
            logger.info(f"バッチ挿入完了: {len(inserted_keys)}件")
            
            return inserted_keys
            
        except Exception as e:
            logger.error(f"バッチ挿入エラー: {str(e)}")
            return []
    
    def search_documents_fulltext(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        全文検索
        
        Args:
            query: 検索クエリ
            limit: 結果の最大件数
            
        Returns:
            検索結果のリスト
        """
        try:
            aql = """
            FOR doc IN documents
            SEARCH ANALYZER(doc.content IN TOKENS(@query, 'text_ja'), 'text_ja')
            SORT BM25(doc) DESC
            LIMIT @limit
            RETURN {
                _key: doc._key,
                law_id: doc.law_id,
                article_number: doc.article_number,
                content: doc.content,
                metadata: doc.metadata,
                score: BM25(doc)
            }
            """
            
            cursor = self.db.aql.execute(aql, bind_vars={'query': query, 'limit': limit})
            results = list(cursor)
            
            logger.debug(f"全文検索完了: クエリ='{query}', 結果数={len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"全文検索エラー: {str(e)}")
            return []
    
    def search_documents_vector(self, query_embedding: List[float], limit: int = 10) -> List[Dict[str, Any]]:
        """
        ベクトル検索
        
        Args:
            query_embedding: クエリの埋め込みベクトル
            limit: 結果の最大件数
            
        Returns:
            検索結果のリスト
        """
        try:
            aql = """
            FOR doc IN documents
            LET similarity = 1 - COSINE_SIMILARITY(doc.embedding, @query_embedding)
            SORT similarity ASC
            LIMIT @limit
            RETURN {
                _key: doc._key,
                law_id: doc.law_id,
                article_number: doc.article_number,
                content: doc.content,
                metadata: doc.metadata,
                score: 1 - similarity
            }
            """
            
            cursor = self.db.aql.execute(aql, bind_vars={'query_embedding': query_embedding, 'limit': limit})
            results = list(cursor)
            
            logger.debug(f"ベクトル検索完了: 結果数={len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"ベクトル検索エラー: {str(e)}")
            return []
    
    def search_documents_hybrid(self, query: str, query_embedding: List[float], 
                               weights: Dict[str, float] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        ハイブリッド検索
        
        Args:
            query: 検索クエリ
            query_embedding: クエリの埋め込みベクトル
            weights: 重み付け
            limit: 結果の最大件数
            
        Returns:
            検索結果のリスト
        """
        if weights is None:
            weights = {'fulltext': 0.4, 'vector': 0.4, 'graph': 0.2}
        
        try:
            # 全文検索とベクトル検索を実行
            fulltext_results = self.search_documents_fulltext(query, limit * 2)
            vector_results = self.search_documents_vector(query_embedding, limit * 2)
            
            # 結果の統合
            combined_results = self._combine_search_results(
                fulltext_results, vector_results, weights
            )
            
            # 上位結果を返す
            final_results = combined_results[:limit]
            
            logger.debug(f"ハイブリッド検索完了: クエリ='{query}', 結果数={len(final_results)}")
            return final_results
            
        except Exception as e:
            logger.error(f"ハイブリッド検索エラー: {str(e)}")
            return []
    
    def _combine_search_results(self, fulltext_results: List[Dict[str, Any]], 
                               vector_results: List[Dict[str, Any]], 
                               weights: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        検索結果を統合
        
        Args:
            fulltext_results: 全文検索結果
            vector_results: ベクトル検索結果
            weights: 重み付け
            
        Returns:
            統合された検索結果
        """
        # 結果の正規化
        fulltext_scores = {r['_key']: r['score'] for r in fulltext_results}
        vector_scores = {r['_key']: r['score'] for r in vector_results}
        
        # スコアの正規化
        if fulltext_results:
            max_fulltext = max(fulltext_scores.values())
            min_fulltext = min(fulltext_scores.values())
            if max_fulltext > min_fulltext:
                for key in fulltext_scores:
                    fulltext_scores[key] = (fulltext_scores[key] - min_fulltext) / (max_fulltext - min_fulltext)
        
        if vector_results:
            max_vector = max(vector_scores.values())
            min_vector = min(vector_scores.values())
            if max_vector > min_vector:
                for key in vector_scores:
                    vector_scores[key] = (vector_scores[key] - min_vector) / (max_vector - min_vector)
        
        # 統合スコアの計算
        combined_scores = {}
        all_keys = set(fulltext_scores.keys()) | set(vector_scores.keys())
        
        for key in all_keys:
            fulltext_score = fulltext_scores.get(key, 0)
            vector_score = vector_scores.get(key, 0)
            
            combined_score = (
                fulltext_score * weights['fulltext'] +
                vector_score * weights['vector']
            )
            combined_scores[key] = combined_score
        
        # 結果の統合
        all_results = {r['_key']: r for r in fulltext_results + vector_results}
        
        # スコアでソート
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: combined_scores.get(x['_key'], 0),
            reverse=True
        )
        
        # 統合スコアを追加
        for result in sorted_results:
            result['combined_score'] = combined_scores.get(result['_key'], 0)
        
        return sorted_results
    
    def get_document_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """
        キーで文書を取得
        
        Args:
            key: 文書のキー
            
        Returns:
            文書データ
        """
        try:
            document = self.db.collection(self.documents_collection).get(key)
            return document
            
        except Exception as e:
            logger.error(f"文書取得エラー: {key}, {str(e)}")
            return None
    
    def get_documents_by_law_id(self, law_id: str) -> List[Dict[str, Any]]:
        """
        法律IDで文書を取得
        
        Args:
            law_id: 法律ID
            
        Returns:
            文書データのリスト
        """
        try:
            aql = """
            FOR doc IN documents
            FILTER doc.law_id == @law_id
            SORT doc.article_number
            RETURN doc
            """
            
            cursor = self.db.aql.execute(aql, bind_vars={'law_id': law_id})
            results = list(cursor)
            
            logger.debug(f"法律IDで文書取得: {law_id}, 結果数={len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"法律ID文書取得エラー: {law_id}, {str(e)}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        データベース統計を取得
        
        Returns:
            統計情報
        """
        try:
            # コレクション統計
            collection_stats = {}
            for collection_name in [self.documents_collection, self.law_relationships_collection, self.article_relationships_collection]:
                if self.db.has_collection(collection_name):
                    collection = self.db.collection(collection_name)
                    collection_stats[collection_name] = {
                        'count': collection.count(),
                        'size': collection.statistics()['figures']['documentsSize']
                    }
            
            # インデックス統計
            indexes = self.db.collection(self.documents_collection).indexes()
            
            stats = {
                'database_name': self.database_name,
                'collections': collection_stats,
                'indexes': len(indexes),
                'timestamp': datetime.now().isoformat()
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"データベース統計取得エラー: {str(e)}")
            return {}
    
    def cleanup_old_documents(self, days: int = 30) -> int:
        """
        古い文書を削除
        
        Args:
            days: 削除対象の日数
            
        Returns:
            削除された文書数
        """
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            cutoff_iso = datetime.fromtimestamp(cutoff_date).isoformat()
            
            aql = """
            FOR doc IN documents
            FILTER doc.metadata.inserted_at < @cutoff_date
            REMOVE doc IN documents
            RETURN OLD._key
            """
            
            cursor = self.db.aql.execute(aql, bind_vars={'cutoff_date': cutoff_iso})
            deleted_keys = list(cursor)
            
            logger.info(f"古い文書を削除: {len(deleted_keys)}件")
            return len(deleted_keys)
            
        except Exception as e:
            logger.error(f"古い文書削除エラー: {str(e)}")
            return 0
    
    def close(self):
        """接続をクローズ"""
        if self.client:
            self.client.close()
            logger.info("ArangoDB接続をクローズしました")
