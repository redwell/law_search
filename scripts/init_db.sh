#!/bin/bash

# データベース初期化スクリプト

set -e

echo "🗄️ ArangoDBを初期化します..."

# 環境変数の読み込み
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# デフォルト値の設定
ARANGO_ROOT_PASSWORD=${ARANGO_ROOT_PASSWORD:-password}
DATABASE_URL=${DATABASE_URL:-arangodb://root:password@localhost:8529}

# ArangoDBの接続確認
echo "🔗 ArangoDBへの接続を確認します..."
until curl -f http://localhost:8529/_api/version > /dev/null 2>&1; do
    echo "⏳ ArangoDBの起動を待機中..."
    sleep 2
done
echo "✅ ArangoDBに接続できました"

# データベースの作成
echo "📊 データベースを作成します..."
python3 -c "
import requests
import json

# データベース作成
db_name = 'law_search'
url = 'http://localhost:8529/_api/database'
headers = {'Content-Type': 'application/json'}
auth = ('root', '${ARANGO_ROOT_PASSWORD}')

# データベース一覧を取得
response = requests.get(url, auth=auth)
if response.status_code == 200:
    databases = response.json()['result']
    if db_name not in databases:
        # データベースを作成
        data = {'name': db_name}
        response = requests.post(url, headers=headers, data=json.dumps(data), auth=auth)
        if response.status_code == 201:
            print(f'✅ データベース {db_name} を作成しました')
        else:
            print(f'❌ データベース作成に失敗しました: {response.text}')
    else:
        print(f'✅ データベース {db_name} は既に存在します')
else:
    print(f'❌ データベース一覧の取得に失敗しました: {response.text}')
"

# コレクションの作成
echo "📋 コレクションを作成します..."
python3 -c "
import requests
import json

db_name = 'law_search'
base_url = f'http://localhost:8529/_db/{db_name}/_api'
headers = {'Content-Type': 'application/json'}
auth = ('root', '${ARANGO_ROOT_PASSWORD}')

# コレクション一覧
collections = [
    {
        'name': 'documents',
        'type': 'document',
        'options': {
            'keyOptions': {'type': 'autoincrement'},
            'schema': {
                'rule': {
                    'type': 'object',
                    'properties': {
                        'law_name': {'type': 'string'},
                        'article_number': {'type': 'string'},
                        'content': {'type': 'string'},
                        'embedding': {'type': 'array', 'items': {'type': 'number'}},
                        'metadata': {'type': 'object'}
                    },
                    'required': ['law_name', 'article_number', 'content']
                },
                'level': 'moderate'
            }
        }
    },
    {
        'name': 'law_relationships',
        'type': 'edge',
        'options': {
            'keyOptions': {'type': 'autoincrement'}
        }
    },
    {
        'name': 'article_relationships',
        'type': 'edge',
        'options': {
            'keyOptions': {'type': 'autoincrement'}
        }
    }
]

for collection in collections:
    # コレクション一覧を取得
    response = requests.get(f'{base_url}/collection', auth=auth)
    if response.status_code == 200:
        existing_collections = [c['name'] for c in response.json()['result']]
        if collection['name'] not in existing_collections:
            # コレクションを作成
            data = {
                'name': collection['name'],
                'type': collection['type'],
                'options': collection['options']
            }
            response = requests.post(f'{base_url}/collection', headers=headers, data=json.dumps(data), auth=auth)
            if response.status_code == 200:
                print(f'✅ コレクション {collection[\"name\"]} を作成しました')
            else:
                print(f'❌ コレクション {collection[\"name\"]} の作成に失敗しました: {response.text}')
        else:
            print(f'✅ コレクション {collection[\"name\"]} は既に存在します')
    else:
        print(f'❌ コレクション一覧の取得に失敗しました: {response.text}')
"

# インデックスの作成
echo "🔍 インデックスを作成します..."
python3 -c "
import requests
import json

db_name = 'law_search'
base_url = f'http://localhost:8529/_db/{db_name}/_api'
headers = {'Content-Type': 'application/json'}
auth = ('root', '${ARANGO_ROOT_PASSWORD}')

# インデックス一覧
indexes = [
    {
        'collection': 'documents',
        'type': 'fulltext',
        'fields': ['content'],
        'options': {'minLength': 2}
    },
    {
        'collection': 'documents',
        'type': 'persistent',
        'fields': ['law_name', 'article_number'],
        'options': {'unique': False}
    },
    {
        'collection': 'documents',
        'type': 'persistent',
        'fields': ['metadata.effective_date'],
        'options': {'unique': False}
    }
]

for index in indexes:
    collection_name = index['collection']
    # インデックス一覧を取得
    response = requests.get(f'{base_url}/index', params={'collection': collection_name}, auth=auth)
    if response.status_code == 200:
        existing_indexes = response.json()['indexes']
        # 同じフィールドのインデックスが存在するかチェック
        exists = any(
            idx['type'] == index['type'] and 
            set(idx.get('fields', [])) == set(index['fields'])
            for idx in existing_indexes
        )
        if not exists:
            # インデックスを作成
            data = {
                'type': index['type'],
                'fields': index['fields'],
                'options': index['options']
            }
            response = requests.post(f'{base_url}/index', headers=headers, data=json.dumps(data), auth=auth)
            if response.status_code == 201:
                print(f'✅ インデックス {index[\"type\"]} を {collection_name} に作成しました')
            else:
                print(f'❌ インデックスの作成に失敗しました: {response.text}')
        else:
            print(f'✅ インデックス {index[\"type\"]} は {collection_name} に既に存在します')
    else:
        print(f'❌ インデックス一覧の取得に失敗しました: {response.text}')
"

echo "🎉 データベースの初期化が完了しました！"
echo ""
echo "作成されたリソース:"
echo "- データベース: law_search"
echo "- コレクション: documents, law_relationships, article_relationships"
echo "- インデックス: 全文検索、複合インデックス"
echo ""
echo "ArangoDB管理画面: http://localhost:8529"
echo "ユーザー名: root"
echo "パスワード: ${ARANGO_ROOT_PASSWORD}"
