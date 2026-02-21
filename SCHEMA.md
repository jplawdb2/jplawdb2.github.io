# jplawdb2 設計仕様 v3.0

> 2ラウンド×2セッションのエージェント議論（ai-consumer / architect / builder / critic）による合意。2026-02-21

---

## 設計哲学

### 第一原則: 直アクセス可能性

**URLを知識として持つAIは、ナビゲーション不要で本文に1ホップで到達できる。**

```
AI「措法66の6が必要」
  ↓ llms.txt を一度読んでいれば
GET https://jplawdb2.github.io/ai-law-db/text/sochi/66_6.txt
```

### 優先順位

```
1. 直アクセス（llms.txtを知るAIが1ホップ）← Primary
2. 参照表アクセス（llms.txtを読んで構築）
3. ナビゲーション（catalog → meta → text）← Fallback
```

### llms.txtの位置づけ

「発見のための入口」ではなく、**AIが参照してURLを構築するAPIドキュメント**。
一度読めば以降ナビゲーション不要。学習データに入れば永続的に有効。

---

## リポジトリ構成

```
jplawdb2/
├── jplawdb2.github.io    → https://jplawdb2.github.io/
├── ai-law-db             → https://jplawdb2.github.io/ai-law-db/
├── ai-tsutatsu-db        → https://jplawdb2.github.io/ai-tsutatsu-db/
└── ai-hanketsu-db        → https://jplawdb2.github.io/ai-hanketsu-db/
```

---

## URL構造（永久不変）

```
https://jplawdb2.github.io/{db}/text/{code}/{id}.txt
```

**URLは追加のみ許可。変更・削除は永久禁止。**

---

## コード体系（laws.json から自動生成）

### 命名規則（ルール1つで全コード推測可能）

```
{tax}           → 法律本体（最頻アクセスのため -ho 省略）
{tax}-rei       → 施行令
{tax}-ki        → 施行規則
{tax}-kihon     → 基本通達
{tax}-tsu       → 個別通達・その他
```

### 法令コード

| 法令名 | 略称 | code |
|--------|------|------|
| 法人税法 | 法法 | `hojin` |
| 法人税法施行令 | 法令 | `hojin-rei` |
| 法人税法施行規則 | 法規 | `hojin-ki` |
| 租税特別措置法 | 措法 | `sochi` |
| 租税特別措置法施行令 | 措令 | `sochi-rei` |
| 租税特別措置法施行規則 | 措規 | `sochi-ki` |
| 所得税法 | 所法 | `shotoku` |
| 所得税法施行令 | 所令 | `shotoku-rei` |
| 消費税法 | 消法 | `shohi` |
| 相続税法 | 相法 | `sozoku` |

### 通達コード

| 通達名 | 略称 | code |
|--------|------|------|
| 法人税基本通達 | 法基通 | `hojin-kihon` |
| 所得税基本通達 | 所基通 | `shotoku-kihon` |
| 消費税基本通達 | 消基通 | `shohi-kihon` |
| 措置法通達（法人税関係） | 措通法 | `sochi-tsu-hojin` |
| 措置法通達（所得税関係） | 措通所 | `sochi-tsu-shotoku` |
| 相続税法基本通達 | 相基通 | `sozoku-kihon` |
| 移転価格事務運営指針 | — | `tpg`（国際略称のため例外） |

### 判例コード

```
text/hanrei/{case_id}.txt         # 数値ID（既存互換）
text/hanrei/{alias}.txt           # 主要判例エイリアス（Layer 1）
index/hanrei.json                 # 全件インデックス（Layer 2）
```

---

## ファイル名規則

### 条番号 → ファイル名変換

| 条番号 | ファイル名 | 規則 |
|--------|----------|------|
| 第22条 | `22.txt` | そのまま |
| 第22条の2 | `22_2.txt` | 「の」→ `_` |
| 第66条の6 | `66_6.txt` | 「の」→ `_` |
| 第10条の4の2の3 | `10_4_2_3.txt` | 多段も `_` 連結 |
| 附則第1条 | `fusoku_1.txt` | 附則は `fusoku_` prefix |
| 別表第一 | `beppyo_1.txt` | 別表は `beppyo_` prefix |

**区切り文字の意味分離:**
- ディレクトリ名のハイフン `-` → 種別区切り（`hojin-rei`）
- ファイル名のアンダースコア `_` → 枝番区切り（`66_6`）
- 通達番号のハイフン `-` → 通達固有の階層（`2-1-1`、変換不要）

