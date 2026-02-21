# jplawdb2

Japanese Tax Law AI Database — designed for LLMs that need direct, 1-hop access to any legal text.

## Quick Start

Read `.well-known/llms.txt` once. After that, construct URLs directly:

```
https://jplawdb2.github.io/text/{code}/{id}.txt
```

Example:
```
https://jplawdb2.github.io/text/sochi/66_6.txt   # 措法66条の6
https://jplawdb2.github.io/text/hojin/22.txt      # 法法22条
https://jplawdb2.github.io/text/hojin-kihon/2-1-1.txt  # 法基通2-1-1
```

## Databases

| Content | Path | Phase |
|---------|------|-------|
| Laws (法令) | `text/{code}/*.txt` | 1+ |
| Circulars (通達) | `text/{code}/*.txt` | 2+ |
| Court Cases (判例) | `text/hanrei/*.txt` | 3 |

## Navigation

```
meta/catalog.json      <- Full catalog
meta/{code}.json       <- Article title index
.well-known/llms.txt   <- LLM discovery / URL schema
```

## Design Specification

See [SCHEMA.md](./SCHEMA.md).

## Build

```bash
# Requires e-Gov XML files in repo root
pip install lxml
make build-phase1    # Phase 1: 6 laws
make validate
```
