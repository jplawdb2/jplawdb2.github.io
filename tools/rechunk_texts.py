#!/usr/bin/env python3
"""Re-chunk long text files so each chunk stays under a token cap.

Default behavior in this repository:
- Tokenizer: o200k_base
- Hard cap: 9500 tokens (including YAML front matter)
- Prefer [pN] paragraph markers when available
- Otherwise split by heading/section boundaries, then by token window if needed
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


try:
    import tiktoken
except ImportError as e:  # pragma: no cover
    raise SystemExit(
        "ERROR: tiktoken is required. Install with: pip install tiktoken"
    ) from e


ENC = tiktoken.get_encoding("o200k_base")

BASE_DIR = Path(__file__).parent.parent
TEXT_DIR = BASE_DIR / "text"

# Focused headings that are common in Q&A / handbook style files.
HEADING_KEYWORDS = {
    "目次",
    "概要",
    "対象税目",
    "根拠法令等",
    "関連リンク",
    "関連コード",
    "お問い合わせ先",
    "法令等",
    "質疑応答事例",
    "照会要旨",
    "回答要旨",
    "具体例",
    "参考",
    "別表",
    "別紙",
}


@dataclass
class Unit:
    text: str
    p_start: str | None = None
    p_end: str | None = None
    heading: str | None = None


def token_len(s: str) -> int:
    return len(ENC.encode(s))


def parse_front_matter(content: str) -> tuple[list[str], str]:
    if not content.startswith("---\n"):
        raise ValueError("File does not start with YAML front matter")
    end = content.find("\n---\n", 4)
    if end == -1:
        raise ValueError("Closing YAML marker not found")
    yaml_block = content[4:end]
    body = content[end + 5 :]
    return yaml_block.splitlines(), body


def yaml_to_dict(yaml_lines: Iterable[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in yaml_lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip().strip('"').strip("'")
    return out


def rebuild_parent_yaml(yaml_lines: list[str], token_estimate: int, chunks: int) -> str:
    kept: list[str] = []
    for ln in yaml_lines:
        if re.match(r"^token_estimate:\s*", ln):
            continue
        if re.match(r"^chunks:\s*", ln):
            continue
        kept.append(ln)
    kept.append(f"token_estimate: {token_estimate}")
    kept.append(f"chunks: {chunks}")
    return "---\n" + "\n".join(kept) + "\n---\n"


def detect_heading(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("#"):
        return True
    if re.match(r"^【[^】]{1,60}】$", s):
        return True
    if re.match(r"^第[一二三四五六七八九十百千0-9０-９]+[編章節款目].*", s):
        return True
    if s in HEADING_KEYWORDS:
        return True
    if any(s.startswith(k) for k in HEADING_KEYWORDS):
        return True
    if re.match(r"^##\s+.*\[part\s+\d+/\d+\]", s, flags=re.IGNORECASE):
        return True
    return False


def units_from_paragraph_markers(body: str) -> list[Unit]:
    # Split at top-level paragraph markers [pN] (not [pN-iM]).
    matches = list(re.finditer(r"(?m)^\[p(\d+)\]", body))
    if not matches:
        return []

    units: list[Unit] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        segment = body[start:end]
        p_num = m.group(1)
        units.append(Unit(text=segment, p_start=f"p{p_num}", p_end=f"p{p_num}"))
    return units


def units_from_headings(body: str) -> list[Unit]:
    lines = body.splitlines(keepends=True)
    if not lines:
        return []

    heading_idx: list[int] = []
    heading_labels: list[str] = []
    for i, ln in enumerate(lines):
        if detect_heading(ln):
            heading_idx.append(i)
            heading_labels.append(ln.strip()[:120])

    units: list[Unit] = []
    if heading_idx:
        # Prefix before first heading (if non-empty) becomes one unit.
        if heading_idx[0] > 0:
            prefix = "".join(lines[: heading_idx[0]])
            if prefix.strip():
                units.append(Unit(text=prefix, heading="(preface)"))

        for pos, idx in enumerate(heading_idx):
            nxt = heading_idx[pos + 1] if pos + 1 < len(heading_idx) else len(lines)
            segment = "".join(lines[idx:nxt])
            units.append(Unit(text=segment, heading=heading_labels[pos]))
        return [u for u in units if u.text.strip()]

    # Fallback: blank-line paragraphs.
    cur: list[str] = []
    for ln in lines:
        if ln.strip() == "":
            if cur:
                cur.append(ln)
                segment = "".join(cur)
                if segment.strip():
                    units.append(Unit(text=segment))
                cur = []
            continue
        cur.append(ln)
    if cur:
        segment = "".join(cur)
        if segment.strip():
            units.append(Unit(text=segment))

    if units:
        return units

    # Last resort: whole body as one unit.
    return [Unit(text=body)] if body.strip() else []


def split_large_text(text: str, cap_tokens: int) -> list[str]:
    """Hard fallback when a single unit still exceeds cap."""
    if token_len(text) <= cap_tokens:
        return [text]

    # Token-window split with light boundary preference.
    toks = ENC.encode(text)
    out: list[str] = []
    start = 0
    while start < len(toks):
        end = min(start + cap_tokens, len(toks))
        chunk_text = ENC.decode(toks[start:end])

        # Prefer a nearby semantic boundary when possible.
        if end < len(toks):
            cut = max(chunk_text.rfind("\n"), chunk_text.rfind("。"))
            # Avoid pathological tiny segments.
            if cut >= max(100, len(chunk_text) // 3):
                chunk_text = chunk_text[: cut + 1]
                used = len(ENC.encode(chunk_text))
                end = start + used

        out.append(chunk_text)
        start = end

    return [c for c in out if c]


def chunk_units(units: list[Unit], cap_tokens: int, yaml_overhead_tokens: int) -> list[list[Unit]]:
    allowed = cap_tokens - yaml_overhead_tokens
    if allowed < 500:
        raise ValueError("Cap too small after YAML overhead")

    chunks: list[list[Unit]] = []
    cur: list[Unit] = []

    def unit_tokens(u: Unit) -> int:
        return token_len(u.text)

    cur_tokens = 0
    for u in units:
        ut = unit_tokens(u)
        if ut > allowed:
            # Flush current chunk first.
            if cur:
                chunks.append(cur)
                cur = []
                cur_tokens = 0

            parts = split_large_text(u.text, allowed)
            for i, part in enumerate(parts):
                p_unit = Unit(text=part, p_start=u.p_start if i == 0 else None,
                              p_end=u.p_end if i == len(parts) - 1 else None,
                              heading=u.heading)
                pt = token_len(part)
                if pt > allowed:
                    raise ValueError("Internal split failed to satisfy cap")
                chunks.append([p_unit])
            continue

        if cur and cur_tokens + ut > allowed:
            chunks.append(cur)
            cur = [u]
            cur_tokens = ut
        else:
            cur.append(u)
            cur_tokens += ut

    if cur:
        chunks.append(cur)

    return chunks


def para_range_for_chunk(units: list[Unit]) -> str | None:
    p_starts = [u.p_start for u in units if u.p_start]
    p_ends = [u.p_end for u in units if u.p_end]
    if not p_starts or not p_ends:
        return None
    first = p_starts[0]
    last = p_ends[-1]
    return first if first == last else f"{first}-{last}"


def section_range_for_chunk(units: list[Unit], idx: int) -> str | None:
    headings = [u.heading for u in units if u.heading]
    if not headings:
        return f"chunk-{idx}"
    first = headings[0]
    last = headings[-1]
    if first == last:
        return first
    return f"{first} -> {last}"


def _range_start_end(v: str | None) -> tuple[str, str] | None:
    if not v:
        return None
    if "-" in v:
        a, b = v.split("-", 1)
        return a, b
    return v, v


def combine_para_ranges(a: str | None, b: str | None) -> str | None:
    ra = _range_start_end(a)
    rb = _range_start_end(b)
    if not ra and not rb:
        return None
    if not ra:
        return b
    if not rb:
        return a
    start = ra[0]
    end = rb[1]
    return start if start == end else f"{start}-{end}"


def combine_section_ranges(a: str | None, b: str | None) -> str | None:
    if a and b:
        if a == b:
            return a
        return f"{a} -> {b}"
    return a or b


def chunk_yaml(
    code: str,
    article_id: str,
    idx: int,
    total: int,
    parent_rel: str,
    cite_key: str | None,
    para_range: str | None,
    section_range: str | None,
) -> str:
    lines = [
        "---",
        "schema_version: 1",
        f"code: {code}",
        f"article_id: {article_id}",
        f"chunk_index: {idx}",
        f"chunk_total: {total}",
    ]
    if para_range:
        lines.append(f"para_range: {para_range}")
    if section_range and not para_range:
        lines.append(f"section_range: {section_range}")
    lines.append(f"parent: {parent_rel}")
    if cite_key:
        lines.append(f"cite_key: {cite_key}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def remove_existing_chunks(main_path: Path) -> None:
    pattern = f"{main_path.stem}__c*.txt"
    for old in main_path.parent.glob(pattern):
        old.unlink()


def rechunk_one(rel_path: str, cap_tokens: int, dry_run: bool = False) -> dict:
    main_path = TEXT_DIR / rel_path
    if not main_path.exists():
        raise FileNotFoundError(f"Missing target file: {rel_path}")

    content = main_path.read_text(encoding="utf-8")
    yaml_lines, body = parse_front_matter(content)
    y = yaml_to_dict(yaml_lines)

    code = y.get("code") or main_path.parent.name
    article_id = y.get("article_id") or main_path.stem
    cite_key = y.get("cite_key")

    total_tokens = token_len(content)

    p_units = units_from_paragraph_markers(body)
    units = p_units if p_units else units_from_headings(body)
    if not units:
        raise ValueError(f"No body content found: {rel_path}")

    # Conservative YAML overhead estimate for chunk files.
    sample_chunk_yaml = chunk_yaml(
        code=code,
        article_id=article_id,
        idx=1,
        total=9,
        parent_rel=f"text/{code}/{article_id}.txt",
        cite_key=cite_key,
        para_range="p1-p99",
        section_range=None,
    )
    chunk_yaml_overhead = token_len(sample_chunk_yaml)

    groups = chunk_units(units, cap_tokens=cap_tokens, yaml_overhead_tokens=chunk_yaml_overhead)

    # Ensure long files are actually chunked.
    if total_tokens > cap_tokens and len(groups) < 2:
        # Force split by large-text fallback.
        forced = split_large_text(body, cap_tokens - chunk_yaml_overhead)
        groups = [[Unit(text=p)] for p in forced]

    # Build initial chunk records.
    chunk_records: list[dict] = []
    for i, chunk_units_list in enumerate(groups, start=1):
        chunk_records.append(
            {
                "body": "".join(u.text for u in chunk_units_list),
                "para_range": para_range_for_chunk(chunk_units_list),
                "section_range": section_range_for_chunk(chunk_units_list, i),
            }
        )

    # Final cap enforcement: if a chunk still exceeds cap with its real header,
    # split it again with exact per-chunk allowance.
    i = 0
    while i < len(chunk_records):
        rec = chunk_records[i]
        total = len(chunk_records)
        header = chunk_yaml(
            code=code,
            article_id=article_id,
            idx=i + 1,
            total=total,
            parent_rel=f"text/{code}/{article_id}.txt",
            cite_key=cite_key,
            para_range=rec["para_range"],
            section_range=rec["section_range"],
        )
        allowed_body_tokens = cap_tokens - token_len(header)
        if allowed_body_tokens < 200:
            raise ValueError(f"{rel_path}: token cap is too small after YAML overhead")

        if token_len(rec["body"]) <= allowed_body_tokens:
            i += 1
            continue

        parts = split_large_text(rec["body"], allowed_body_tokens)
        if len(parts) <= 1:
            raise ValueError(
                f"{rel_path}: cannot split chunk {i + 1} below cap={cap_tokens}"
            )

        replacement = []
        for pi, part in enumerate(parts, start=1):
            replacement.append(
                {
                    "body": part,
                    "para_range": None,  # split fallback may cut ranges; avoid false metadata
                    "section_range": None,
                }
            )
        chunk_records[i : i + 1] = replacement
        # Re-check at the same index with updated total.

    # Merge tiny adjacent chunks when the merged result still satisfies the cap.
    changed = True
    while changed:
        changed = False
        i = 0
        while i < len(chunk_records) - 1:
            a = chunk_records[i]
            b = chunk_records[i + 1]
            merged_body = a["body"] + b["body"]
            merged_para = combine_para_ranges(a.get("para_range"), b.get("para_range"))
            merged_sec = combine_section_ranges(a.get("section_range"), b.get("section_range"))
            merged_total = len(chunk_records) - 1
            header = chunk_yaml(
                code=code,
                article_id=article_id,
                idx=i + 1,
                total=merged_total,
                parent_rel=f"text/{code}/{article_id}.txt",
                cite_key=cite_key,
                para_range=merged_para,
                section_range=merged_sec,
            )
            if token_len(header + merged_body) <= cap_tokens:
                chunk_records[i] = {
                    "body": merged_body,
                    "para_range": merged_para,
                    "section_range": merged_sec,
                }
                del chunk_records[i + 1]
                changed = True
            else:
                i += 1

    chunk_total = len(chunk_records)
    if chunk_total < 2:
        raise ValueError(
            f"{rel_path}: chunking produced {chunk_total} chunk(s); expected >=2 for long file"
        )

    parent_yaml = rebuild_parent_yaml(yaml_lines, token_estimate=total_tokens, chunks=chunk_total)
    parent_text = parent_yaml + body

    chunk_payloads: list[tuple[Path, str, int]] = []
    for i, rec in enumerate(chunk_records, start=1):
        header = chunk_yaml(
            code=code,
            article_id=article_id,
            idx=i,
            total=chunk_total,
            parent_rel=f"text/{code}/{article_id}.txt",
            cite_key=cite_key,
            para_range=rec["para_range"],
            section_range=rec["section_range"],
        )
        full = header + rec["body"]
        tok = token_len(full)
        if tok > cap_tokens:
            raise ValueError(
                f"{rel_path}: generated chunk {i} has {tok} tokens (> {cap_tokens})"
            )
        out = main_path.parent / f"{main_path.stem}__c{i}.txt"
        chunk_payloads.append((out, full, tok))

    if not dry_run:
        remove_existing_chunks(main_path)
        main_path.write_text(parent_text, encoding="utf-8")
        for out, full, _ in chunk_payloads:
            out.write_text(full, encoding="utf-8")

    return {
        "file": rel_path,
        "tokens": total_tokens,
        "chunks": chunk_total,
        "chunk_tokens": [t for _, _, t in chunk_payloads],
        "mode": "paragraph" if p_units else "heading",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Rechunk target text files by token cap")
    parser.add_argument("targets", nargs="+", help="text-relative paths, e.g. qa-taxanswer/2732.txt")
    parser.add_argument("--cap", type=int, default=9500, help="Token cap per URL file (default: 9500)")
    parser.add_argument("--dry-run", action="store_true", help="Analyze only, do not write files")
    args = parser.parse_args()

    for rel in args.targets:
        result = rechunk_one(rel, cap_tokens=args.cap, dry_run=args.dry_run)
        chunks = ", ".join(str(x) for x in result["chunk_tokens"])
        print(
            f"[OK] {result['file']} tokens={result['tokens']} mode={result['mode']} "
            f"chunks={result['chunks']} chunk_tokens=[{chunks}]"
        )


if __name__ == "__main__":
    main()
