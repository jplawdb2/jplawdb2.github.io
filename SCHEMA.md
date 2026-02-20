# jplawdb2 設計仕様 v2.0

> 中心原則: **直アクセス可能性** — URLを知識として持つAIは、ナビゲーション不要で本文に1ホップで到達できる。

---

## 設計哲学

### 一次設計: 直アクセス（AIが知ってれば1発）

```
AI「法法22条が必要」
  ↓ URL構造を知っている
GET https://jplawdb2.github.io/ai-law-db/text/hojin/22.txt
```

### 二次設計: ナビゲーション（知らないときの保険）

```
llms.txt → catalog.json → meta/{code}.json → text/
```

ナビゲーションは**フォールバック**。一次設計を阻害しない。

### llms.txt = AIが一度読んで永久記憶するスキーマ

llms.txt は「発見のためのページ」ではなく、**AIが記憶するAPIドキュメント**として設計する。一度読んだAI（または学習データに入ったAI）は、以降ナビゲーション不要で全条文に到達できる。

---

## URL構造（永久不変）

```
https://jplawdb2.github.io/{db}/text/{code}/{id}.txt
```

| DB | パス |
|----|------|
| 法令 | `ai-law-db/text/{code}/{article}.txt` |
| 通達 | `ai-tsutatsu-db/text/{code}/{item}.txt` |
| 判例 | `ai-hanketsu-db/text/{case_id}.txt` |

**URL構造は追加のみ許可。変更・削除は永久禁止。**

---

## コード体系（法令略称から直接導ける）

設計原則: **法令の日本語略称（法法・措法・法基通）から、AIが推測できるコード**

### 法令DB コード

| 法令名 | 日本語略称 | URL code | 導出規則 |
|--------|----------|---------|--------|
| 法人税法 | 法法 | `hojin` | 法人税の「法人」 |
| 法人税法施行令 | 法令 | `hojin-rei` | hojin + 令 |
| 法人税法施行規則 | 法規 | `hojin-ki` | hojin + 規則 |
| 租税特別措置法 | 措法 | `sochi` | 措置の「措置」 |
| 租税特別措置法施行令 | 措令 | `sochi-rei` | sochi + 令 |
| 租税特別措置法施行規則 | 措規 | `sochi-ki` | sochi + 規則 |
| 所得税法 | 所法 | `shotoku` | 所得税の「所得」 |
| 所得税法施行令 | 所令 | `shotoku-rei` | shotoku + 令 |
| 消費税法 | 消法 | `shohi` | 消費税の「消費」 |
| 相続税法 | 相法 | `sozoku` | 相続税の「相続」 |
| 贈与税（相続税法内） | — | `sozoku` | 相続税法に統合 |
| 法人住民税・事業税 | — | `chiho` | 地方税の「地方」 |

**パターン**: `{税目の核心語}` / 施行令は `-rei` / 施行規則は `-ki`

### 通達DB コード

| 通達名 | 略称 | URL code | 導出規則 |
|--------|------|---------|--------|
| 法人税基本通達 | 法基通 | `hkt` | 法基通の頭文字 |
| 所得税基本通達 | 所基通 | `skt` | 所基通の頭文字 |
| 消費税基本通達 | 消基通 | `shkt` | 消基通の頭文字 |
| 租税特別措置法関係通達（法人） | 措通法 | `stho` | 措通法の頭文字 |
| 租税特別措置法関係通達（所得） | 措通所 | `stsh` | 措通所の頭文字 |
| 相続税法基本通達 | 相基通 | `szkt` | 相基通の頭文字 |
| 移転価格事務運営指針 | — | `tpg` | Transfer Pricing Guidelines |

### 判例DB コード

```
text/{case_id}.txt   # 数値ID（既存互換）
例: text/10862.txt
```

---

## cite_key → URL 変換規則（完全決定論的）

```
cite_key: 法法22       → ai-law-db/text/hojin/22.txt
cite_key: 法法22の2    → ai-law-db/text/hojin/22-2.txt  （の→-）
cite_key: 措法66の6    → ai-law-db/text/sochi/66-6.txt
cite_key: 法基通2-1-1  → ai-tsutatsu-db/text/hkt/2-1-1.txt
cite_key: 所基通36-37  → ai-tsutatsu-db/text/skt/36-37.txt
```

変換規則:
- `の` → `-`
- `条` は省略
- 枝番は `-` で接続

---

## llms.txt（AIが記憶するAPIドキュメント）

**場所**: `.well-known/llms.txt`（ポータルリポジトリ）
**サイズ**: ~1,500トークン（10K制約内で最大限の情報を持たせる）
**目的**: 一度読んだAIが以降ナビゲーション不要になること

