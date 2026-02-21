#!/usr/bin/env python3
"""jplawdb2 builder - e-Gov XML -> text/{code}/{id}.txt

Usage:
    python3 tools/build.py                  # Build all laws in laws.json
    python3 tools/build.py --phase 1        # Build only Phase 1 laws
    python3 tools/build.py --code sochi     # Build a single law by code
    python3 tools/build.py --dry-run        # Show what would be built
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    from lxml import etree

    USING_LXML = True
except ImportError:
    import xml.etree.ElementTree as etree

    USING_LXML = False

BASE_DIR = Path(__file__).parent.parent
LAWS_JSON = BASE_DIR / "laws.json"
TEXT_DIR = BASE_DIR / "text"
META_DIR = BASE_DIR / "meta"

# Namespace used by e-Gov XML
EGOV_NS = {"": "http://law.e-gov.go.jp/xmlschema/lawdata"}


def strip_ns(tag: str) -> str:
    """Remove namespace prefix from an XML tag."""
    return re.sub(r"\{[^}]+\}", "", tag)


def iter_elements(root, tag_local: str):
    """Find elements by local name, namespace-agnostic."""
    for el in root.iter():
        if strip_ns(el.tag) == tag_local:
            yield el


def get_text_recursive(el) -> str:
    """Extract all text content from an element, recursively."""
    if el is None:
        return ""
    parts = []
    if el.text:
        parts.append(el.text)
    for child in el:
        parts.append(get_text_recursive(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def find_child(el, tag_local: str):
    """Find the first direct child with the given local tag name."""
    for child in el:
        if strip_ns(child.tag) == tag_local:
            return child
    return None


def find_children(el, tag_local: str):
    """Find all direct children with the given local tag name."""
    return [child for child in el if strip_ns(child.tag) == tag_local]


def extract_article_title(article_el, title_overrides: dict, parent_sections: list) -> str:
    """Extract the title for an Article element.

    Priority:
    1. <ArticleCaption> if present
    2. title_overrides from laws.json
    3. Nearest parent section name
    4. Empty string
    """
    # 1. ArticleCaption
    caption = find_child(article_el, "ArticleCaption")
    if caption is not None:
        text = get_text_recursive(caption).strip()
        if text:
            return text

    # 2. title_overrides
    num = article_el.get("Num", "")
    if num in title_overrides:
        return title_overrides[num]

    # 3. Parent section name (nearest)
    if parent_sections:
        return parent_sections[-1]

    return ""


def article_to_text(article_el) -> str:
    """Convert an Article element to readable plain text."""
    lines = []

    # ArticleTitle (e.g. "第六十六条の六")
    article_title = find_child(article_el, "ArticleTitle")
    if article_title is not None:
        lines.append(get_text_recursive(article_title).strip())

    # ArticleCaption (e.g. "内国法人に係る特定外国子会社等の課税の特例")
    caption = find_child(article_el, "ArticleCaption")
    if caption is not None:
        cap_text = get_text_recursive(caption).strip()
        if cap_text:
            lines.append(cap_text)

    if lines:
        lines.append("")

    # Paragraphs
    for para in find_children(article_el, "Paragraph"):
        para_num = find_child(para, "ParagraphNum")
        para_sent = find_child(para, "ParagraphSentence")

        para_text_parts = []
        if para_num is not None:
            num_text = get_text_recursive(para_num).strip()
            if num_text:
                para_text_parts.append(num_text)
        if para_sent is not None:
            sent_text = get_text_recursive(para_sent).strip()
            if sent_text:
                para_text_parts.append(sent_text)

        if para_text_parts:
            lines.append(" ".join(para_text_parts))

        # Items within a paragraph
        for item in find_children(para, "Item"):
            item_title = find_child(item, "ItemTitle")
            item_sent = find_child(item, "ItemSentence")

            item_parts = []
            if item_title is not None:
                t = get_text_recursive(item_title).strip()
                if t:
                    item_parts.append(t)
            if item_sent is not None:
                t = get_text_recursive(item_sent).strip()
                if t:
                    item_parts.append(t)

            if item_parts:
                lines.append("  " + " ".join(item_parts))

            # Sub-items
            for subitem in find_children(item, "Subitem1"):
                sub_title = find_child(subitem, "Subitem1Title")
                sub_sent = find_child(subitem, "Subitem1Sentence")
                sub_parts = []
                if sub_title is not None:
                    t = get_text_recursive(sub_title).strip()
                    if t:
                        sub_parts.append(t)
                if sub_sent is not None:
                    t = get_text_recursive(sub_sent).strip()
                    if t:
                        sub_parts.append(t)
                if sub_parts:
                    lines.append("    " + " ".join(sub_parts))

                # Sub-sub-items
                for subitem2 in find_children(subitem, "Subitem2"):
                    s2_title = find_child(subitem2, "Subitem2Title")
                    s2_sent = find_child(subitem2, "Subitem2Sentence")
                    s2_parts = []
                    if s2_title is not None:
                        t = get_text_recursive(s2_title).strip()
                        if t:
                            s2_parts.append(t)
                    if s2_sent is not None:
                        t = get_text_recursive(s2_sent).strip()
                        if t:
                            s2_parts.append(t)
                    if s2_parts:
                        lines.append("      " + " ".join(s2_parts))

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def make_yaml_front_matter(code: str, article_id: str, title: str,
                           cite_key: str, law_num: str, last_amended: str,
                           status: str = "current") -> str:
    """Generate YAML front matter block."""
    lines = [
        "---",
        "schema_version: 1",
        f"code: {code}",
        f"article_id: {article_id}",
        f"title: {title}",
        f"cite_key: {cite_key}",
        f"law_num: {law_num}",
        f'last_amended: "{last_amended}"',
        f"status: {status}",
        "---",
    ]
    return "\n".join(lines) + "\n"


def make_cite_key(code: str, article_id: str, cite_prefix: str) -> str:
    """Build cite_key from code and article_id.

    Examples:
        ("sochi", "66_6", "措法") -> "措法66の6"
        ("hojin", "22_2", "法法") -> "法法22の2"
        ("hojin-kihon", "2-1-1", "法基通") -> "法基通2-1-1"
    """
    # For tsutatsu (contains "-" in id), keep dashes as-is
    if "-" in article_id:
        return f"{cite_prefix}{article_id}"
    # For regular laws, convert underscores back to "の"
    display_id = article_id.replace("_", "の")
    return f"{cite_prefix}{display_id}"


def collect_section_names(main_prov) -> dict:
    """Build a map of Article Num -> list of parent section names."""
    section_map = {}
    section_tags = {"Part", "Chapter", "Section", "Subsection", "Division"}

    def walk(el, parents: list):
        local_tag = strip_ns(el.tag)

        if local_tag in section_tags:
            title_el = find_child(el, f"{local_tag}Title")
            name = get_text_recursive(title_el).strip() if title_el is not None else ""
            new_parents = parents + [name] if name else parents
            for child in el:
                walk(child, new_parents)
        elif local_tag == "Article":
            num = el.get("Num", "")
            if num:
                section_map[num] = list(parents)
            # Don't recurse into Article children
        else:
            for child in el:
                walk(child, parents)

    for child in main_prov:
        walk(child, [])

    return section_map


def build_law(code: str, law_cfg: dict, dry_run: bool = False) -> dict:
    """Build text files for a single law.

    Returns a dict with build statistics:
        {"code": str, "count": int, "articles": [{"id": str, "title": str, "size": int}, ...]}
    """
    xml_path = BASE_DIR / law_cfg["xml"]
    if not xml_path.exists():
        print(f"  WARNING: XML not found: {xml_path}", file=sys.stderr)
        return {"code": code, "count": 0, "articles": [], "error": f"XML not found: {xml_path}"}

    cite_prefix = law_cfg.get("cite_prefix", code)
    law_num = law_cfg.get("law_num", "")
    last_amended = law_cfg.get("last_amended", "")
    title_overrides = law_cfg.get("title_overrides", {})

    # Parse XML
    try:
        tree = etree.parse(str(xml_path))
        root = tree.getroot()
    except Exception as e:
        print(f"  ERROR: Failed to parse {xml_path}: {e}", file=sys.stderr)
        return {"code": code, "count": 0, "articles": [], "error": str(e)}

    # Find MainProvision
    main_prov = None
    for el in iter_elements(root, "MainProvision"):
        main_prov = el
        break

    if main_prov is None:
        print(f"  WARNING: No MainProvision found in {xml_path}", file=sys.stderr)
        return {"code": code, "count": 0, "articles": [], "error": "No MainProvision"}

    # Collect parent section names for title fallback
    section_map = collect_section_names(main_prov)

    # Output dir
    out_dir = TEXT_DIR / code
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    articles = []
    seen_nums = set()

    for article_el in iter_elements(main_prov, "Article"):
        num = article_el.get("Num", "")
        if not num:
            continue

        # Skip duplicates (keep first)
        if num in seen_nums:
            print(f"  WARNING: Duplicate Num='{num}' in {code}, skipping", file=sys.stderr)
            continue
        seen_nums.add(num)

        parent_sections = section_map.get(num, [])
        title = extract_article_title(article_el, title_overrides, parent_sections)
        cite_key = make_cite_key(code, num, cite_prefix)

        # Generate content
        body_text = article_to_text(article_el)
        front_matter = make_yaml_front_matter(
            code=code,
            article_id=num,
            title=title,
            cite_key=cite_key,
            law_num=law_num,
            last_amended=last_amended,
        )
        full_content = front_matter + body_text

        file_path = out_dir / f"{num}.txt"
        file_size = len(full_content.encode("utf-8"))

        if not dry_run:
            file_path.write_text(full_content, encoding="utf-8")

        articles.append({
            "id": num,
            "title": title,
            "cite_key": cite_key,
            "size": file_size,
        })

    result = {"code": code, "count": len(articles), "articles": articles}

    # Write meta/{code}.json
    if not dry_run and articles:
        META_DIR.mkdir(parents=True, exist_ok=True)
        meta_path = META_DIR / f"{code}.json"
        meta_data = {
            "code": code,
            "cite_prefix": cite_prefix,
            "law_num": law_num,
            "last_amended": last_amended,
            "count": len(articles),
            "articles": [
                {"id": a["id"], "title": a["title"], "cite_key": a["cite_key"], "size": a["size"]}
                for a in articles
            ],
        }
        meta_path.write_text(
            json.dumps(meta_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    return result


def update_catalog(results: list, dry_run: bool = False):
    """Update meta/catalog.json with build results."""
    if dry_run:
        return

    META_DIR.mkdir(parents=True, exist_ok=True)
    catalog_path = META_DIR / "catalog.json"

    # Load existing catalog if present
    catalog = {}
    if catalog_path.exists():
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            catalog = {}

    # Update entries
    laws = catalog.get("laws", {})
    for r in results:
        if r.get("error"):
            continue
        laws[r["code"]] = {
            "count": r["count"],
            "meta": f"meta/{r['code']}.json",
            "text_dir": f"text/{r['code']}/",
        }

    catalog["laws"] = laws
    catalog["total_articles"] = sum(v["count"] for v in laws.values())
    catalog["last_built"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    catalog["schema_version"] = 1

    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser(description="Build jplawdb2 text files from e-Gov XML")
    parser.add_argument("--phase", type=int, help="Build only laws in this phase")
    parser.add_argument("--code", type=str, help="Build a single law by code")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be built without writing files")
    args = parser.parse_args()

    if not LAWS_JSON.exists():
        print(f"ERROR: {LAWS_JSON} not found", file=sys.stderr)
        sys.exit(1)

    laws = json.loads(LAWS_JSON.read_text(encoding="utf-8"))

    # Filter
    targets = {}
    for code, cfg in laws.items():
        if args.code and code != args.code:
            continue
        if args.phase is not None and cfg.get("phase", 1) != args.phase:
            continue
        targets[code] = cfg

    if not targets:
        print("No laws matched the given filters.", file=sys.stderr)
        sys.exit(1)

    print(f"Building {len(targets)} law(s)..." + (" [DRY RUN]" if args.dry_run else ""))
    print()

    results = []
    for code, cfg in targets.items():
        print(f"  [{code}] {cfg.get('cite_prefix', code)} ...", end=" ", flush=True)
        result = build_law(code, cfg, dry_run=args.dry_run)
        if result.get("error"):
            print(f"ERROR: {result['error']}")
        else:
            print(f"{result['count']} articles")
        results.append(result)

    # Update catalog
    update_catalog(results, dry_run=args.dry_run)

    # Summary
    total = sum(r["count"] for r in results)
    errors = sum(1 for r in results if r.get("error"))
    print()
    print(f"Done: {total} articles from {len(results) - errors} law(s)")
    if errors:
        print(f"  ({errors} law(s) had errors)")


if __name__ == "__main__":
    main()
