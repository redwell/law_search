# 法律検索システム (Law Search)

日本の法律を検索できるシステムです。e-GovのXMLデータを活用し、全文検索・ベクトル検索・グラフ検索を組み合わせたハイブリッド検索により、一般ユーザーが自然言語で質問して法律情報を取得できます。

## 特徴

- **ハイブリッド検索**: 全文検索・ベクトル検索・グラフ検索の統合
- **自然言語質問応答**: ChatGPTを活用したRAGシステム
- **引用元表示**: 回答の根拠となる法律条文の明示
- **e-Gov準拠**: 公式XMLスキーマ v3に完全対応
- **コスト重視**: 効率的なリソース使用
- **段階的開発**: MVPから段階的に機能拡張

## 技術スタック

- **バックエンド**: FastAPI, Python 3.11+
- **データベース**: ArangoDB (全文検索・ベクトル検索・グラフ検索)
- **AI**: OpenAI GPT-4, jinaai/jina-embeddings-v3
- **RAG**: langchain, langgraph
- **データ形式**: e-Gov XMLスキーマ v3準拠
- **フロントエンド**: 未定 (React/Vue.js/Next.js候補)
- **インフラ**: Docker, Docker Compose
- **開発**: uv, GitHub Actions, TDD

## プロジェクト構成

```
law_search/
├── src/                    # ソースコード
│   ├── core/              # コア機能
│   │   ├── data/          # データ処理
│   │   ├── search/        # 検索機能
│   │   ├── rag/           # RAGシステム
│   │   └── utils/         # ユーティリティ
│   ├── api/               # API層
│   └── web/               # WebUI
├── tests/                 # テストコード
├── scripts/               # 開発・運用スクリプト
├── config/                # 設定ファイル
├── docs/                  # ドキュメント
└── docker/                # Docker設定
```

## クイックスタート

### 前提条件

- Python 3.11+
- Docker & Docker Compose
- uv
- Git

### セットアップ

1. **リポジトリのクローン**
```bash
git clone https://github.com/redwell/law_search.git
cd law_search
```

2. **環境変数の設定**
```bash
cp env.example .env
# .envファイルを編集して必要な設定を追加
```

3. **依存関係のインストール**
```bash
uv sync
```

4. **Dockerサービスの起動**
```bash
docker-compose up -d
```

5. **アプリケーションの起動**
```bash
uv run uvicorn src.main:app --reload
```

### アクセス

- **API**: http://localhost:8000
- **API仕様書**: http://localhost:8000/docs
- **ArangoDB管理画面**: http://localhost:8529

## 開発

### 開発環境のセットアップ

```bash
# 開発用依存関係のインストール
uv sync --dev

# テストの実行
uv run pytest

# コードフォーマット
uv run black src/ tests/

# リントチェック
uv run ruff check src/ tests/

# 型チェック
uv run mypy src/
```

### テスト

```bash
# 全テストの実行
uv run pytest

# カバレッジ付きテスト
uv run pytest --cov=src

# 特定のテストファイル
uv run pytest tests/unit/test_search.py
```

### データベース操作

```bash
# ArangoDBの初期化
./scripts/init_db.sh

# データの取得・処理
./scripts/data_download.sh
```

## ドキュメント

- [プロジェクト仕様書](PROJECT_SPEC.md)
- [技術アーキテクチャ](ARCHITECTURE.md)
- [MVP要件定義](MVP_REQUIREMENTS.md)
- [開発ガイドライン](DEVELOPMENT_GUIDE.md)
- [開発プロセス](PROCESS_SPEC.md)
- [API仕様書](API_SPEC.md)

## e-Gov XMLスキーマ対応

本システムは、e-Govの公式XMLスキーマ v3に完全対応しています：

- **スキーマ参照**: [XMLSchemaForJapaneseLaw_v3.xsd](https://laws.e-gov.go.jp/file/XMLSchemaForJapaneseLaw_v3.xsd)
- **ルート要素**: `<Law>`（法令基本情報を属性として持つ）
- **本則部分**: `<MainProvision>`要素内の条文解析
- **条文構造**: `<Article>`、`<ArticleNum>`、`<ArticleCaption>`
- **名前空間**: `http://elaws.e-gov.go.jp/XMLSchema`

## ライセンス

MIT License

## 貢献

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

## ロードマップ

### MVP (現在)
- [x] プロジェクト計画・設計
- [ ] データ取得・前処理基盤
- [ ] データベース設計・実装
- [ ] 検索基盤の実装
- [ ] RAGシステムの実装
- [ ] WebUIの実装

### 次のステップ
- [ ] 判例・通達データの追加
- [ ] 他プラットフォーム連携 (LINE/Teams/Slack/Discord)
- [ ] 全法律領域への拡張
- [ ] 高度な分析・レポート機能

## サポート

問題や質問がある場合は、[GitHub Issues](https://github.com/redwell/law_search/issues)でお知らせください。
