# jplawdb2 設計仕様 v1.0

> 3ラウンドのエージェント議論（ai-consumer / architect / builder / critic）により合意。2026-02-21

## 設計原則

- **10Kトークン制約**: LLMが1回のコンテキストで本文に最短到達できること
- **2ホップ原則**: 典型的なアクセスパターンはポータル→本文の2ホップ以内
- **DB自律性**: 各DBはポータルなしで単体で動作できること
- **2層設計**: 全DBで `text/` + `meta/` の共通層を守り、固有層は自由

---

## A. リポジトリ構成

```
jplawdb2/
├── jplawdb2.github.io     # ポータル（ディスカバリー層）
├── ai-law-db              # 法令DB
├── ai-tsutatsu-db         # 通達DB
└── ai-hanketsu-db         # 判例DB
```

- 全て新規リポジトリ（git history引き継がない）
- jplawdb（v1）はv2安定後にdeprecation通知に置換

---

## B. DB共通骨格（2層設計）

### 共通層（全DBで必ず守る）

```
{db}/
├── text/              # 本文（YAML front matter + プレーンテキスト）
├── meta/              # メタデータ
│   ├── catalog.json   # DBメタ情報のみ（~1KB）
│   └── {code}.json    # コード別詳細目次
└── README.md          # 先頭にLLM向けナビ情報を記載
```

### 固有層（DB固有、自由に追加可能）

- `meta/aliases.json` — DB固有エイリアス（オプション）
- `meta/title_overrides.json` — XMLのCaption欠落補完（法令DB）
- `text/` 以下の階層構造 — DB固有

---

## C. meta/catalog.json（共通スキーマ）

DBメタ情報のみ。**1KB未満を厳守**。

```json
{
  "version": "2.0",
  "db": "law",
  "db_name": "法令データベース",
  "as_of": "2026-02-21",
  "base_url": "https://jplawdb2.github.io/ai-law-db",
  "collections": {
    "hojinzei": { "name": "法人税法", "count": 234 }
  }
}
```

- `base_url` を含め、DB単体で独立動作可能（ポータル障害時の自律性）
- `collections` には `name` + `count` のみ（エントリ一覧は `{code}.json` へ）

---

## D. meta/{code}.json（条文タイトル付きフラットマップ）

```json
{
  "law_name": "法人税法",
  "law_code": "hojinzei",
  "article_count": 234,
  "articles": {
    "1": "趣旨",
    "22": "各事業年度の所得の金額の計算",
    "37": "寄附金の損金不算入"
  }
}
```

- **300条超の法令**（措置法等）は分割: `{code}.json` を「目次の目次」にし、`{code}_part{n}.json` に分割
- 措置法のように条文タイトルがない場合は節見出しで補完 → `meta/title_overrides.json`

---

## E. text/ ヘッダー仕様（YAML front matter）

### 法令（ai-law-db）

```yaml
---
law_code: hojinzei
law_name: 法人税法
law_num: 昭和四十年法律第三十四号
article: "22"
title: 各事業年度の所得の金額の計算
cite_key: 法法22
egov_url: https://laws.e-gov.go.jp/law/340AC0000000034#222
as_of: "2026-02-21"
db: law
related:
  - hojinzei_seirei:25
---
（条文本文）
```

**10フィールド**: law_code / law_name / law_num / article / title / cite_key / egov_url / as_of / db / related

### 判例（ai-hanketsu-db）

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
  - 相続税法27条1項
db: hanketsu
cite_key: 大阪地判平20.1.16
---
## 主文
...
## 事案の概要
...
## 判断
...
```

- 法令は `##` 見出し不使用（インデントで構造表現）
- 判例は `## セクション見出し` をoptionalで許容

### 通達（ai-tsutatsu-db）

```yaml
---
doc_code: hojinzei_kihon_tsutatsu
doc_name: 法人税法基本通達
doc_num: 法人税基本通達（昭和44年5月1日付直審（法）25）
item: "2-1-1"
title: 棚卸資産の取得価額
cite_key: 法基通2-1-1
egov_url: （通達URLまたはNTA掲載URL）
as_of: "2026-02-21"
db: tsutatsu
---
```

---

## F. ポータル（jplawdb2.github.io）

役割: **オプショナルなディスカバリー層**（SPOFにしない）

```
jplawdb2.github.io/
├── .well-known/
│   └── llms.txt       # 唯一のllms.txt（10行以内、主要法令への直リンク含む）
├── index.json         # 全DBカタログ + 全エイリアス集約
├── SCHEMA.md          # 本ファイル
└── README.md
```

### index.json（ポータル）

```json
{
  "as_of": "2026-02-21",
  "aliases": {
    "法人税法": "law:hojinzei",
    "法法": "law:hojinzei",
    "法基通": "tsutatsu:hojinzei_kihon_tsutatsu"
  },
  "dbs": {
    "law": {
      "base_url": "https://jplawdb2.github.io/ai-law-db",
      "catalog_url": "https://jplawdb2.github.io/ai-law-db/meta/catalog.json"
    },
    "tsutatsu": {
      "base_url": "https://jplawdb2.github.io/ai-tsutatsu-db",
      "catalog_url": "https://jplawdb2.github.io/ai-tsutatsu-db/meta/catalog.json"
    },
    "hanketsu": {
      "base_url": "https://jplawdb2.github.io/ai-hanketsu-db",
      "catalog_url": "https://jplawdb2.github.io/ai-hanketsu-db/meta/catalog.json"
    }
  }
}
```

