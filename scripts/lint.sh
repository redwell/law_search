#!/bin/bash

# コード品質チェックスクリプト

set -e

echo "🔍 コード品質をチェックします..."

# フォーマットチェック
echo "🎨 コードフォーマットをチェックします..."
uv run black --check src/ tests/
echo "✅ フォーマットチェック完了"

# リントチェック
echo "🔧 リントチェックを実行します..."
uv run ruff check src/ tests/
echo "✅ リントチェック完了"

# 型チェック
echo "📝 型チェックを実行します..."
uv run mypy src/
echo "✅ 型チェック完了"

# セキュリティチェック
echo "🔒 セキュリティチェックを実行します..."
uv run bandit -r src/
echo "✅ セキュリティチェック完了"

echo "🎉 全てのコード品質チェックが完了しました！"
