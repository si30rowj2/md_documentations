---
title: 在庫照会API
published: true
---

# 在庫照会API (F-002)

在庫照会画面から呼び出す、在庫検索用の REST API。

## リクエスト

```http
GET /api/v1/stocks?sku=A100&location=B-01-02
Authorization: Bearer {token}
```

| クエリパラメータ | 必須 | 説明 |
|------------------|------|------|
| sku | - | SKU コード(前方一致) |
| location | - | ロケーション(完全一致) |
| status | - | 在庫区分(good / defective) |

## レスポンス

```json
{
  "items": [
    { "sku": "A1001234", "location": "B-01-02", "qty": 120, "status": "good" }
  ],
  "total": 1
}
```

## エラーレスポンス

| HTTP | コード | 条件 |
|------|--------|------|
| 401 | E-0102 | トークン不正・期限切れ |
| 400 | E-0201 | クエリパラメータの形式不正 |
