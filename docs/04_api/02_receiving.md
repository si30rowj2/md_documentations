---
title: 入庫登録API
published: true
---

# 入庫登録API (F-003)

入庫登録画面から呼び出す、入庫実績登録用の REST API。

## リクエスト

```http
POST /api/v1/receipts
Authorization: Bearer {token}
Content-Type: application/json

{
  "sku": "A1001234",
  "location": "B-01-02",
  "qty": 50
}
```

| ボディ項目 | 必須 | 説明 |
|-----------|------|------|
| sku | ○ | 入庫対象の SKU |
| location | ○ | 格納先のロケーション |
| qty | ○ | 入庫数量(1 以上の整数) |

## レスポンス

```json
{
  "receiptId": "R-20260730-0001",
  "sku": "A1001234",
  "location": "B-01-02",
  "qty": 50,
  "stockAfter": 170
}
```

## エラーレスポンス

| HTTP | コード | 条件 |
|------|--------|------|
| 401 | E-0102 | トークン不正・期限切れ |
| 400 | E-0301 | 入庫数量が 1 未満 |
| 404 | E-0302 | 該当する SKU が存在しない |
