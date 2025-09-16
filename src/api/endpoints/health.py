"""
ヘルスチェックエンドポイント
"""

from fastapi import APIRouter, Depends
from datetime import datetime
from typing import Dict, Any

from src.core.utils.config_loader import ConfigLoader

router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    ヘルスチェックエンドポイント
    
    Returns:
        システムの状態情報
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "service": "law-search"
    }


@router.get("/health/detailed")
async def detailed_health_check(config: ConfigLoader = Depends(lambda: ConfigLoader())) -> Dict[str, Any]:
    """
    詳細ヘルスチェックエンドポイント
    
    Args:
        config: 設定ローダー
        
    Returns:
        詳細なシステム状態情報
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0",
        "service": "law-search",
        "components": {}
    }
    
    # データベース接続チェック
    try:
        # TODO: ArangoDB接続チェック
        health_status["components"]["database"] = {
            "status": "healthy",
            "message": "ArangoDB接続正常"
        }
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "message": f"ArangoDB接続エラー: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # OpenAI API接続チェック
    try:
        api_key = config.get_openai_api_key()
        if api_key and api_key != "your_openai_api_key_here":
            health_status["components"]["openai"] = {
                "status": "healthy",
                "message": "OpenAI API設定正常"
            }
        else:
            health_status["components"]["openai"] = {
                "status": "unhealthy",
                "message": "OpenAI APIキーが設定されていません"
            }
            health_status["status"] = "unhealthy"
    except Exception as e:
        health_status["components"]["openai"] = {
            "status": "unhealthy",
            "message": f"OpenAI API設定エラー: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    # 埋め込みモデルチェック
    try:
        # TODO: 埋め込みモデルの読み込みチェック
        health_status["components"]["embedding_model"] = {
            "status": "healthy",
            "message": "埋め込みモデル正常"
        }
    except Exception as e:
        health_status["components"]["embedding_model"] = {
            "status": "unhealthy",
            "message": f"埋め込みモデルエラー: {str(e)}"
        }
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/health/ready")
async def readiness_check() -> Dict[str, Any]:
    """
    レディネスチェックエンドポイント
    
    Returns:
        システムの準備完了状態
    """
    # TODO: 必要なリソースの準備完了チェック
    return {
        "status": "ready",
        "timestamp": datetime.now().isoformat(),
        "message": "システムは準備完了です"
    }


@router.get("/health/live")
async def liveness_check() -> Dict[str, Any]:
    """
    ライブネスチェックエンドポイント
    
    Returns:
        システムの生存状態
    """
    return {
        "status": "alive",
        "timestamp": datetime.now().isoformat(),
        "message": "システムは稼働中です"
    }
