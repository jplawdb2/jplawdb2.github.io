# SCHEMA.md — jplawdb2 Design Specification v4.0

> **Version**: 4.0
> **Date**: 2026-02-21
> **Status**: Final
> **Repository**: `jplawdb2.github.io`

---

## 1. Design Principles

### 1.1 First Principle: Direct Accessibility

Every legal text must be reachable via a **permanent, predictable URL** without requiring search, API calls, or JavaScript execution.

```
https://jplawdb2.github.io/text/{code}/{id}.txt
```

This URL is the **canonical, permanent identifier** for each document. It will never change.

### 1.2 Core Design Decisions

| Decision | Rationale |
|----------|-----------|
| Single-repo integration | All DBs (laws, circulars, cases) in one `jplawdb2.github.io` repository |
| Plain `.txt` with YAML front matter | Machine-readable, human-readable, zero dependencies |
| Static files on GitHub Pages | Free hosting, CDN, no backend required |
| `laws.json` as SSOT | Single Source of Truth drives all build outputs |
| Deterministic URL scheme | `{code}/{id}.txt` — predictable without any index lookup |

---

## 2. Repository Structure

```
jplawdb2.github.io/
├── .well-known/
│   └── llms.txt              # LLM discovery endpoint (auto-generated)
├── text/
│   ├── hojin/                # 法人税法
│   │   ├── 22.txt
│   │   ├── 22_2.txt          # 第22条の2
│   │   └── ...
│   ├── hojin-rei/            # 法人税法施行令
│   ├── hojin-ki/             # 法人税法施行規則
│   ├── sochi/                # 租税特別措置法
│   │   └── 66_6.txt          # 第66条の6
│   ├── sochi-rei/            # 措置法施行令
│   ├── sochi-ki/             # 措置法施行規則
│   ├── shotoku/              # 所得税法
│   ├── shotoku-rei/          # 所得税法施行令
│   ├── shohi/                # 消費税法
│   ├── sozoku/               # 相続税法
│   ├── hojin-kihon/          # 法基通（Phase 2）
│   ├── shotoku-kihon/        # 所基通（Phase 2）
│   ├── shohi-kihon/          # 消基通（Phase 2）
│   ├── sochi-tsu-hojin/      # 措置法通達・法人税関係（Phase 2）
│   ├── sochi-tsu-shotoku/    # 措置法通達・所得税関係（Phase 2）
│   ├── sozoku-kihon/         # 相基通（Phase 2）
│   ├── tpg/                  # 移転価格事務運営指針（Phase 2）
│   └── hanrei/               # 判例（Phase 3）
│       ├── 13082.txt         # 数値ID
│       └── cfc-denso-2016-sc.txt  # エイリアス
├── meta/
│   ├── catalog.json          # DB全体カタログ
│   ├── hojin.json            # 条文タイトルマップ
│   ├── sochi.json
│   ├── hanrei.json           # 判例インデックス
│   ├── deleted_articles.json # 削除条文の記録
│   └── ...                   # 各code毎に1ファイル
├── laws.json                 # SSOT（Single Source of Truth）
├── SCHEMA.md                 # This file
├── 404.html                  # Custom 404 page
└── .nojekyll                 # Disable Jekyll processing
```

---

## 3. Code System (`{code}`)

### 3.1 Laws — `{tax}-{type}` Pattern

| Code | Japanese Name | Abbreviation | Tax Category |
|------|---------------|-------------|--------------|
| `hojin` | 法人税法 | 法法 | Corporate |
| `hojin-rei` | 法人税法施行令 | 法令 | Corporate |
| `hojin-ki` | 法人税法施行規則 | 法規 | Corporate |
| `sochi` | 租税特別措置法 | 措法 | Special Measures |
| `sochi-rei` | 措置法施行令 | 措令 | Special Measures |
| `sochi-ki` | 措置法施行規則 | 措規 | Special Measures |
| `shotoku` | 所得税法 | 所法 | Income |
| `shotoku-rei` | 所得税法施行令 | 所令 | Income |
| `shohi` | 消費税法 | 消法 | Consumption |
| `sozoku` | 相続税法 | 相法 | Inheritance |

### 3.2 Circulars — `{tax}-kihon` or `{tax}-tsu-{target}` Pattern

| Code | Japanese Name | Abbreviation |
|------|---------------|-------------|
| `hojin-kihon` | 法人税基本通達 | 法基通 |
| `shotoku-kihon` | 所得税基本通達 | 所基通 |
| `shohi-kihon` | 消費税基本通達 | 消基通 |
| `sochi-tsu-hojin` | 措置法通達（法人税関係） | 措通（法） |
| `sochi-tsu-shotoku` | 措置法通達（所得税関係） | 措通（所） |
| `sozoku-kihon` | 相続税法基本通達 | 相基通 |
| `tpg` | 移転価格事務運営指針 | TPG |

