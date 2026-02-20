# jplawdb2

日本の税法AIデータベース。LLMエージェントが10Kトークン制約内で最短距離に本文に到達できる設計。

## DBs

| DB | URL | 内容 |
|----|-----|------|
| 法令DB | https://jplawdb2.github.io/ai-law-db | 法人税法、措置法等24法令 |
| 通達DB | https://jplawdb2.github.io/ai-tsutatsu-db | 法基通等7通達 |
| 判例DB | https://jplawdb2.github.io/ai-hanketsu-db | 税務訴訟判例3,057件 |

## 設計仕様

[SCHEMA.md](./SCHEMA.md) を参照。

## アクセスパターン

```
# 法令を名前で探す
GET .well-known/llms.txt           # ← エントリポイント
GET meta/catalog.json              # ← DB一覧
GET meta/hojinzei.json             # ← 条文一覧（タイトル付き）
GET text/hojinzei/22.txt           # ← 本文
```

## jplawdb（旧版）

https://jplawdb.github.io/html-preview/ — 旧版。参照のみ。
