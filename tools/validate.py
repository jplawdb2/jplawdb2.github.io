#!/usr/bin/env python3
"""jplawdb2 validator - check consistency of generated files.

Usage:
    python3 tools/validate.py              # Validate all
    python3 tools/validate.py --code sochi # Validate single law
"""

import argparse
import json
import re
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
TEXT_DIR = BASE_DIR / "text"
META_DIR = BASE_DIR / "meta"

REQUIRED_YAML_FIELDS = [
    "schema_version",
    "code",
    "article_id",
    "title",
    "cite_key",
    "law_num",
    "last_amended",
    "status",
]

CITE_KEY_PATTERN = re.compile(
    r"^[^\d]+"          # prefix (e.g. 措法, 法法, 法基通)
    r"[\d_\-の]+$"      # article part (digits, underscores, hyphens, の)
)


def parse_yaml_front_matter(text: str) -> dict:
    """Parse YAML front matter from text content.

    Returns dict of key-value pairs, or empty dict if no front matter found.
    """
    if not text.startswith("---\n"):
        return {}

    end = text.find("\n---\n", 4)
    if end == -1:
        return {}

    yaml_block = text[4:end]
    result = {}
    for line in yaml_block.split("\n"):
        line = line.strip()
        if not line:
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            result[key] = value

    return result


def is_chunk_file(file_path: Path) -> bool:
    """チャンクファイル ({id}__cN.txt) かどうかを判定"""
    return "__c" in file_path.stem


def validate_chunk_file(file_path: Path, expected_code: str) -> list:
    """チャンクファイル専用バリデーション"""
    errors = []
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{file_path}: Cannot read file: {e}"]

    yaml = parse_yaml_front_matter(content)
    if not yaml:
        return [f"{file_path}: No YAML front matter found"]

    for field in ["code", "article_id", "chunk_index", "chunk_total", "parent"]:
        if field not in yaml:
            errors.append(f"{file_path}: Missing chunk YAML field '{field}'")

    if "code" in yaml and yaml["code"] != expected_code:
        errors.append(f"{file_path}: code='{yaml['code']}' does not match directory '{expected_code}'")

    return errors


def validate_text_file(file_path: Path, expected_code: str) -> list:
    """Validate a single text file. Returns list of error strings."""
    # チャンクファイルは専用バリデーション
    if is_chunk_file(file_path):
        return validate_chunk_file(file_path, expected_code)

    errors = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return [f"{file_path}: Cannot read file: {e}"]

    if not content.strip():
        return [f"{file_path}: File is empty"]

    # Check YAML front matter
    yaml = parse_yaml_front_matter(content)
    if not yaml:
        errors.append(f"{file_path}: No YAML front matter found")
        return errors

    # Required fields
    for field in REQUIRED_YAML_FIELDS:
        if field not in yaml:
            errors.append(f"{file_path}: Missing YAML field '{field}'")

    # code must match directory
    if "code" in yaml and yaml["code"] != expected_code:
        errors.append(
            f"{file_path}: code='{yaml['code']}' does not match directory '{expected_code}'"
        )

    # article_id must match filename
    expected_id = file_path.stem
    if "article_id" in yaml and yaml["article_id"] != expected_id:
        errors.append(
            f"{file_path}: article_id='{yaml['article_id']}' does not match filename '{expected_id}'"
        )

    # cite_key format check
    if "cite_key" in yaml:
        ck = yaml["cite_key"]
        if not CITE_KEY_PATTERN.match(ck):
            errors.append(f"{file_path}: cite_key '{ck}' has invalid format")

    # schema_version
    if "schema_version" in yaml and yaml["schema_version"] != "1":
        errors.append(f"{file_path}: Unexpected schema_version '{yaml['schema_version']}'")

    return errors


