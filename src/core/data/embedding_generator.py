"""
埋め込み生成モジュール
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime
import time
from pathlib import Path
import pickle

from sentence_transformers import SentenceTransformer
from src.core.data.parser import Article, LawDocument
from src.core.utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """埋め込み生成結果"""
    law_id: str
    article_number: str
    content: str
    embedding: List[float]
    model_name: str
    generation_time: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class EmbeddingBatch:
    """埋め込みバッチ"""
    results: List[EmbeddingResult]
    total_time: float
    batch_size: int
    model_name: str


class EmbeddingGenerator:
    """埋め込み生成クラス"""
    
    def __init__(self, config: Optional[ConfigLoader] = None):
        """
        初期化
        
        Args:
            config: 設定ローダー
        """
        self.config = config or ConfigLoader()
        self.model_name = self.config.get_embedding_model()
        self.batch_size = self.config.get("EMBEDDING_BATCH_SIZE", 32)
        self.timeout = self.config.get("EMBEDDING_TIMEOUT", 60)
        
        # モデルの初期化
        self.model = None
        self._initialize_model()
        
        # キャッシュディレクトリ
        self.cache_dir = Path("cache/embeddings")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_model(self):
        """埋め込みモデルの初期化"""
        try:
            logger.info(f"埋め込みモデルを初期化中: {self.model_name}")
            start_time = time.time()
            
            self.model = SentenceTransformer(self.model_name)
            
            init_time = time.time() - start_time
            logger.info(f"埋め込みモデルの初期化完了: {init_time:.2f}秒")
            
        except Exception as e:
            logger.error(f"埋め込みモデルの初期化に失敗: {str(e)}")
            raise
    
    def generate_embedding(self, text: str, law_id: str = "", article_number: str = "") -> Optional[EmbeddingResult]:
        """
        単一テキストの埋め込みを生成
        
        Args:
            text: テキスト
            law_id: 法律ID
            article_number: 条番号
            
        Returns:
            埋め込み結果
        """
        if not self.model:
            logger.error("埋め込みモデルが初期化されていません")
            return None
        
        try:
            start_time = time.time()
            
            # 埋め込みの生成
            embedding = self.model.encode(text, convert_to_tensor=False)
            
            generation_time = time.time() - start_time
            
            result = EmbeddingResult(
                law_id=law_id,
                article_number=article_number,
                content=text,
                embedding=embedding.tolist(),
                model_name=self.model_name,
                generation_time=generation_time,
                metadata={
                    "text_length": len(text),
                    "embedding_dimension": len(embedding),
                    "generated_at": datetime.now().isoformat()
                }
            )
            
            logger.debug(f"埋め込み生成完了: {law_id}-{article_number}, 時間: {generation_time:.3f}秒")
            return result
            
        except Exception as e:
            logger.error(f"埋め込み生成エラー: {law_id}-{article_number}, {str(e)}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str], law_ids: List[str] = None, article_numbers: List[str] = None) -> EmbeddingBatch:
        """
        バッチで埋め込みを生成
        
        Args:
            texts: テキストのリスト
            law_ids: 法律IDのリスト
            article_numbers: 条番号のリスト
            
        Returns:
            埋め込みバッチ結果
        """
        if not self.model:
            logger.error("埋め込みモデルが初期化されていません")
            return EmbeddingBatch([], 0, 0, self.model_name)
        
        if not texts:
            return EmbeddingBatch([], 0, 0, self.model_name)
        
        # デフォルト値の設定
        if law_ids is None:
            law_ids = [""] * len(texts)
        if article_numbers is None:
            article_numbers = [""] * len(texts)
        
        try:
            start_time = time.time()
            logger.info(f"バッチ埋め込み生成を開始: {len(texts)}件")
            
            # バッチで埋め込みを生成
            embeddings = self.model.encode(texts, convert_to_tensor=False, batch_size=self.batch_size)
            
            total_time = time.time() - start_time
            
            # 結果の作成
            results = []
            for i, (text, law_id, article_number, embedding) in enumerate(zip(texts, law_ids, article_numbers, embeddings)):
                result = EmbeddingResult(
                    law_id=law_id,
                    article_number=article_number,
                    content=text,
                    embedding=embedding.tolist(),
                    model_name=self.model_name,
                    generation_time=0,  # バッチ処理なので個別時間は0
                    metadata={
                        "text_length": len(text),
                        "embedding_dimension": len(embedding),
                        "batch_index": i,
                        "generated_at": datetime.now().isoformat()
                    }
                )
                results.append(result)
            
            batch_result = EmbeddingBatch(
                results=results,
                total_time=total_time,
                batch_size=len(texts),
                model_name=self.model_name
            )
            
            logger.info(f"バッチ埋め込み生成完了: {len(texts)}件, 時間: {total_time:.2f}秒, "
                       f"平均: {total_time/len(texts):.3f}秒/件")
            
            return batch_result
            
        except Exception as e:
            logger.error(f"バッチ埋め込み生成エラー: {str(e)}")
            return EmbeddingBatch([], 0, 0, self.model_name)
    
    def generate_embeddings_for_articles(self, articles: List[Article]) -> List[EmbeddingResult]:
        """
        条文の埋め込みを生成
        
        Args:
            articles: 条文のリスト
            
        Returns:
            埋め込み結果のリスト
        """
        if not articles:
            return []
        
        logger.info(f"条文の埋め込み生成を開始: {len(articles)}件")
        
        # テキストとメタデータを準備
        texts = []
        law_ids = []
        article_numbers = []
        
        for article in articles:
            texts.append(article.content)
            law_ids.append(article.law_id)
            article_numbers.append(article.article_number)
        
        # バッチで埋め込みを生成
        batch_result = self.generate_embeddings_batch(texts, law_ids, article_numbers)
        
        # メタデータを追加
        for i, result in enumerate(batch_result.results):
            if i < len(articles):
                article = articles[i]
                result.metadata.update({
                    "chapter": article.chapter,
                    "section": article.section,
                    "subsection": article.subsection,
                    "effective_date": article.effective_date,
                    "original_metadata": article.metadata
                })
        
        logger.info(f"条文の埋め込み生成完了: {len(batch_result.results)}件")
        return batch_result.results
    
    def generate_embeddings_for_law_document(self, law_document: LawDocument) -> List[EmbeddingResult]:
        """
        法律文書の埋め込みを生成
        
        Args:
            law_document: 法律文書
            
        Returns:
            埋め込み結果のリスト
        """
        logger.info(f"法律文書の埋め込み生成を開始: {law_document.law_id}")
        
        # 条文の埋め込みを生成
        article_embeddings = self.generate_embeddings_for_articles(law_document.articles)
        
        # 法律文書全体の埋め込みも生成（オプション）
        law_summary = self._create_law_summary(law_document)
        if law_summary:
            law_embedding = self.generate_embedding(law_summary, law_document.law_id, "SUMMARY")
            if law_embedding:
                article_embeddings.append(law_embedding)
        
        logger.info(f"法律文書の埋め込み生成完了: {law_document.law_id}, {len(article_embeddings)}件")
        return article_embeddings
    
    def _create_law_summary(self, law_document: LawDocument) -> Optional[str]:
        """
        法律文書の要約を作成
        
        Args:
            law_document: 法律文書
            
        Returns:
            要約テキスト
        """
        try:
            # 法律名と説明を組み合わせて要約を作成
            summary_parts = []
            
            if law_document.law_name:
                summary_parts.append(f"法律名: {law_document.law_name}")
            
            if law_document.description:
                summary_parts.append(f"概要: {law_document.description}")
            
            if law_document.law_number:
                summary_parts.append(f"法律番号: {law_document.law_number}")
            
            if law_document.effective_date:
                summary_parts.append(f"施行日: {law_document.effective_date}")
            
            # 条文数の情報
            summary_parts.append(f"条文数: {len(law_document.articles)}条")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.warning(f"法律要約の作成でエラー: {law_document.law_id}, {str(e)}")
            return None
    
    def save_embeddings_to_cache(self, embeddings: List[EmbeddingResult], cache_key: str) -> bool:
        """
        埋め込みをキャッシュに保存
        
        Args:
            embeddings: 埋め込み結果のリスト
            cache_key: キャッシュキー
            
        Returns:
            保存成功フラグ
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            with open(cache_file, 'wb') as f:
                pickle.dump(embeddings, f)
            
            logger.info(f"埋め込みをキャッシュに保存: {cache_key}, {len(embeddings)}件")
            return True
            
        except Exception as e:
            logger.error(f"埋め込みキャッシュ保存エラー: {cache_key}, {str(e)}")
            return False
    
    def load_embeddings_from_cache(self, cache_key: str) -> Optional[List[EmbeddingResult]]:
        """
        キャッシュから埋め込みを読み込み
        
        Args:
            cache_key: キャッシュキー
            
        Returns:
            埋め込み結果のリスト
        """
        try:
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'rb') as f:
                embeddings = pickle.load(f)
            
            logger.info(f"埋め込みをキャッシュから読み込み: {cache_key}, {len(embeddings)}件")
            return embeddings
            
        except Exception as e:
            logger.error(f"埋め込みキャッシュ読み込みエラー: {cache_key}, {str(e)}")
            return None
    
    def get_embedding_stats(self, embeddings: List[EmbeddingResult]) -> Dict[str, Any]:
        """
        埋め込みの統計情報を取得
        
        Args:
            embeddings: 埋め込み結果のリスト
            
        Returns:
            統計情報
        """
        if not embeddings:
            return {}
        
        # 基本統計
        total_count = len(embeddings)
        total_time = sum(e.generation_time for e in embeddings)
        avg_time = total_time / total_count if total_count > 0 else 0
        
        # テキスト長の統計
        text_lengths = [len(e.content) for e in embeddings]
        avg_text_length = sum(text_lengths) / len(text_lengths)
        max_text_length = max(text_lengths)
        min_text_length = min(text_lengths)
        
        # 埋め込み次元数
        embedding_dimensions = [len(e.embedding) for e in embeddings]
        unique_dimensions = set(embedding_dimensions)
        
        # 法律ID別の統計
        law_id_counts = {}
        for e in embeddings:
            law_id_counts[e.law_id] = law_id_counts.get(e.law_id, 0) + 1
        
        stats = {
            "total_count": total_count,
            "total_time": total_time,
            "average_time": avg_time,
            "text_length": {
                "average": avg_text_length,
                "max": max_text_length,
                "min": min_text_length
            },
            "embedding_dimensions": list(unique_dimensions),
            "law_id_distribution": law_id_counts,
            "model_name": embeddings[0].model_name if embeddings else None
        }
        
        return stats
    
    def validate_embeddings(self, embeddings: List[EmbeddingResult]) -> Dict[str, Any]:
        """
        埋め込みの妥当性を検証
        
        Args:
            embeddings: 埋め込み結果のリスト
            
        Returns:
            検証結果
        """
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "total_count": len(embeddings)
        }
        
        if not embeddings:
            validation_result["errors"].append("埋め込みが空です")
            validation_result["valid"] = False
            return validation_result
        
        # 埋め込み次元数の一貫性チェック
        dimensions = [len(e.embedding) for e in embeddings]
        unique_dimensions = set(dimensions)
        
        if len(unique_dimensions) > 1:
            validation_result["errors"].append(f"埋め込み次元数が一貫していません: {unique_dimensions}")
            validation_result["valid"] = False
        
        # 空の埋め込みチェック
        empty_embeddings = [i for i, e in enumerate(embeddings) if not e.embedding]
        if empty_embeddings:
            validation_result["errors"].append(f"空の埋め込みがあります: インデックス {empty_embeddings}")
            validation_result["valid"] = False
        
        # テキスト長のチェック
        short_texts = [i for i, e in enumerate(embeddings) if len(e.content) < 10]
        if short_texts:
            validation_result["warnings"].append(f"短いテキストがあります: インデックス {short_texts}")
        
        # 生成時間のチェック
        long_times = [i for i, e in enumerate(embeddings) if e.generation_time > 10]
        if long_times:
            validation_result["warnings"].append(f"生成時間が長い埋め込みがあります: インデックス {long_times}")
        
        return validation_result
    
    def close(self):
        """リソースのクリーンアップ"""
        if self.model:
            # モデルのクリーンアップ（必要に応じて）
            self.model = None
            logger.info("埋め込みモデルをクリーンアップしました")
