#!/usr/bin/env python3
"""Merge one session's sections into the shared ledger files without touching other sessions.

`TASKS_TABLE.md` and `CONTEXT_STATE.md` hold one `## Session: <name>` section per
session and are edited by several sessions over time. A session that rewrites the
whole file can silently drop the others' notes. This script is the safe write path:

* Each section in a part file is matched to the ledger by its exact `## Session: <name>`
  header line (any session name; no prefix is assumed). A match is replaced in place
  (from its header up to the next `## Session:` header); no match is appended after a
  `---` separator. Every other section is left byte-for-byte as it was.
* Only the timestamp of a leading `Last updated: YYYY-MM-DD[ HH:MM]` line is refreshed
  (to `--stamp`); the rest of that line is kept.
* The section count must not go down. If it does, nothing is written and the exit code is 1.
* Every target is validated before any file is written (all or nothing), and writes are atomic.

Usage (Python 3, standard library only):

    python scripts/ledger_merge_sections.py --root <dir> --stamp "YYYY-MM-DD HH:MM" \
        --merge TASKS_TABLE.md=<part.md> [--merge CONTEXT_STATE.md=<part.md>]...

Exit codes: 0 merged, 1 safety assertion failed (section count dropped), 2 usage error or unreadable input.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import tempfile
from pathlib import Path

HEADER_RE = re.compile(r"(?m)^(?=## Session: )")
HEADER_LINE_RE = re.compile(r"^## Session: [^\r\n]*")
STAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}$")
LAST_UPDATED_RE = re.compile(r"(?m)^(Last updated: )\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2})?")
SEPARATOR_TAIL_RE = re.compile(r"(?:\r?\n)---[ \t]*(?:\r?\n)+$")


def split_sections(text: str) -> tuple[str, list[str]]:
    parts = HEADER_RE.split(text)
    return parts[0], parts[1:]


def header_of(section: str) -> str:
    match = HEADER_LINE_RE.match(section)
    return match.group(0).strip() if match else ""


def normalise_newlines(text: str, newline: str) -> str:
    return text.replace("\r\n", "\n").replace("\n", newline)


def merge_text(ledger: str, part: str, stamp: str) -> tuple[str, int, int]:
    """Return (merged text, sections before, sections after)."""
    newline = "\r\n" if "\r\n" in ledger else "\n"
    header, sections = split_sections(ledger)
    before = len(sections)
    _, new_sections = split_sections(normalise_newlines(part, newline))
    if not new_sections:
        raise ValueError("part file has no '## Session: ' section")
    for new in new_sections:
        new = new.rstrip() + newline
        name = header_of(new)
        index = next((i for i, old in enumerate(sections) if header_of(old) == name), None)
        if index is None:
            if sections:
                last = sections[-1]
                if not SEPARATOR_TAIL_RE.search(last):
                    sections[-1] = last.rstrip() + newline + newline + "---" + newline + newline
            elif header and not header.endswith(newline * 2):
                header = header.rstrip() + newline + newline
            sections.append(new + newline)
        else:
            tail = SEPARATOR_TAIL_RE.search(sections[index])
            sections[index] = new + newline + (("---" + newline + newline) if tail else "")
    merged = header + "".join(sections)
    merged = LAST_UPDATED_RE.sub(lambda m: m.group(1) + stamp, merged, count=1)
    return merged, before, len(sections)


def write_atomic(path: Path, text: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge session sections into ledger files, keeping other sessions intact.")
    parser.add_argument("--root", required=True, type=Path, help="Directory holding the ledger files")
    parser.add_argument("--stamp", required=True, help='Timestamp for the "Last updated:" line, YYYY-MM-DD HH:MM')
    parser.add_argument("--merge", action="append", default=[], metavar="TARGET=PART",
                        help="Ledger file name (relative to --root) and the part file holding this session's section(s); repeatable")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not STAMP_RE.match(args.stamp):
        print(f"error: --stamp must look like 'YYYY-MM-DD HH:MM', got {args.stamp!r}", file=sys.stderr)
        return 2
    if not args.merge:
        print("error: at least one --merge TARGET=PART is required", file=sys.stderr)
        return 2
    if not args.root.is_dir():
        print(f"error: --root is not a directory: {args.root}", file=sys.stderr)
        return 2
    results: list[tuple[Path, str, int, int]] = []
    for spec in args.merge:
        target, sep, part_name = spec.partition("=")
        if not sep or not target or not part_name:
            print(f"error: --merge expects TARGET=PART, got {spec!r}", file=sys.stderr)
            return 2
        path = args.root / target
        try:
            with path.open("r", encoding="utf-8", newline="") as handle:
                ledger = handle.read()
            with Path(part_name).open("r", encoding="utf-8", newline="") as handle:
                part = handle.read()
            merged, before, after = merge_text(ledger, part, args.stamp)
        except (OSError, UnicodeDecodeError, ValueError) as exc:
            print(f"error: {target}: {exc}", file=sys.stderr)
            return 2
        if after < before:
            print(f"error: {target}: section count dropped {before} -> {after}; nothing written", file=sys.stderr)
            return 1
        results.append((path, merged, before, after))
    for path, merged, before, after in results:
        write_atomic(path, merged)
        print(f"{path.name} ok {before} -> {after} session headers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
