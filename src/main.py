"""
法律検索システムのメインアプリケーション
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from src.api.endpoints import health, search, laws
from src.core.utils.config_loader import ConfigLoader


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションのライフサイクル管理"""
    # 起動時の処理
    print("🚀 法律検索システムを起動しています...")
    
    # 設定の読み込み
    config = ConfigLoader()
    app.state.config = config
    
    # データベース接続の初期化
    # TODO: ArangoDB接続の初期化
    
    print("✅ アプリケーションの起動が完了しました")
    
    yield
    
    # シャットダウン時の処理
    print("🛑 アプリケーションをシャットダウンしています...")
    # TODO: リソースのクリーンアップ
    print("✅ シャットダウンが完了しました")


# FastAPIアプリケーションの作成
app = FastAPI(
    title="法律検索システム",
    description="e-GovのXMLデータを活用したハイブリッド検索による質問応答システム",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ルーターの登録
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(search.router, prefix="/api", tags=["search"])
app.include_router(laws.router, prefix="/api", tags=["laws"])


@app.get("/")
async def root():
    """ルートエンドポイント"""
    return {
        "message": "法律検索システムへようこそ",
        "version": "0.1.0",
        "docs": "/docs",
        "api": "/api"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """グローバル例外ハンドラー"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部サーバーエラー",
            "message": str(exc),
            "path": str(request.url)
        }
    )


def main():
    """メイン関数"""
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
