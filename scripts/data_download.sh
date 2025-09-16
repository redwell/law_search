#!/bin/bash

# e-Govデータ取得スクリプト

set -e

echo "📥 e-Govデータを取得します..."

# 環境変数の読み込み
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# デフォルト値の設定
EGOV_BASE_URL=${EGOV_BASE_URL:-https://elaws.e-gov.go.jp}
EGOV_DATA_DIR=${EGOV_DATA_DIR:-./data/egov}

# データディレクトリの作成
mkdir -p "$EGOV_DATA_DIR"

echo "📁 データディレクトリ: $EGOV_DATA_DIR"

# 税法関連の法律ID（例）
TAX_LAW_IDS=(
    "M32HO089"  # 所得税法
    "M40HO034"  # 法人税法
    "M63HO108"  # 消費税法
    "M25HO073"  # 相続税法
    "M37HO028"  # 国税通則法
    "M37HO029"  # 国税徴収法
    "M37HO030"  # 国税犯則取締法
)

# データ取得関数
download_law_data() {
    local law_id=$1
    local output_file="$EGOV_DATA_DIR/${law_id}.xml"
    
    echo "📥 法律ID: $law_id を取得中..."
    
    # XMLデータの取得
    local xml_url="$EGOV_BASE_URL/api/opendata/${law_id}.xml"
    
    if curl -s -f "$xml_url" -o "$output_file"; then
        echo "✅ $law_id の取得が完了しました: $output_file"
        
        # ファイルサイズの確認
        local file_size=$(stat -f%z "$output_file" 2>/dev/null || stat -c%s "$output_file" 2>/dev/null)
        if [ "$file_size" -gt 1000 ]; then
            echo "📊 ファイルサイズ: $file_size bytes"
        else
            echo "⚠️  ファイルサイズが小さいです: $file_size bytes"
        fi
    else
        echo "❌ $law_id の取得に失敗しました"
        return 1
    fi
}

# 各法律のデータを取得
echo "🚀 税法関連の法律データを取得します..."
for law_id in "${TAX_LAW_IDS[@]}"; do
    download_law_data "$law_id"
    sleep 1  # サーバーへの負荷を軽減
done

# 取得結果の確認
echo ""
echo "📋 取得結果の確認:"
ls -la "$EGOV_DATA_DIR"

# データ処理の実行（Pythonスクリプトが実装されたら）
if [ -f "src/core/data/processor.py" ]; then
    echo ""
    echo "🔄 データ処理を実行します..."
    uv run python src/core/data/processor.py
    echo "✅ データ処理が完了しました"
else
    echo ""
    echo "ℹ️  データ処理スクリプトが未実装です"
    echo "   次のステップ: src/core/data/processor.py を実装してください"
fi

echo ""
echo "🎉 データ取得が完了しました！"
echo ""
echo "取得されたファイル:"
echo "- 場所: $EGOV_DATA_DIR"
echo "- 形式: XML"
echo "- 次のステップ: データ処理・ArangoDBへの格納"