> **Note**: `tpg` is an exception to the naming pattern, using the international abbreviation (Transfer Pricing Guidelines).

### 3.3 Cases

| Code | Description |
|------|-------------|
| `hanrei` | Court cases and tribunal rulings |

---

## 4. File Naming Rules

### 4.1 Article ID (`{id}`)

| Pattern | Rule | Example |
|---------|------|---------|
| Simple article | Number only | `22.txt` (第22条) |
| Article with の | `_` (underscore) replaces の | `66_6.txt` (第66条の6) |
| Nested の | Chain underscores | `10_4_2_3.txt` (第10条の4の2の3) |
| Supplementary provisions | `fusoku_{n}.txt` | `fusoku_1.txt` (附則第1条) — Phase 2 |
| Schedules | `beppyo_{n}.txt` | `beppyo_1.txt` (別表第一) — Phase 2 |

### 4.2 Deleted Articles

Deleted articles do **not** get a `.txt` file. They are recorded in:

```
meta/deleted_articles.json
```

### 4.3 URL Examples

```
https://jplawdb2.github.io/text/hojin/22.txt          # 法法22条
https://jplawdb2.github.io/text/hojin/22_2.txt         # 法法22条の2
https://jplawdb2.github.io/text/sochi/66_6.txt          # 措法66条の6
https://jplawdb2.github.io/text/sochi-rei/39_14_3.txt   # 措令39条の14の3
https://jplawdb2.github.io/text/hojin-kihon/9_1_1.txt   # 法基通9-1-1（Phase 2）
https://jplawdb2.github.io/text/hanrei/13082.txt         # 判例（Phase 3）
https://jplawdb2.github.io/text/hanrei/cfc-denso-2016-sc.txt  # エイリアス（Phase 3）
```

---

## 5. File Format

### 5.1 YAML Front Matter

Every `.txt` file begins with YAML front matter delimited by `---`:

```yaml
---
schema_version: 1
code: sochi
article_id: 66_6
title: 内国法人に係る特定外国子会社等の課税の特例
cite_key: 措法66の6
law_num: 昭和三十七年法律第二十六号
last_amended: "2024-04-01"
status: current
related_tsutatsu:
  - sochi-tsu-hojin/66_6_1
related_cases:
  - 13082
---
```

### 5.2 Front Matter Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | integer | Yes | Always `1` for this schema |
| `code` | string | Yes | Code identifier (e.g., `sochi`) |
| `article_id` | string | Yes | Article ID (e.g., `66_6`) |
| `title` | string | Yes | Article title in Japanese |
| `cite_key` | string | Yes | Human-readable citation key (e.g., `措法66の6`) |
| `law_num` | string | Yes | Official law number |
| `last_amended` | string | Yes | Date of last amendment (ISO 8601) |
| `status` | string | Yes | `current` or `repealed` |
| `egov_url` | string | No | Link to e-Gov source |
| `related_tsutatsu` | list | No | Related circular `{code}/{id}` references |
| `related_cases` | list | No | Related case IDs |
| `token_estimate` | integer | No | Token count estimate (o200k_base) |
| `chunks` | integer | No | Number of pre-split chunk files for long documents |

### 5.3 Chunk File Format (`{id}__cN.txt`)

When a main file is large, chunk files are generated under the same code directory:

```
text/{code}/{id}__c1.txt
text/{code}/{id}__c2.txt
...
```

Chunk YAML fields:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `schema_version` | integer | Yes | Always `1` |
| `code` | string | Yes | Code identifier |
| `article_id` | string | Yes | Parent article/source ID |
| `chunk_index` | integer | Yes | 1-based chunk index |
| `chunk_total` | integer | Yes | Total chunk count |
| `parent` | string | Yes | Parent file path (`text/{code}/{id}.txt`) |
| `para_range` | string | No | Paragraph marker range (for `[pN]` sources) |
| `section_range` | string | No | Heading/section range (for non-`[pN]` sources) |
| `cite_key` | string | No | Parent cite key |

### 5.4 Body

After the front matter, the body contains the **plain text of the article** — the full statutory text including all paragraphs (項), items (号), and sub-items.

---

## 6. Metadata Files

### 6.1 `meta/catalog.json` — Database Catalog

The top-level catalog describing the entire database:

```json
{
  "schema_version": 1,
  "base_url": "https://jplawdb2.github.io",
  "as_of": "2026-02-21",
  "codes": {
    "hojin": {
      "name": "法人税法",
      "type": "law",
      "count": 170,
      "toc": "meta/hojin.json"
    },
    "hojin-rei": {
      "name": "法人税法施行令",
      "type": "law",
      "count": 310,
      "toc": "meta/hojin-rei.json"
    },
    "sochi": {
      "name": "租税特別措置法",
      "type": "law",
      "count": 145,
      "toc": "meta/sochi.json"
    },
    "hojin-kihon": {
      "name": "法人税基本通達",
      "type": "circular",
      "parent": "hojin",
      "count": 1523,
      "toc": "meta/hojin-kihon.json"
    },
    "hanrei": {
      "name": "判例",
      "type": "case",
      "count": 3057,
      "index": "meta/hanrei.json"
    }
  }
}
```

**Fields per code entry:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Japanese display name |
| `type` | string | Yes | `law`, `circular`, or `case` |
| `parent` | string | No | Parent code (for circulars) |
| `count` | integer | Yes | Number of documents |
| `toc` | string | Conditional | Path to article title map (laws/circulars) |
| `index` | string | Conditional | Path to case index (cases only) |

### 6.2 `meta/{code}.json` — Article Title Map

Per-code index mapping article IDs to titles and file sizes:

```json
{
  "code": "sochi",
  "article_count": 145,
  "articles": {
    "66_6": {
      "title": "内国法人に係る特定外国子会社等の課税の特例",
      "size": 18432
    },
    "66_7": {
      "title": "特定外国子会社等に係る所得の課税の特例",
      "size": 12288
    },
    "70_7": {
      "title": "非上場株式等についての贈与税の納税猶予及び免除",
      "size": 108544
    }
  }
}
```

**Fields per article entry:**

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Article title in Japanese |
| `size` | integer | File size in bytes |

### 6.3 `meta/hanrei.json` — Case Index

```json
{
  "code": "hanrei",
  "case_count": 3057,
  "aliases": {
    "cfc-denso-2016-sc": 13082
  },
  "cases": {
    "13082": {
      "title": "デンソー事件・最高裁平成29年10月24日判決",
      "court": "最高裁判所第三小法廷",
      "date": "2017-10-24",
      "aliases": ["cfc-denso-2016-sc"],
      "tags": ["CFC", "措法66の6"]
    }
  }
}
```

### 6.4 `meta/deleted_articles.json` — Deleted Articles Record

```json
{
  "hojin": {
    "25": {
      "title": "（削除）",
      "deleted_by": "平成XX年法律第YY号",
      "deleted_date": "2020-04-01"
    }
  }
}
```

---

## 7. Case Access: Three-Layer Model

Cases are accessible through three complementary layers:

```
Layer 1: Alias Access (Top ~50 landmark cases)
  └─ text/hanrei/cfc-denso-2016-sc.txt
  └─ Listed in .well-known/llms.txt

Layer 2: Index Lookup (All cases)
  └─ meta/hanrei.json → find case_id by title/tag search
  └─ Enables discovery of any case

Layer 3: Direct ID Access (All cases)
  └─ text/hanrei/{case_id}.txt
  └─ Numeric ID from ai-law-db
```

### Alias Naming Convention

```
{topic}-{party}-{year}-{court}
```

| Suffix | Court |
|--------|-------|
| `sc` | Supreme Court (最高裁) |
| `hc` | High Court (高裁) |
| `dc` | District Court (地裁) |

Example: `cfc-denso-2016-sc` = CFC + Denso + 2016 + Supreme Court

---

## 8. LLM Discovery: `.well-known/llms.txt`

Auto-generated file enabling LLM tools to discover and use this database:

```
# jplawdb2 — Japanese Tax Law Database
# https://jplawdb2.github.io

> Base URL: https://jplawdb2.github.io
> Catalog: https://jplawdb2.github.io/meta/catalog.json

## URL Pattern
text/{code}/{article_id}.txt

## Available Codes
- hojin: 法人税法 (170 articles)
- sochi: 租税特別措置法 (145 articles)
- ...

## Key Cases (Aliases)
- cfc-denso-2016-sc: デンソー事件・最高裁平成29年
- ...
```

---

## 9. Build System

### 9.1 Build Pipeline

```
laws.json (SSOT)
    │
    ▼
 build.py
    │
    ├──► text/{code}/{id}.txt       (article files with YAML front matter)
    ├──► meta/catalog.json          (database catalog)
    ├──► meta/{code}.json           (article title maps with size field)
    └──► .well-known/llms.txt       (LLM discovery file, auto-generated)
```