---

## G. 廃止するもの

| 廃止対象 | 代替 |
|---------|------|
| `enhanced/` ディレクトリ | `egov_url` フィールドで代替 |
| `resolve.json` / `resolve.min.json` | ポータル `index.json` に統合 |
| `resolve_lite/` / `resolve_meta/` / `resolve_meta_corp/` | `meta/{code}.json` に統合 |
| `llms.txt` 4世代 | `.well-known/llms.txt` 1つに統合 |
| `shards`（法令DB） | `meta/{code}.json` のタイトル検索で代替 |

- 判例DBの shards は条件付き維持（topic別に整理して `meta/shards/` へ）

---

## H. ビルドパイプライン

```
Makefile
├── make build          # 全DB生成
├── make build-law      # 法令DBのみ
├── make validate       # meta ↔ text 整合性チェック
├── make validate-links # 全DBリンクチェック（ポータルリポジトリで実行）
└── make search-hook    # search/拡張ポイント（実装はしない）

tools/
├── parse_xml.py        # e-Gov XML → text/ 変換
├── build_meta.py       # text/ → meta/{code}.json 生成
├── validate.py         # 整合性検証
└── title_overrides.py  # Caption欠落の補完処理
```

GitHub Actions で `make build` + `make validate` を自動実行。

---

## I. 拡張ポイント（search/）

将来のセマンティック検索導入のための予約。現時点では実装しない。

```
{db}/
└── search/            # 将来のsearch層（現在は空）
```

SCHEMA.md（本ファイル）に導入基準を記載:
- 判例DB件数が10,000件を超えた場合
- meta/shards/では10K制約を満たせなくなった場合

---

## J. title_overrides.json

XMLの ArticleCaption が欠落している条文のタイトルを補完。

```json
{
  "hojinzei": {
    "22": "各事業年度の所得の金額の計算"
  },
  "sozei_tokubetsu_sochi": {
    "66-6": "内国法人の特定外国子会社等に係る所得の課税の特例"
  }
}
```

配置: `meta/title_overrides.json`（各DB内）

---

## K. v1 移行戦略

1. Phase 1（v2法令DB公開）: jplawdb v1の `README.md` にdeprecation通知追加
2. Phase 2（v2通達DB公開）: 通知を強化
3. Phase 3（v2判例DB公開）: v1の text/ ファイルをリダイレクトメッセージに置換

---

## L. ホップ最適化（2ホップ設計）

| アクセスパターン | ホップ数 | 経路 |
|----------------|---------|------|
| 直接参照（ID既知） | 1 | `text/{law}/{article}.txt` |
| エイリアス解決 | 2 | ポータル `index.json` → `text/{law}/{article}.txt` |
| 探索的（タイトルから） | 3 | ポータル → `meta/{code}.json` → `text/` |

`llms.txt` に主要法令の直リンクを含めることで、典型ケースを2ホップ以内に収める。

---

## M. 判例ID

- 既存の数値ID（`10862` 等）を維持（互換性優先）
- 事件番号（`平成20年(行ウ)第123号`）はYAML front matterの `case_id_formal` フィールドに追加（Phase 2）

---

## N. 初期スコープ（Phase 1）

**Phase 1 に含める:**
- 本則（MainProvision）のみ
- 6法令（法人税法、法人税法施行令、法人税法施行規則、措置法、措置法令、措置法規則）
- ポータル（llms.txt + index.json + SCHEMA.md）

**Phase 2 以降:**
- 附則（オリジナル附則のみ、改正附則は除外）
- 通達DB（7通達）
- 残18法令

**Phase 3:**
- 判例DB（別途設計が必要）

---

## O. 措置法の分割パターン

300条超の法令（措置法496条等）の `meta/{code}.json` 分割方法:

```json
// meta/sozei_tokubetsu_sochi.json（目次の目次）
{
  "law_name": "租税特別措置法",
  "article_count": 496,
  "parts": {
    "part1": { "range": "1-40", "url": "meta/sozei_tokubetsu_sochi_part1.json" },
    "part2": { "range": "41-80", "url": "meta/sozei_tokubetsu_sochi_part2.json" }
  }
}
```

---

## P. リリース戦略

```
Phase 1: 法令DB（6法令）+ ポータル
  → 目標: 2週間以内
  → builder実証済み: 3,059条、12.7MB（GitHub Pages 1GBの1.3%）

Phase 2: 法令DB正式版（24法令）+ 通達DB（7通達）
  → 附則追加、残18法令追加

Phase 3: 判例DB
  → 設計を別途検討（法令DBとは根本的に異なる）
  → 現行shards（topic別整理）を暫定使用
```

---

## 未解決課題（Phase 2 以降）

| # | 課題 |
|---|------|
| 1 | 判例DBのmeta設計（3,057件はcatalog.jsonに収まらない） |
| 2 | 通達のID体系（通達番号の正規化） |
| 3 | ポータル aliases.json の二重管理問題 |
| 4 | ビルドパイプラインのCI/CD完全自動化 |
| 5 | `related:` フィールドの自動生成（法令→施行令リンク） |
