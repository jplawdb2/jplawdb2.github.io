# jplawdb2 ディレクトリ構造

```
jplawdb2.github.io/
├── .well-known/
│   └── llms.txt          # AIアクセスポイント
├── text/
│   ├── hojin/            # 法人税法
│   │   ├── 22.txt
│   │   └── 22_2.txt
│   ├── hojin-rei/        # 法人税法施行令
│   ├── hojin-ki/         # 法人税法施行規則
│   ├── sochi/            # 租税特別措置法
│   ├── sochi-rei/        # 租税特別措置法施行令
│   ├── sochi-ki/         # 租税特別措置法施行規則
│   ├── shotoku/          # 所得税法
│   ├── shotoku-rei/      # 所得税法施行令
│   ├── shohi/            # 消費税法
│   ├── sozoku/           # 相続税法
│   ├── hojin-kihon/      # 法人税基本通達
│   ├── shotoku-kihon/    # 所得税基本通達
│   ├── shohi-kihon/      # 消費税基本通達
│   ├── sochi-tsu-hojin/  # 措置法通達（法人税編）
│   ├── sochi-tsu-shotoku/# 措置法通達（所得税編）
│   ├── sozoku-kihon/     # 相続税法基本通達
│   ├── tpg/              # 移転価格事務運営指針
│   └── hanrei/           # 判例
│       ├── 13082.txt     # 数値ID
│       └── cfc-denso-2016-sc.txt  # エイリアス
├── meta/
│   ├── catalog.json      # 全体カタログ（~5KB）
│   ├── hojin.json        # 条文タイトルマップ
│   ├── hanrei.json       # 判例インデックス
│   └── {code}.json       # 各法令のメタデータ
├── tools/
│   ├── build.py          # ビルドスクリプト
│   ├── validate.py       # 検証
│   └── test_cite_key.py  # cite_key変換テスト
├── laws.json             # SSOT（全法令定義）
├── Makefile              # ビルドコマンド
├── SCHEMA.md             # 設計仕様
├── 404.html              # AI向けエラーページ
└── .nojekyll
```

## Phase 1 対象（6法令）

| コード | 法令名 | cite_prefix |
|--------|--------|-------------|
| hojin | 法人税法 | 法法 |
| hojin-rei | 法人税法施行令 | 法令 |
| hojin-ki | 法人税法施行規則 | 法規 |
| sochi | 租税特別措置法 | 措法 |
| sochi-rei | 租税特別措置法施行令 | 措令 |
| shotoku | 所得税法 | 所法 |

## Phase 2 対象（残り法令 + 通達 + 指針）

| コード | 法令名 | タイプ |
|--------|--------|--------|
| sochi-ki | 租税特別措置法施行規則 | law |
| shotoku-rei | 所得税法施行令 | law |
| shohi | 消費税法 | law |
| sozoku | 相続税法 | law |
| hojin-kihon | 法人税基本通達 | circular |
| shotoku-kihon | 所得税基本通達 | circular |
| shohi-kihon | 消費税基本通達 | circular |
| sochi-tsu-hojin | 措置法通達（法人税編） | circular |
| sochi-tsu-shotoku | 措置法通達（所得税編） | circular |
| sozoku-kihon | 相続税法基本通達 | circular |
| tpg | 移転価格事務運営指針 | guideline |
