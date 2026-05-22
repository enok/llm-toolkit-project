#!/usr/bin/env python3
"""Validate a PDF: size, pages, text length, required and forbidden phrases."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path, help="Path to PDF")
    ap.add_argument("--min-bytes", type=int, default=0)
    ap.add_argument("--min-pages", type=int, default=1)
    ap.add_argument("--min-text-chars", type=int, default=0)
    ap.add_argument(
        "--must-contain",
        nargs="*",
        default=[],
        help="Each phrase must appear in extracted text (after lowercasing + collapsing whitespace)",
    )
    ap.add_argument(
        "--must-not-contain",
        nargs="*",
        default=[],
        help="Each phrase must be absent from extracted text (after lowercasing + collapsing whitespace)",
    )
    args = ap.parse_args()

    path: Path = args.pdf
    if not path.is_file():
        print(f"ERROR: not a file: {path}", file=sys.stderr)
        return 1

    size = path.stat().st_size
    if size < args.min_bytes:
        print(f"ERROR: size {size} < --min-bytes {args.min_bytes}: {path.name}", file=sys.stderr)
        return 1

    try:
        from pypdf import PdfReader
    except ImportError:
        print("ERROR: install pypdf (pip install -r scripts/pdf-verify-requirements.txt)", file=sys.stderr)
        return 2

    reader = PdfReader(str(path))
    n_pages = len(reader.pages)
    if n_pages < args.min_pages:
        print(
            f"ERROR: pages {n_pages} < --min-pages {args.min_pages}: {path.name}",
            file=sys.stderr,
        )
        return 1

    parts = []
    for pg in reader.pages:
        try:
            parts.append(pg.extract_text() or "")
        except Exception as e:  # noqa: BLE001
            print(f"WARN: extract_text failed on a page: {e}", file=sys.stderr)
    text = "".join(parts)
    stripped = text.strip()
    if len(stripped) < args.min_text_chars:
        print(
            f"ERROR: extracted text chars {len(stripped)} < --min-text-chars {args.min_text_chars}: {path.name}",
            file=sys.stderr,
        )
        return 1

    tn = norm(text)
    for needle in args.must_contain:
        nn = norm(needle)
        if nn and nn not in tn:
            print(f"ERROR: missing required phrase {needle!r} in {path.name}", file=sys.stderr)
            return 1
    for needle in args.must_not_contain:
        nn = norm(needle)
        if nn and nn in tn:
            print(f"ERROR: forbidden phrase {needle!r} found in {path.name}", file=sys.stderr)
            return 1

    print(f"OK {path.name}  {size} bytes  {n_pages} pages  {len(stripped)} text chars")
    return 0


if __name__ == "__main__":
    sys.exit(main())
