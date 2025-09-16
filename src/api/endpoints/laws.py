"""
法律情報エンドポイント
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

router = APIRouter()


class LawInfo(BaseModel):
    """法律情報モデル"""
    law_id: str = Field(..., description="法律ID")
    law_name: str = Field(..., description="法律名")
    law_name_kana: Optional[str] = Field(None, description="法律名（カナ）")
    law_number: Optional[str] = Field(None, description="法律番号")
    promulgation_date: Optional[str] = Field(None, description="公布日")
    effective_date: Optional[str] = Field(None, description="施行日")
    category: Optional[str] = Field(None, description="カテゴリ")
    description: Optional[str] = Field(None, description="説明")


class ArticleInfo(BaseModel):
    """条文情報モデル"""
    article_number: str = Field(..., description="条番号")
    content: str = Field(..., description="条文内容")
    chapter: Optional[str] = Field(None, description="章")
    section: Optional[str] = Field(None, description="節")
    subsection: Optional[str] = Field(None, description="款")
    effective_date: Optional[str] = Field(None, description="施行日")


class LawDetail(BaseModel):
    """法律詳細モデル"""
    law_info: LawInfo = Field(..., description="法律情報")
    articles: List[ArticleInfo] = Field(..., description="条文一覧")
    total_articles: int = Field(..., description="条文総数")
    last_updated: datetime = Field(..., description="最終更新日時")


@router.get("/laws", response_model=List[LawInfo])
async def get_laws(
    category: Optional[str] = Query(None, description="カテゴリでフィルタ"),
    limit: int = Query(50, description="取得件数", ge=1, le=100),
    offset: int = Query(0, description="オフセット", ge=0)
) -> List[LawInfo]:
    """
    法律一覧を取得する
    
    Args:
        category: カテゴリでフィルタ
        limit: 取得件数
        offset: オフセット
        
    Returns:
        法律一覧
    """
    try:
        # TODO: 実際のデータベースクエリを実装
        # 現在はモックデータを返す
        
        mock_laws = [
            LawInfo(
                law_id="M32HO089",
                law_name="所得税法",
                law_name_kana="しょとくぜいほう",
                law_number="昭和32年法律第89号",
                promulgation_date="1957-03-31",
                effective_date="1957-04-01",
                category="税法",
                description="個人の所得に係る税金について定める法律"
            ),
            LawInfo(
                law_id="M40HO034",
                law_name="法人税法",
                law_name_kana="ほうじんぜいほう",
                law_number="昭和40年法律第34号",
                promulgation_date="1965-03-31",
                effective_date="1965-04-01",
                category="税法",
                description="法人の所得に係る税金について定める法律"
            ),
            LawInfo(
                law_id="M63HO108",
                law_name="消費税法",
                law_name_kana="しょうひぜいほう",
                law_number="昭和63年法律第108号",
                promulgation_date="1988-12-30",
                effective_date="1989-04-01",
                category="税法",
                description="消費に係る税金について定める法律"
            ),
            LawInfo(
                law_id="M25HO073",
                law_name="相続税法",
                law_name_kana="そうぞくぜいほう",
                law_number="昭和25年法律第73号",
                promulgation_date="1950-03-31",
                effective_date="1950-04-01",
                category="税法",
                description="相続及び遺贈に係る税金について定める法律"
            )
        ]
        
        # カテゴリフィルタ
        if category:
            mock_laws = [law for law in mock_laws if law.category == category]
        
        # ページネーション
        return mock_laws[offset:offset + limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"法律一覧取得エラー: {str(e)}"
        )


@router.get("/laws/{law_id}", response_model=LawDetail)
async def get_law_detail(law_id: str) -> LawDetail:
    """
    法律の詳細情報を取得する
    
    Args:
        law_id: 法律ID
        
    Returns:
        法律詳細情報
    """
    try:
        # TODO: 実際のデータベースクエリを実装
        # 現在はモックデータを返す
        
        mock_law_info = LawInfo(
            law_id=law_id,
            law_name="所得税法",
            law_name_kana="しょとくぜいほう",
            law_number="昭和32年法律第89号",
            promulgation_date="1957-03-31",
            effective_date="1957-04-01",
            category="税法",
            description="個人の所得に係る税金について定める法律"
        )
        
        mock_articles = [
            ArticleInfo(
                article_number="第1条",
                content="この法律は、個人の所得に係る税金について定める。",
                chapter="第1章",
                section="第1節",
                effective_date="1957-04-01"
            ),
            ArticleInfo(
                article_number="第2条",
                content="所得とは、個人の収入から必要経費を差し引いた金額をいう。",
                chapter="第1章",
                section="第1節",
                effective_date="1957-04-01"
            ),
            ArticleInfo(
                article_number="第3条",
                content="納税義務者は、所得がある個人とする。",
                chapter="第1章",
                section="第1節",
                effective_date="1957-04-01"
            )
        ]
        
        return LawDetail(
            law_info=mock_law_info,
            articles=mock_articles,
            total_articles=len(mock_articles),
            last_updated=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"法律詳細取得エラー: {str(e)}"
        )


@router.get("/laws/{law_id}/articles/{article_number}")
async def get_article_detail(
    law_id: str,
    article_number: str
) -> ArticleInfo:
    """
    条文の詳細情報を取得する
    
    Args:
        law_id: 法律ID
        article_number: 条番号
        
    Returns:
        条文詳細情報
    """
    try:
        # TODO: 実際のデータベースクエリを実装
        # 現在はモックデータを返す
        
        return ArticleInfo(
            article_number=article_number,
            content="この条文は、個人の所得に係る税金について定める。",
            chapter="第1章",
            section="第1節",
            effective_date="1957-04-01"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"条文詳細取得エラー: {str(e)}"
        )


@router.get("/laws/categories")
async def get_law_categories() -> Dict[str, Any]:
    """
    法律カテゴリ一覧を取得する
    
    Returns:
        法律カテゴリ一覧
    """
    try:
        # TODO: 実際のデータベースクエリを実装
        # 現在はモックデータを返す
        
        return {
            "categories": [
                {"name": "税法", "count": 15, "description": "税金に関する法律"},
                {"name": "民法", "count": 8, "description": "民事に関する法律"},
                {"name": "刑法", "count": 5, "description": "刑事に関する法律"},
                {"name": "商法", "count": 12, "description": "商事に関する法律"},
                {"name": "労働法", "count": 10, "description": "労働に関する法律"}
            ],
            "total_categories": 5,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"カテゴリ一覧取得エラー: {str(e)}"
        )