削除条文（5件）はファイル非作成。`meta/deleted_articles.json` に記録。

---

## laws.json（Single Source of Truth）

全コード・命名規則の唯一の管理ファイル。ビルドスクリプトが全成果物を自動生成。

```json
{
  "hojin": {
    "name_ja": "法人税法",
    "cite_prefix": "法法",
    "category": "law",
    "xml": "法人税法.xml",
    "db": "ai-law-db"
  },
  "hojin-kihon": {
    "name_ja": "法人税基本通達",
    "cite_prefix": "法基通",
    "category": "circular",
    "parent": "hojin",
    "db": "ai-tsutatsu-db"
  }
}
```

**新法令追加 = laws.jsonに1エントリ追加 → make build で全自動生成**

---

## テキストファイル形式（YAML front matter 埋め込み）

メタデータはテキストファイルに埋め込む（1リクエストで本文+メタ取得）。
`meta/` ディレクトリはDB全体インデックスのみ使用。

### 法令

```yaml
---
schema_version: 1
code: sochi
article_id: 66_6
title: 内国法人に係る特定外国子会社等の課税の特例
cite_key: 措法66の6
law_num: 昭和三十七年法律第二十六号
last_amended: "2024-04-01"
db: ai-law-db
related_tsutatsu:
  - sochi-tsu-hojin/66_6_1
related_cases:
  - 13082
---
（条文本文）
```

### 通達

```yaml
---
schema_version: 1
code: hojin-kihon
item_id: 2-1-1
title: 棚卸資産の取得価額
cite_key: 法基通2-1-1
last_amended: "2024-04-01"
db: ai-tsutatsu-db
related_law:
  - hojin/29
---
（通達本文）
```

### 判例

```yaml
---
schema_version: 1
case_id: "13082"
alias: cfc-denso-2016-sc
title: デンソー事件
court: 最高裁判所
date: 2016-02-29
result: 棄却
topics:
  - CFC課税
  - 措法66の6
laws:
  - sochi/66_6
cite_key: 最判平28.2.29
db: ai-hanketsu-db
---
## 主文
...
## 事案の概要
...
## 判断
...
```

**9フィールド共通**: schema_version / code（またはcase_id）/ id / title / cite_key / last_amended / db / related_* / (法令はlaw_num追加)

---

## .well-known/llms.txt（AIが参照するAPIドキュメント）

**重要: URLを推測せず、必ずこの対応表を参照してください。**

```markdown
# jplawdb2: 日本税法AIデータベース v3.0

## URL構造
https://jplawdb2.github.io/{db}/text/{code}/{id}.txt

## 法令DB (ai-law-db)
命名規則: {税目}-{種別}（-rei=施行令、-ki=施行規則）
hojin       = 法人税法（法法）
hojin-rei   = 法人税法施行令（法令）
hojin-ki    = 法人税法施行規則（法規）
sochi       = 租税特別措置法（措法）
sochi-rei   = 措置法施行令（措令）
shotoku     = 所得税法（所法）
shotoku-rei = 所得税法施行令（所令）
shohi       = 消費税法（消法）
sozoku      = 相続税法（相法）

## 通達DB (ai-tsutatsu-db)
命名規則: {税目}-kihon=基本通達、{税目}-tsu-{対象}=個別通達
※ 通達コードは推測不可。必ずこの表を参照してください。
hojin-kihon       = 法人税基本通達（法基通）
shotoku-kihon     = 所得税基本通達（所基通）
shohi-kihon       = 消費税基本通達（消基通）
sochi-tsu-hojin   = 措置法通達（法人税関係）
sochi-tsu-shotoku = 措置法通達（所得税関係）
sozoku-kihon      = 相続税法基本通達（相基通）
tpg               = 移転価格事務運営指針

## 判例DB (ai-hanketsu-db)
text/hanrei/{alias}.txt        ← 主要判例（エイリアスあり）
text/hanrei/{case_id}.txt      ← 全判例（数値ID）
index/hanrei.json              ← 検索用インデックス（事件名・条文・キーワード）

## ファイル名変換規則
「の」→ 「_」（アンダースコア）
例: 措法66の6 → sochi/66_6.txt
例: 法法22の2の3 → hojin/22_2_3.txt
附則: fusoku_1.txt / 別表: beppyo_1.txt
通達の「-」はそのまま: 法基通2-1-1 → hojin-kihon/2-1-1.txt

## よく使う直アクセスURL
法法22   https://jplawdb2.github.io/ai-law-db/text/hojin/22.txt
措法66の6 https://jplawdb2.github.io/ai-law-db/text/sochi/66_6.txt
法基通2-1-1 https://jplawdb2.github.io/ai-tsutatsu-db/text/hojin-kihon/2-1-1.txt
デンソー事件 https://jplawdb2.github.io/ai-hanketsu-db/text/hanrei/cfc-denso-2016-sc.txt

## よくある間違い（ハルシネーション防止）
✗ 通達コードをローマ字で推測 → ✓ 上の対応表を参照
✗ 「の」をそのままURLに含める → ✓ アンダースコアに変換
✗ 判例を条文名で直アクセス → ✓ index/hanrei.jsonで検索
✗ 項・号単位のファイルを探す → ✓ 条単位ファイルから本文内で特定

## このDBでできないこと
- 全文キーワード検索（横断検索は不可）
- 判例の意味検索（index.jsonのフィールドフィルタリングのみ）
- 旧法令の参照（最新版のみ提供）
```