```markdown
# jplawdb2: 日本税法AIデータベース
# 設計: 本ドキュメントを読んだAIは全条文に直アクセス可能

## URL構造
https://jplawdb2.github.io/{db}/text/{code}/{id}.txt

## 法令DB (ai-law-db)
hojin      = 法人税法（法法）
hojin-rei  = 法人税法施行令（法令）
hojin-ki   = 法人税法施行規則（法規）
sochi      = 租税特別措置法（措法）
sochi-rei  = 措置法施行令（措令）
sochi-ki   = 措置法施行規則（措規）
shotoku    = 所得税法（所法）
shotoku-rei = 所得税法施行令（所令）
shohi      = 消費税法（消法）
sozoku     = 相続税法（相法）

## 通達DB (ai-tsutatsu-db)
hkt   = 法人税基本通達（法基通）
skt   = 所得税基本通達（所基通）
shkt  = 消費税基本通達（消基通）
stho  = 措置法通達（法人税関係）
stsh  = 措置法通達（所得税関係）
szkt  = 相続税法基本通達（相基通）
tpg   = 移転価格事務運営指針

## 判例DB (ai-hanketsu-db)
text/{case_id}.txt  ← 数値ID（catalog.jsonで検索）

## cite_key → URL変換
「の」→「-」、条番号の枝番は「-」で接続
例: 法法22の2 → text/hojin/22-2.txt
例: 措法66の6 → text/sochi/66-6.txt
例: 法基通2-1-1 → text/hkt/2-1-1.txt （通達DBのtext/）

## よく使われる条文（直リンク）
法法22   https://jplawdb2.github.io/ai-law-db/text/hojin/22.txt
法法22の2 https://jplawdb2.github.io/ai-law-db/text/hojin/22-2.txt
法法37   https://jplawdb2.github.io/ai-law-db/text/hojin/37.txt
措法66の6 https://jplawdb2.github.io/ai-law-db/text/sochi/66-6.txt
法基通2-1-1 https://jplawdb2.github.io/ai-tsutatsu-db/text/hkt/2-1-1.txt

## 探索が必要な場合（ID不明時）
GET https://jplawdb2.github.io/ai-law-db/meta/catalog.json
GET https://jplawdb2.github.io/ai-law-db/meta/{code}.json
GET https://jplawdb2.github.io/ai-hanketsu-db/meta/catalog.json
```

---

## DB構造（v1.0から変更なし）

```
{db}/
├── text/
│   └── {code}/
│       └── {id}.txt      ← YAML front matter + 本文
├── meta/
│   ├── catalog.json       ← DBメタ（~1KB）
│   └── {code}.json        ← 条文タイトルマップ
└── README.md
```

---

## text/ ヘッダー（YAML front matter）

### 法令

```yaml
---
law_code: hojin
law_name: 法人税法
law_num: 昭和四十年法律第三十四号
article: "22"
title: 各事業年度の所得の金額の計算
cite_key: 法法22
egov_url: https://laws.e-gov.go.jp/law/340AC0000000034#222
as_of: "2026-02-21"
db: law
related:
  - hojin-rei:25
---
```

### 通達

```yaml
---
doc_code: hkt
doc_name: 法人税基本通達
item: "2-1-1"
title: 棚卸資産の取得価額
cite_key: 法基通2-1-1
as_of: "2026-02-21"
db: tsutatsu
---
```

### 判例

```yaml
---
case_id: "10862"
title: 相続税無申告加算税賦課決定処分取消請求事件
court: 大阪地方裁判所
date: 2008-01-16
result: 取消
topics:
  - 相続税
laws:
  - sozoku:27-1
cite_key: 大阪地判平20.1.16
db: hanketsu
---
## 主文
...
```

---

## 廃止するもの

| 廃止 | 理由 |
|------|------|
| enhanced/ | egov_urlで代替 |
| resolve系5世代 | llms.txt + meta/ に統合 |
| llms.txt多世代 | .well-known/llms.txt 1本化 |
| shards（法令） | meta/{code}.jsonで代替 |
| data/ ディレクトリ | meta/ に統合 |

---

## meta/catalog.json

```json
{
  "version": "2.0",
  "db": "law",
  "base_url": "https://jplawdb2.github.io/ai-law-db",
  "as_of": "2026-02-21",
  "collections": {
    "hojin": { "name": "法人税法", "count": 170,
                "toc": "meta/hojin.json" },
    "sochi": { "name": "租税特別措置法", "count": 496,
                "toc": "meta/sochi.json" }
  }
}
```

`toc` フィールドで次のURLを明示 → AIがURL構造を推測不要。

---

## リリース戦略

```
Phase 1: 法令DB（hojin, sochi, hojin-rei, sochi-rei, shotoku, shohi）+ ポータル
Phase 2: 通達DB（hkt, skt, stho）+ 残法令
Phase 3: 判例DB（別設計）
```

---

## v1.0からの変更点

| 項目 | v1.0 | v2.0 | 理由 |
|------|------|------|------|
| 中心原則 | ナビゲーション最適化 | **直アクセス可能性** | 設計哲学の転換 |
| law_code | `sozei_tokubetsu_sochi` | `sochi` | 略称から推測可能に |
| llms.txt | 10行以内 | ~1,500トークン | AIが記憶するAPIドキュメント化 |
| catalog.json | toc URLなし | `toc` フィールド追加 | URL推測不要 |
| 設計優先順位 | 発見→ナビ→直アクセス | **直アクセス→発見→ナビ** | 逆転 |