def validate_meta_file(code: str) -> list:
    """Validate meta/{code}.json against text/{code}/ files."""
    errors = []

    meta_path = META_DIR / f"{code}.json"
    text_dir = TEXT_DIR / code

    if not meta_path.exists():
        errors.append(f"meta/{code}.json: File does not exist")
        return errors

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        errors.append(f"meta/{code}.json: Cannot parse: {e}")
        return errors

    # Check meta has required keys
    for key in ["code", "count", "articles"]:
        if key not in meta:
            errors.append(f"meta/{code}.json: Missing key '{key}'")

    if meta.get("code") != code:
        errors.append(f"meta/{code}.json: code='{meta.get('code')}' does not match '{code}'")

    # Cross-check: meta article IDs vs actual text files
    meta_ids = set()
    if "articles" in meta:
        for a in meta["articles"]:
            aid = a.get("id", "")
            if aid:
                meta_ids.add(aid)

    if text_dir.exists():
        # チャンクファイル (__cN.txt) は除外
        file_ids = {f.stem for f in text_dir.glob("*.txt") if "__c" not in f.stem}
    else:
        file_ids = set()

    # IDs in meta but no file
    for mid in sorted(meta_ids - file_ids):
        errors.append(f"meta/{code}.json: article '{mid}' listed but text/{code}/{mid}.txt missing")

    # Files exist but not in meta
    for fid in sorted(file_ids - meta_ids):
        errors.append(f"text/{code}/{fid}.txt: exists but not listed in meta/{code}.json")

    # Count check
    if "count" in meta and meta["count"] != len(meta.get("articles", [])):
        errors.append(
            f"meta/{code}.json: count={meta['count']} but {len(meta.get('articles', []))} articles listed"
        )

    return errors


def validate_catalog() -> list:
    """Validate meta/catalog.json against actual file counts."""
    errors = []

    catalog_path = META_DIR / "catalog.json"
    if not catalog_path.exists():
        errors.append("meta/catalog.json: File does not exist")
        return errors

    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        errors.append(f"meta/catalog.json: Cannot parse: {e}")
        return errors

    laws = catalog.get("laws", {})
    for code, info in laws.items():
        expected_count = info.get("count", 0)
        text_dir = TEXT_DIR / code
        if text_dir.exists():
            # チャンクファイル (__cN.txt) は除外して記事数のみカウント
            actual_count = sum(1 for f in text_dir.glob("*.txt") if "__c" not in f.stem)
        else:
            actual_count = 0

        if expected_count != actual_count:
            errors.append(
                f"meta/catalog.json: {code} count={expected_count} but {actual_count} files exist"
            )

    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate jplawdb2 generated files")
    parser.add_argument("--code", type=str, help="Validate only this law code")
    args = parser.parse_args()

    all_errors = []

    # Determine which codes to validate
    if args.code:
        codes = [args.code]
    else:
        codes = []
        if TEXT_DIR.exists():
            codes = sorted(d.name for d in TEXT_DIR.iterdir() if d.is_dir())

    print(f"Validating {len(codes)} law(s)...")
    print()

    for code in codes:
        text_dir = TEXT_DIR / code
        if not text_dir.exists():
            all_errors.append(f"text/{code}/: Directory does not exist")
            continue

        txt_files = sorted(text_dir.glob("*.txt"))
        print(f"  [{code}] {len(txt_files)} files ...", end=" ", flush=True)

        code_errors = []
        for tf in txt_files:
            code_errors.extend(validate_text_file(tf, code))

        code_errors.extend(validate_meta_file(code))

        if code_errors:
            print(f"{len(code_errors)} error(s)")
            all_errors.extend(code_errors)
        else:
            print("OK")

    # Catalog validation
    print()
    print("  [catalog] ...", end=" ", flush=True)
    catalog_errors = validate_catalog()
    if catalog_errors:
        print(f"{len(catalog_errors)} error(s)")
        all_errors.extend(catalog_errors)
    else:
        print("OK")

    # Summary
    print()
    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s) found:")
        print()
        for err in all_errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("PASSED: All checks passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