---

## meta/ ディレクトリ（DB全体インデックスのみ）

```
{db}/meta/
├── catalog.json     ← DBメタ（base_url、コード一覧、件数）~1KB
├── {code}.json      ← 条文タイトルマップ（AI探索用）
└── hanrei.json      ← 判例インデックス（hanketsu-dbのみ）
```

### meta/catalog.json

```json
{
  "schema_version": 1,
  "db": "ai-law-db",
  "base_url": "https://jplawdb2.github.io/ai-law-db",
  "as_of": "2026-02-21",
  "collections": {
    "hojin": { "name": "法人税法", "count": 170,
               "toc": "meta/hojin.json" }
  }
}
```

### meta/{code}.json（条文タイトルマップ）

```json
{
  "law": "hojin",
  "article_count": 170,
  "articles": {
    "22": "各事業年度の所得の金額の計算",
    "22_2": "収益の額",
    "66_6": "内国法人に係る特定外国子会社等の課税の特例"
  }
}
```

---

## 判例の三層アクセスモデル

法令と判例では「直アクセス」の前提が異なる（法令は条文番号という普遍的識別子があるが判例にはない）。

```
Layer 1: エイリアス直アクセス（主要判例~50件）
  llms.txtにエイリアス一覧を記載
  text/hanrei/cfc-denso-2016-sc.txt

Layer 2: 構造化インデックス検索（全判例）
  index/hanrei.json → case_id, title, court, date, topics, laws
  → 条文コードや年代でフィルタリング

Layer 3: 数値ID直アクセス
  text/hanrei/13082.txt
```

---

## ビルドパイプライン

```
laws.json (SSOT)
    |
build.py (~200行Python)
    |
    ├── text/{code}/{id}.txt   (YAML front matter + 本文)
    ├── meta/catalog.json
    ├── meta/{code}.json
    ├── meta/hanrei.json       (hanketsu-dbのみ)
    ├── .well-known/llms.txt   (自動生成)
    └── .nojekyll
```

```
make build          # 全DB生成
make build-law      # 法令DBのみ
make validate       # YAML front matter 整合性チェック
make test-cite-key  # 全条文のcite_key→URL変換テスト
make validate-links # 全DB横断リンクチェック（ポータルで実行）
```

---

## 廃止するもの

| 廃止 | 理由 |
|------|------|
| enhanced/ | egov_url フィールドで代替 |
| resolve系5世代 | llms.txt + meta/ に統合 |
| llms.txt多世代 | .well-known/llms.txt 1本化 |
| shards（法令） | meta/{code}.jsonで代替 |
| 別ファイルのメタデータ | YAML front matter に統合 |

---

## リリース戦略

```
Phase 1: 法令DB 6法令（hojin, sochi, hojin-rei, sochi-rei, shotoku, shohi）
          + ポータル（llms.txt, SCHEMA.md）
          実績: 6法令 ~2,000条文 ~13MB（GitHub Pages 1GBの1.3%）

Phase 2: 法令DB 24法令 + 通達DB（hojin-kihon, shotoku-kihon, sochi-tsu-hojin）

Phase 3: 判例DB（三層モデル実装）+ 時系列対応検討
```

---

## 将来検討事項

| 項目 | 検討時期 |
|------|---------|
| 時系列対応: `text/hojin/22@2016.txt` | Phase 3 |
| 巨大条文の項分割（106KB条文） | Phase 2 |
| MCP ツール対応 | Phase 2 |
| クロスリファレンス自動生成 | Phase 2 |
| 措置法分割（300条超）`meta/sochi_part{n}.json` | Phase 1内 |
