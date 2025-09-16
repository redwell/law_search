# 開発ガイドライン (DEVELOPMENT_GUIDE.md)

## 開発環境セットアップ

### 1. 前提条件
- **OS**: macOS 24.6.0以上
- **Python**: 3.11以上
- **Git**: 最新版
- **Docker**: 最新版
- **uv**: 最新版
- **e-Gov XMLスキーマ**: v3準拠（[XMLSchemaForJapaneseLaw_v3.xsd](https://laws.e-gov.go.jp/file/XMLSchemaForJapaneseLaw_v3.xsd)）

### 2. プロジェクト初期化

#### 2.1 リポジトリのクローン
```bash
git clone https://github.com/your-username/law_search.git
cd law_search
```

#### 2.2 Python環境のセットアップ
```bash
# uvのインストール（未インストールの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh

# プロジェクトの初期化
uv init

# 依存関係のインストール
uv sync
```

#### 2.3 開発用スクリプトの実行
```bash
# 開発環境のセットアップ
./scripts/setup.sh

# テストの実行
./scripts/test.sh

# コード品質チェック
./scripts/lint.sh
```

### 3. Docker環境のセットアップ

#### 3.1 ArangoDBの起動
```bash
# Docker Composeでサービスを起動
docker-compose up -d

# ArangoDBの状態確認
docker-compose ps
```

#### 3.2 データベースの初期化
```bash
# データベースの初期化スクリプト実行
./scripts/init_db.sh
```

## プロジェクト構造

```
law_search/
├── src/                    # ソースコード
│   ├── core/              # コア機能
│   │   ├── data/          # データ処理
│   │   ├── search/        # 検索機能
│   │   ├── rag/           # RAGシステム
│   │   └── utils/         # ユーティリティ
│   ├── api/               # API層
│   │   ├── endpoints/     # エンドポイント
│   │   ├── middleware/    # ミドルウェア
│   │   └── schemas/       # データスキーマ
│   └── web/               # WebUI
│       ├── components/    # Reactコンポーネント
│       ├── pages/         # ページ
│       └── styles/        # スタイル
├── tests/                 # テストコード
│   ├── unit/              # 単体テスト
│   ├── integration/       # 統合テスト
│   └── e2e/               # E2Eテスト
├── scripts/               # 開発・運用スクリプト
│   ├── setup.sh           # 環境セットアップ
│   ├── test.sh            # テスト実行
│   ├── lint.sh            # コード品質チェック
│   ├── data_download.sh   # データ取得
│   └── init_db.sh         # DB初期化
├── config/                # 設定ファイル
│   ├── development.yaml   # 開発環境設定
│   ├── production.yaml    # 本番環境設定
│   └── logging.yaml       # ログ設定
├── docs/                  # ドキュメント
│   ├── api/               # API仕様書
│   ├── deployment/        # デプロイメント手順
│   └── user/              # ユーザーガイド
├── docker/                # Docker設定
│   ├── Dockerfile         # アプリケーション用
│   ├── docker-compose.yml # 開発環境用
│   └── docker-compose.prod.yml # 本番環境用
├── .github/               # GitHub設定
│   ├── workflows/         # GitHub Actions
│   ├── ISSUE_TEMPLATE/    # Issueテンプレート
│   └── PULL_REQUEST_TEMPLATE.md # PRテンプレート
├── pyproject.toml         # Python設定
├── README.md              # プロジェクト概要
└── .env.example           # 環境変数テンプレート
```

## コーディング規約

### 1. Python規約

#### 1.1 基本ルール
- **PEP 8**: Python標準のコーディング規約に従う
- **型ヒント**: 全ての関数・メソッドに型ヒントを記述
- **docstring**: 全ての関数・クラスにdocstringを記述
- **命名規則**: スネークケース（関数・変数）、パスカルケース（クラス）

#### 1.2 e-Gov XMLスキーマ対応
- **スキーマ準拠**: e-Gov XMLスキーマ v3に完全準拠
- **名前空間**: `http://elaws.e-gov.go.jp/XMLSchema`を使用
- **要素構造**: `<Law>`、`<MainProvision>`、`<Article>`等の正しい構造
- **属性抽出**: 法令基本情報は属性から優先的に抽出

#### 1.3 コード例
```python
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class SearchResult:
    """検索結果を表すデータクラス"""
    content: str
    score: float
    metadata: Dict[str, str]

def search_laws(query: str, limit: int = 10) -> List[SearchResult]:
    """
    法律を検索する
    
    Args:
        query: 検索クエリ
        limit: 結果の最大件数
        
    Returns:
        検索結果のリスト
        
    Raises:
        ValueError: クエリが空の場合
    """
    if not query.strip():
        raise ValueError("クエリは空にできません")
    
    # 実装...
    return results
```

#### 1.3 インポート順序
```python
# 1. 標準ライブラリ
import os
import sys
from typing import List, Dict

# 2. サードパーティライブラリ
import requests
from fastapi import FastAPI

# 3. ローカルインポート
from src.core.search import SearchEngine
from src.core.utils import ConfigLoader
```

### 2. テスト規約

#### 2.1 テスト構造
- **テストファイル**: `test_*.py`または`*_test.py`
- **テストクラス**: `Test*`で始まる
- **テストメソッド**: `test_*`で始まる
- **フィクスチャ**: `conftest.py`で定義

#### 2.2 テスト例
```python
import pytest
from unittest.mock import Mock, patch
from src.core.search import SearchEngine

class TestSearchEngine:
    """SearchEngineのテストクラス"""
    
    @pytest.fixture
    def search_engine(self):
        """SearchEngineのフィクスチャ"""
        return SearchEngine()
    
    def test_search_with_valid_query(self, search_engine):
        """有効なクエリでの検索テスト"""
        # Given
        query = "所得税法"
        expected_count = 5
        
        # When
        results = search_engine.search(query, limit=expected_count)
        
        # Then
        assert len(results) <= expected_count
        assert all(result.score > 0 for result in results)
    
    def test_search_with_empty_query(self, search_engine):
        """空のクエリでの検索テスト"""
        # Given
        query = ""
        
        # When & Then
        with pytest.raises(ValueError, match="クエリは空にできません"):
            search_engine.search(query)
```

### 3. ドキュメント規約

#### 3.1 e-Gov XMLスキーマ対応の実装例
```python
def parse_law_xml(self, xml_file_path: str) -> Optional[LawDocument]:
    """
    e-Gov XMLスキーマ v3準拠の法律XMLファイルをパース
    
    Args:
        xml_file_path: XMLファイルのパス
        
    Returns:
        パースされた法律文書オブジェクト
        
    Note:
        - ルート要素: <Law>（法令基本情報を属性として持つ）
        - 本則部分: <MainProvision>要素内の条文解析
        - 条文構造: <Article>、<ArticleNum>、<ArticleCaption>
        - 名前空間: http://elaws.e-gov.go.jp/XMLSchema
    """
    pass
```

#### 3.2 docstring形式
```python
def process_xml_data(xml_file: str, output_dir: str) -> Dict[str, int]:
    """
    XMLデータを処理してArangoDBに格納する
    
    Args:
        xml_file: 入力XMLファイルのパス
        output_dir: 出力ディレクトリのパス
        
    Returns:
        処理結果の統計情報
        {
            'processed_documents': int,  # 処理した文書数
            'errors': int,              # エラー数
            'processing_time': float    # 処理時間（秒）
        }
        
    Raises:
        FileNotFoundError: XMLファイルが見つからない場合
        XMLParseError: XMLの解析に失敗した場合
        
    Example:
        >>> stats = process_xml_data('data/law.xml', 'output/')
        >>> print(f"処理した文書数: {stats['processed_documents']}")
    """
    pass
```

#### 3.2 コメント規約
```python
# 複雑なロジックには説明コメントを追加
def calculate_search_score(fulltext_score: float, vector_score: float, 
                          graph_score: float) -> float:
    """
    ハイブリッド検索のスコアを計算する
    
    重み付け: 全文検索40%, ベクトル検索40%, グラフ検索20%
    """
    # 重み付けの計算
    weighted_score = (
        fulltext_score * 0.4 +
        vector_score * 0.4 +
        graph_score * 0.2
    )
    
    # スコアの正規化（0-1の範囲に調整）
    normalized_score = min(max(weighted_score, 0.0), 1.0)
    
    return normalized_score
```

## 開発ワークフロー

### 1. ブランチ戦略（GitHub Flow）

#### 1.1 ブランチ構成
- **main**: 本番環境用の安定ブランチ
- **feature/***: 機能開発用ブランチ
- **hotfix/***: 緊急修正用ブランチ

#### 1.2 開発フロー
```bash
# 1. 最新のmainブランチを取得
git checkout main
git pull origin main

# 2. 機能ブランチを作成
git checkout -b feature/tax-law-search

# 3. 開発・テスト・コミット
git add .
git commit -m "feat: 税法検索機能を追加"

# 4. プッシュ
git push origin feature/tax-law-search

# 5. プルリクエストを作成
# GitHub上でプルリクエストを作成

# 6. レビュー・マージ後、ブランチを削除
git checkout main
git pull origin main
git branch -d feature/tax-law-search
```

#### 1.3 コミットメッセージ規約
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Type例:**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント更新
- `style`: コードスタイル修正
- `refactor`: リファクタリング
- `test`: テスト追加・修正
- `chore`: その他の変更

**例:**
```
feat(search): ハイブリッド検索機能を実装

- 全文検索・ベクトル検索・グラフ検索を統合
- 結果の重み付け・ランキング機能を追加
- 検索性能を平均3秒以内に改善

Closes #123
```

### 2. テスト駆動開発（TDD）

#### 2.1 TDDサイクル
1. **Red**: 失敗するテストを書く
2. **Green**: テストが通る最小限のコードを書く
3. **Refactor**: コードを改善する

#### 2.2 テスト実行
```bash
# 全テストの実行
./scripts/test.sh

# 特定のテストファイルの実行
pytest tests/unit/test_search.py

# カバレッジ付きテスト実行
pytest --cov=src tests/

# 特定のテストメソッドの実行
pytest tests/unit/test_search.py::TestSearchEngine::test_search_with_valid_query
```

### 3. コード品質管理

#### 3.1 リント・フォーマット
```bash
# コードフォーマット
black src/ tests/

# リントチェック
ruff check src/ tests/

# 型チェック
mypy src/

# セキュリティチェック
bandit -r src/
```

#### 3.2 プリコミットフック
```bash
# pre-commitのインストール
pip install pre-commit

# フックの設定
pre-commit install

# 手動実行
pre-commit run --all-files
```

## デバッグ・トラブルシューティング

### 1. ログ設定

#### 1.1 ログレベル
```python
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

#### 1.2 ログの使用例
```python
def search_laws(query: str) -> List[SearchResult]:
    logger.info(f"検索開始: query='{query}'")
    
    try:
        results = perform_search(query)
        logger.info(f"検索完了: {len(results)}件の結果")
        return results
    except Exception as e:
        logger.error(f"検索エラー: {str(e)}", exc_info=True)
        raise
```

### 2. デバッグツール

#### 2.1 デバッガー
```python
import pdb

def complex_function():
    # デバッグポイントを設定
    pdb.set_trace()
    
    # コードの実行...
```

#### 2.2 プロファイラー
```python
import cProfile
import pstats

def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # プロファイル対象のコード
    search_laws("所得税法")
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)
```

### 3. よくある問題と解決方法

#### 3.1 ArangoDB接続エラー
```python
# 接続確認
from arango import ArangoClient

client = ArangoClient(hosts='http://localhost:8529')
db = client.db('law_search', username='root', password='password')

# 接続テスト
try:
    db.version()
    print("ArangoDB接続成功")
except Exception as e:
    print(f"ArangoDB接続エラー: {e}")
```

#### 3.2 埋め込み生成エラー
```python
# モデル読み込み確認
from sentence_transformers import SentenceTransformer

try:
    model = SentenceTransformer('jinaai/jina-embeddings-v3')
    print("埋め込みモデル読み込み成功")
except Exception as e:
    print(f"埋め込みモデルエラー: {e}")
```

## パフォーマンス最適化

### 1. データベース最適化

#### 1.1 インデックス作成
```python
# 全文検索インデックス
db.collection('documents').add_fulltext_index(
    fields=['content'],
    min_length=2
)

# ベクトルインデックス
db.collection('documents').add_vector_index(
    fields=['embedding'],
    vector_size=1024
)
```

#### 1.2 クエリ最適化
```python
# 効率的なクエリ例
def search_documents(query: str, limit: int = 10):
    aql = """
    FOR doc IN documents
    SEARCH ANALYZER(doc.content IN TOKENS(@query, 'text_ja'), 'text_ja')
    SORT BM25(doc) DESC
    LIMIT @limit
    RETURN doc
    """
    
    cursor = db.aql.execute(aql, bind_vars={'query': query, 'limit': limit})
    return list(cursor)
```

### 2. メモリ最適化

#### 2.1 バッチ処理
```python
def process_documents_batch(documents: List[Dict], batch_size: int = 100):
    """文書をバッチで処理してメモリ使用量を抑制"""
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        process_batch(batch)
        
        # メモリ解放
        del batch
        gc.collect()
```

#### 2.2 キャッシュ活用
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_embedding(text: str) -> List[float]:
    """埋め込みをキャッシュして計算コストを削減"""
    return model.encode(text)
```

## セキュリティ

### 1. 入力検証

#### 1.1 SQLインジェクション対策
```python
# AQLクエリのパラメータ化
def search_laws_safe(query: str):
    aql = """
    FOR doc IN documents
    FILTER doc.content LIKE @query
    RETURN doc
    """
    
    # パラメータ化によりインジェクションを防止
    cursor = db.aql.execute(aql, bind_vars={'query': f'%{query}%'})
    return list(cursor)
```

#### 1.2 XSS対策
```python
import html

def sanitize_input(user_input: str) -> str:
    """ユーザー入力をサニタイズ"""
    return html.escape(user_input)
```

### 2. 認証・認可

#### 2.1 API認証
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

def verify_token(token: str = Depends(security)):
    """トークンの検証"""
    if not is_valid_token(token.credentials):
        raise HTTPException(status_code=401, detail="Invalid token")
    return token.credentials
```

## デプロイメント

### 1. 本番環境設定

#### 1.1 環境変数
```bash
# .env.production
DATABASE_URL=arangodb://localhost:8529
OPENAI_API_KEY=your_api_key
LOG_LEVEL=INFO
DEBUG=False
```

#### 1.2 Docker設定
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install uv && uv sync --frozen

COPY . .

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 2. 監視・ログ

#### 2.1 ヘルスチェック
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy", "timestamp": datetime.now()}
```

#### 2.2 メトリクス収集
```python
import time
from functools import wraps

def measure_time(func):
    """実行時間を測定するデコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        logger.info(f"{func.__name__} 実行時間: {end_time - start_time:.2f}秒")
        return result
    return wrapper
```

---

*このドキュメントはリビングドキュメントです。開発の進行に合わせて継続的に更新されます。*
