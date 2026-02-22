#!/usr/bin/env python3
"""Rebuild meta/oversized.json from current text files.

Rules:
- Evaluate only main files ({id}.txt, excluding __cN)
- oversized threshold default: 10000 tokens (o200k_base)
- include chunk count from parent YAML 'chunks' (0 if absent)
- update meta/catalog.json oversized_count and generated_at
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

try:
    import tiktoken
except ImportError as e:  # pragma: no cover
    raise SystemExit("ERROR: tiktoken is required. Install with: pip install tiktoken") from e

ENC = tiktoken.get_encoding("o200k_base")

BASE_DIR = Path(__file__).parent.parent
TEXT_DIR = BASE_DIR / "text"
META_DIR = BASE_DIR / "meta"


def token_len(s: str) -> int:
    return len(ENC.encode(s))


def parse_yaml(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    out: dict[str, str] = {}
    for ln in text[4:end].splitlines():
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild meta/oversized.json from text files")
    parser.add_argument("--threshold", type=int, default=10000, help="Oversized threshold (default: 10000)")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, do not write files")
    args = parser.parse_args()

    entries: list[dict] = []
    for path in sorted(TEXT_DIR.rglob("*.txt")):
        if "__c" in path.stem:
            continue
        content = path.read_text(encoding="utf-8", errors="ignore")
        t = token_len(content)
        if t <= args.threshold:
            continue
        y = parse_yaml(content)
        code = y.get("code", path.parent.name)
        article_id = y.get("article_id", path.stem)
        cite_key = y.get("cite_key", f"{code}/{article_id}")
        try:
            chunks = int(y.get("chunks", "0"))
        except ValueError:
            chunks = 0
        entries.append(
            {
                "code": code,
                "article_id": article_id,
                "cite_key": cite_key,
                "token_estimate": t,
                "chunks": chunks,
            }
        )

    payload = {"count": len(entries), "articles": entries}

    if not args.dry_run:
        META_DIR.mkdir(parents=True, exist_ok=True)
        overs_path = META_DIR / "oversized.json"
        overs_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        cat_path = META_DIR / "catalog.json"
        if cat_path.exists():
            cat = json.loads(cat_path.read_text(encoding="utf-8"))
            cat["oversized_count"] = len(entries)
            cat["oversized_index"] = "meta/oversized.json"
            cat["generated_at"] = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
            if "codes" in cat and isinstance(cat["codes"], dict):
                cat["total_articles"] = sum(v.get("count", 0) for v in cat["codes"].values())
            cat_path.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"oversized entries: {len(entries)}")


if __name__ == "__main__":
    main()
