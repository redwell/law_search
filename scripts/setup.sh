#!/bin/bash

# 開発環境セットアップスクリプト

set -e

echo "🚀 法律検索システムの開発環境をセットアップします..."

# 環境変数ファイルの作成
if [ ! -f .env ]; then
    echo "📝 環境変数ファイルを作成します..."
    cp env.example .env
    echo "✅ .envファイルが作成されました。必要に応じて設定を編集してください。"
else
    echo "✅ .envファイルは既に存在します。"
fi

# データディレクトリの作成
echo "📁 データディレクトリを作成します..."
mkdir -p data/egov
mkdir -p logs
echo "✅ データディレクトリが作成されました。"

# 依存関係のインストール
echo "📦 依存関係をインストールします..."
uv sync --dev
echo "✅ 依存関係のインストールが完了しました。"

# Dockerサービスの起動
echo "🐳 Dockerサービスを起動します..."
docker-compose up -d
echo "✅ Dockerサービスが起動しました。"

# データベースの初期化待機
echo "⏳ ArangoDBの起動を待機します..."
sleep 10

# データベースの初期化
echo "🗄️ データベースを初期化します..."
./scripts/init_db.sh
echo "✅ データベースの初期化が完了しました。"

echo "🎉 開発環境のセットアップが完了しました！"
echo ""
echo "次のステップ:"
echo "1. .envファイルを編集してAPIキーなどを設定してください"
echo "2. 'uv run uvicorn src.main:app --reload' でアプリケーションを起動してください"
echo "3. http://localhost:8000 でアプリケーションにアクセスできます"
echo ""
echo "便利なコマンド:"
echo "- テスト実行: ./scripts/test.sh"
echo "- コード品質チェック: ./scripts/lint.sh"
echo "- データ取得: ./scripts/data_download.sh"
