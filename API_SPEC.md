# API仕様書 (API_SPEC.md)

## 概要

本システムのAPI仕様書です。e-Gov XMLスキーマ v3準拠のデータ構造に基づいて設計されています。

## ベースURL

```
開発環境: http://localhost:8000
本番環境: https://api.law-search.example.com
```

## 認証

現在は認証なしでアクセス可能です。将来的にはAPIキー認証を実装予定です。

## 共通レスポンス形式

### 成功レスポンス

```json
{
  "status": "success",
  "data": {
    // レスポンスデータ
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
  }
}
```

### エラーレスポンス

```json
{
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "エラーメッセージ",
    "details": {}
  },
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
  }
}
```

## エンドポイント

### 1. ヘルスチェック

#### GET /health

システムの状態を確認します。

**レスポンス例:**
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "database": "connected",
    "services": {
      "arangodb": "up",
      "embedding_model": "loaded"
    }
  }
}
```

### 2. 法律検索

#### POST /search

法律を検索します。

**リクエスト:**
```json
{
  "query": "所得税法について教えて",
  "search_type": "hybrid",
  "limit": 10,
  "filters": {
    "category": "税法",
    "date_range": {
      "start": "2020-01-01",
      "end": "2024-12-31"
    }
  }
}
```

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "law_id": "M32HO089",
        "law_name": "所得税法",
        "law_name_kana": "しょとくぜいほう",
        "law_number": "昭和32年法律第89号",
        "promulgation_date": "1957-03-31",
        "effective_date": "1957-04-01",
        "category": "税法",
        "articles": [
          {
            "article_number": "第1条",
            "content": "この法律は、個人の所得に係る税金について定める。",
            "chapter": null,
            "section": null,
            "subsection": null,
            "paragraph": null,
            "effective_date": "1957-04-01",
            "metadata": {}
          }
        ],
        "score": 0.95,
        "search_type": "vector"
      }
    ],
    "total_count": 1,
    "search_time_ms": 150
  }
}
```

### 3. 法律詳細取得

#### GET /laws/{law_id}

特定の法律の詳細情報を取得します。

**パラメータ:**
- `law_id`: 法律ID（例: M32HO089）

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "law_id": "M32HO089",
    "law_name": "所得税法",
    "law_name_kana": "しょとくぜいほう",
    "law_number": "昭和32年法律第89号",
    "promulgation_date": "1957-03-31",
    "effective_date": "1957-04-01",
    "category": "税法",
    "description": "所得税法に関する法律",
    "articles": [
      {
        "article_number": "第1条",
        "content": "この法律は、個人の所得に係る税金について定める。",
        "chapter": null,
        "section": null,
        "subsection": null,
        "paragraph": null,
        "effective_date": "1957-04-01",
        "metadata": {}
      },
      {
        "article_number": "第2条",
        "content": "所得とは、個人の収入から必要経費を差し引いた金額をいう。",
        "chapter": null,
        "section": null,
        "subsection": null,
        "paragraph": null,
        "effective_date": "1957-04-01",
        "metadata": {}
      }
    ],
    "related_laws": [
      {
        "law_id": "S40HO034",
        "law_name": "法人税法",
        "relation_type": "関連"
      }
    ]
  }
}
```

### 4. 条文検索

#### POST /articles/search

特定の条文を検索します。

**リクエスト:**
```json
{
  "query": "所得の定義",
  "law_id": "M32HO089",
  "limit": 5
}
```

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "results": [
      {
        "law_id": "M32HO089",
        "article_number": "第2条",
        "content": "所得とは、個人の収入から必要経費を差し引いた金額をいう。",
        "chapter": null,
        "section": null,
        "subsection": null,
        "paragraph": null,
        "effective_date": "1957-04-01",
        "metadata": {},
        "score": 0.98
      }
    ],
    "total_count": 1,
    "search_time_ms": 75
  }
}
```

### 5. 質問応答

#### POST /qa

自然言語での質問に回答します。

**リクエスト:**
```json
{
  "question": "所得税法の趣旨は何ですか？",
  "context": {
    "law_id": "M32HO089",
    "include_citations": true
  }
}
```

**レスポンス:**
```json
{
  "status": "success",
  "data": {
    "answer": "所得税法の趣旨は、個人の所得に係る税金について定めることです。",
    "citations": [
      {
        "law_id": "M32HO089",
        "article_number": "第1条",
        "content": "この法律は、個人の所得に係る税金について定める。",
        "relevance_score": 0.95
      }
    ],
    "confidence": 0.92,
    "processing_time_ms": 1200
  }
}
```

## データ構造

### LawDocument

e-Gov XMLスキーマ v3準拠の法律文書構造：

```typescript
interface LawDocument {
  law_id: string;                    // 法律ID
  law_name: string;                  // 法律名
  law_name_kana?: string;            // 法律名（カナ）
  law_number?: string;               // 法律番号
  promulgation_date?: string;        // 公布日
  effective_date?: string;           // 施行日
  category?: string;                 // カテゴリ
  description?: string;              // 説明
  articles: Article[];               // 条文リスト
}
```

### Article

条文構造：

```typescript
interface Article {
  law_id: string;                    // 所属法律ID
  article_number: string;            // 条番号
  content: string;                   // 条文内容
  chapter?: string;                  // 章
  section?: string;                  // 節
  subsection?: string;               // 款
  paragraph?: string;                // 項
  effective_date?: string;           // 施行日
  metadata?: Record<string, any>;    // メタデータ
}
```

## エラーコード

| コード | 説明 |
|--------|------|
| `INVALID_QUERY` | 無効な検索クエリ |
| `LAW_NOT_FOUND` | 指定された法律が見つからない |
| `DATABASE_ERROR` | データベースエラー |
| `EMBEDDING_ERROR` | 埋め込み生成エラー |
| `RAG_ERROR` | RAG処理エラー |
| `VALIDATION_ERROR` | リクエスト検証エラー |

## レート制限

- **検索API**: 100リクエスト/分
- **質問応答API**: 20リクエスト/分
- **その他**: 200リクエスト/分

## バージョニング

APIバージョンはURLパスで管理されます：

```
/v1/search
/v1/laws/{law_id}
```

## 更新履歴

### v1.0.0 (2024-01-01)
- 初回リリース
- e-Gov XMLスキーマ v3対応
- 基本的な検索・質問応答機能
