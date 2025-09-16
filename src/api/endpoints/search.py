"""
検索エンドポイント
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.core.utils.config_loader import ConfigLoader

router = APIRouter()


class SearchRequest(BaseModel):
    """検索リクエストモデル"""
    query: str = Field(..., description="検索クエリ", max_length=500)
    limit: int = Field(10, description="結果の最大件数", ge=1, le=100)
    search_type: str = Field("hybrid", description="検索タイプ", regex="^(fulltext|vector|graph|hybrid)$")
    include_metadata: bool = Field(True, description="メタデータを含めるかどうか")


class SearchResult(BaseModel):
    """検索結果モデル"""
    content: str = Field(..., description="条文内容")
    law_name: str = Field(..., description="法律名")
    article_number: str = Field(..., description="条番号")
    score: float = Field(..., description="検索スコア", ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = Field(None, description="メタデータ")


class SearchResponse(BaseModel):
    """検索レスポンスモデル"""
    query: str = Field(..., description="検索クエリ")
    results: List[SearchResult] = Field(..., description="検索結果")
    total_count: int = Field(..., description="総件数")
    search_time: float = Field(..., description="検索時間（秒）")
    search_type: str = Field(..., description="検索タイプ")
    timestamp: datetime = Field(..., description="検索実行時刻")


@router.post("/search", response_model=SearchResponse)
async def search_laws(
    request: SearchRequest,
    config: ConfigLoader = Depends(lambda: ConfigLoader())
) -> SearchResponse:
    """
    法律を検索する
    
    Args:
        request: 検索リクエスト
        config: 設定ローダー
        
    Returns:
        検索結果
        
    Raises:
        HTTPException: 検索エラー
    """
    start_time = datetime.now()
    
    try:
        # TODO: 実際の検索ロジックを実装
        # 現在はモックデータを返す
        
        # モック検索結果
        mock_results = [
            SearchResult(
                content="この法律は、個人の所得に係る税金について定める。",
                law_name="所得税法",
                article_number="第1条",
                score=0.95,
                metadata={
                    "chapter": "第1章",
                    "section": "第1節",
                    "effective_date": "2024-01-01"
                } if request.include_metadata else None
            ),
            SearchResult(
                content="所得とは、個人の収入から必要経費を差し引いた金額をいう。",
                law_name="所得税法",
                article_number="第2条",
                score=0.87,
                metadata={
                    "chapter": "第1章",
                    "section": "第1節",
                    "effective_date": "2024-01-01"
                } if request.include_metadata else None
            )
        ]
        
        # 検索時間の計算
        search_time = (datetime.now() - start_time).total_seconds()
        
        return SearchResponse(
            query=request.query,
            results=mock_results[:request.limit],
            total_count=len(mock_results),
            search_time=search_time,
            search_type=request.search_type,
            timestamp=start_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"検索エラー: {str(e)}"
        )


@router.get("/search/suggest")
async def get_search_suggestions(
    q: str = Query(..., description="検索クエリ", max_length=100),
    limit: int = Query(5, description="提案の最大件数", ge=1, le=20)
) -> Dict[str, Any]:
    """
    検索提案を取得する
    
    Args:
        q: 検索クエリ
        limit: 提案の最大件数
        
    Returns:
        検索提案のリスト
    """
    try:
        # TODO: 実際の提案ロジックを実装
        # 現在はモックデータを返す
        
        mock_suggestions = [
            "所得税法",
            "法人税法",
            "消費税法",
            "相続税法",
            "国税通則法"
        ]
        
        # クエリに基づく提案のフィルタリング
        filtered_suggestions = [
            suggestion for suggestion in mock_suggestions
            if q.lower() in suggestion.lower()
        ][:limit]
        
        return {
            "query": q,
            "suggestions": filtered_suggestions,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"提案取得エラー: {str(e)}"
        )


@router.get("/search/stats")
async def get_search_stats() -> Dict[str, Any]:
    """
    検索統計を取得する
    
    Returns:
        検索統計情報
    """
    try:
        # TODO: 実際の統計データを実装
        # 現在はモックデータを返す
        
        return {
            "total_searches": 1234,
            "popular_queries": [
                {"query": "所得税法", "count": 156},
                {"query": "法人税法", "count": 134},
                {"query": "消費税法", "count": 98},
                {"query": "相続税法", "count": 87},
                {"query": "国税通則法", "count": 76}
            ],
            "search_types": {
                "hybrid": 856,
                "fulltext": 234,
                "vector": 123,
                "graph": 21
            },
            "average_response_time": 1.23,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"統計取得エラー: {str(e)}"
        )
