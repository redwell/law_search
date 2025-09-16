#!/bin/bash

# テスト実行スクリプト

set -e

echo "🧪 テストを実行します..."

# テストの種類を選択
if [ "$1" = "unit" ]; then
    echo "📋 単体テストを実行します..."
    uv run pytest tests/unit/ -v
elif [ "$1" = "integration" ]; then
    echo "🔗 統合テストを実行します..."
    uv run pytest tests/integration/ -v
elif [ "$1" = "e2e" ]; then
    echo "🌐 E2Eテストを実行します..."
    uv run pytest tests/e2e/ -v
elif [ "$1" = "coverage" ]; then
    echo "📊 カバレッジ付きテストを実行します..."
    uv run pytest --cov=src --cov-report=html --cov-report=term
    echo "📈 カバレッジレポートが生成されました: htmlcov/index.html"
else
    echo "🧪 全テストを実行します..."
    uv run pytest tests/ -v --cov=src --cov-report=term
fi

echo "✅ テストが完了しました！"