### 9.2 Make Targets

```makefile
make build          # Full build from laws.json
make validate       # Validate all files against schema
make test-cite-key  # Verify cite_key consistency
```

### 9.3 `laws.json` — Single Source of Truth

The `laws.json` file is the **sole input** to the build process. It contains all raw law data retrieved from e-Gov API. The build script (`build.py`) transforms this into the output files. No manual editing of `text/` or `meta/` files should occur.

---

## 10. Phase Strategy

### Phase 1: Core Laws + Portal

**Scope:**
- 6 law codes: `hojin`, `sochi`, `hojin-rei`, `sochi-rei`, `shotoku`, `shohi`
- Main provisions only (`MainProvision`)
- Supplementary provisions (附則) and schedules (別表) deferred to Phase 2

**Estimated Output:**
- ~2,000 articles
- ~13 MB total

**Deliverables:**
- `text/{code}/{id}.txt` for all 6 codes
- `meta/catalog.json`
- `meta/{code}.json` for each code
- `.well-known/llms.txt`
- `SCHEMA.md`
- `404.html`, `.nojekyll`

### Phase 2: Full Laws + Circulars

**Scope:**
- Expand to 24 law codes (add施行規則, remaining tax categories)
- Add circulars: `hojin-kihon`, `shotoku-kihon`, `sochi-tsu-hojin`, etc.
- Supplementary provisions (`fusoku_{n}.txt`)
- Schedules (`beppyo_{n}.txt`)
- Large article splitting strategy (for articles >100KB)
- MCP server support

### Phase 3: Cases + Historical Versions

**Scope:**
- `text/hanrei/` — full case database (~3,057 cases)
- Alias system for landmark cases
- Historical versions: `text/hojin/22@2016.txt`

---

## 11. Deprecated / Removed

The following legacy components are **permanently removed** in v4.0:

| Removed | Replaced By |
|---------|-------------|
| `enhanced/` directory | `egov_url` field in YAML front matter |
| `resolve` system (5 generations) | `llms.txt` + `meta/` files |
| Multiple `llms.txt` versions | Single `.well-known/llms.txt` |
| `shards/` system | `meta/{code}.json` per-code indexes |

---

## 12. Future Considerations

### 12.1 Historical Versions (Phase 3)

```
text/hojin/22@2016.txt    # 法法22条 as of 2016
text/hojin/22.txt          # Always current version
```

### 12.2 Large Article Splitting (Phase 2)

Articles exceeding ~100KB (e.g., 措法70の7 at ~106KB) may be split:

```
text/sochi/70_7.txt        # Full article (default)
text/sochi/70_7_p1.txt     # Paragraph 1 only (if split)
```

Strategy to be finalized in Phase 2 design.

### 12.3 MCP Server (Phase 2)

Model Context Protocol server providing structured access to the database for AI tools. Will wrap the static file structure with search and filtering capabilities.

---

## Appendix A: Full URL Examples

```
# Laws
https://jplawdb2.github.io/text/hojin/22.txt           # 法法22条（各事業年度の所得の金額の計算）
https://jplawdb2.github.io/text/hojin/22_2.txt          # 法法22条の2（収益の額）
https://jplawdb2.github.io/text/sochi/66_6.txt           # 措法66条の6（CFC税制）
https://jplawdb2.github.io/text/sochi-rei/39_14_3.txt    # 措令39条の14の3
https://jplawdb2.github.io/text/hojin-rei/4_1.txt        # 法令4条の1
https://jplawdb2.github.io/text/shotoku/36.txt           # 所法36条（収入金額）
https://jplawdb2.github.io/text/shohi/30.txt             # 消法30条（仕入税額控除）

# Circulars (Phase 2)
https://jplawdb2.github.io/text/hojin-kihon/9_1_1.txt   # 法基通9-1-1
https://jplawdb2.github.io/text/sochi-tsu-hojin/66_6_1.txt  # 措通（法）66の6-1

# Cases (Phase 3)
https://jplawdb2.github.io/text/hanrei/13082.txt         # 数値IDアクセス
https://jplawdb2.github.io/text/hanrei/cfc-denso-2016-sc.txt  # エイリアスアクセス

# Metadata
https://jplawdb2.github.io/meta/catalog.json             # DB全体カタログ
https://jplawdb2.github.io/meta/hojin.json               # 法人税法 条文マップ
https://jplawdb2.github.io/meta/hanrei.json               # 判例インデックス
https://jplawdb2.github.io/.well-known/llms.txt           # LLM discovery
```

---

*End of SCHEMA.md v4.0*
