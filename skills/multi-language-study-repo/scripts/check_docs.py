#!/usr/bin/env python3
"""Docs drift guard for multi-language study repos (stdlib only, Python 3.9+).

Over the Markdown files selected by --docs it reports:

1. a `*.mmd` file under --diagrams that is not identical to the body of some
   ```mermaid fenced block;
2. a fenced block directly preceded by `<!-- source: <repo-relative path> -->`
   whose body differs from that file, or whose file is missing or resolves outside the
   repo (a marker that is not followed by a fenced block is reported too: it would
   guard nothing);
3. a relative link whose target does not exist, or leaves the repository, or exists
   only with a different letter case (GitHub paths are case-sensitive). Checked forms:
   inline links and images `[x](path#anchor)`, reference definitions `[id]: path`, and
   `src=`/`href=` of single-line `<img>`, `<a>`, `<source>`, `<video>`, `<audio>`,
   `<link>`, `<script>` tags. External schemes, mailto and pure `#anchor` links are
   skipped, as is anything inside fenced code or inline code or written with a backslash
   escape (`\\[x\\](y)`). Anchors are not validated.

Comparison rule: CRLF is normalised to LF, then a block body must equal the file
content minus its single final newline (if it has one).

Usage: check_docs.py --root REPO [--diagrams docs/diagrams] [--docs docs README.md]
Prints one `path: message` line per problem and exits 1, or prints `ok` and exits 0.
Exit 2: bad arguments or unreadable root. Output never fails on a console that cannot
encode a character: it is written as a backslash escape instead.
"""
from __future__ import annotations

import argparse
import html
import os
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, Tuple
from urllib.parse import unquote

DEFAULT_DIAGRAMS = "docs/diagrams"
DEFAULT_DOCS = ("docs", "README.md")
SKIP_DIRS = frozenset({".git", "node_modules", "target", ".venv", "venv", "__pycache__", "dist", "build"})

FENCE_OPEN_RE = re.compile(r"^(?P<indent>[ \t]*)(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
SOURCE_RE = re.compile(r"^[ \t]*<!--\s*source:\s*(?P<path>.+?)\s*-->[ \t]*$")
INLINE_CODE_RE = re.compile(r"(`+).*?\1")
ESCAPED_RE = re.compile(r"\\[!-/:-@\[-`{-~]")  # backslash + ASCII punctuation: a literal character
LINK_RE = re.compile(
    r"\]\(\s*(?:<(?P<angle>[^>]*)>|(?P<plain>(?:[^()\s]|\([^()\s]*\))+))"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
REF_DEF_RE = re.compile(
    r"^ {0,3}\[(?!\^)[^\]]+\]:[ \t]*(?:<([^>]*)>|(\S+))"
    r"(?:[ \t]+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?[ \t]*$"
)
HTML_REF_RE = re.compile(
    r"<(?:img|a|source|video|audio|link|script)\b[^>]*?\s(?:src|href)\s*=\s*(?:\"(?P<dq>[^\"]*)\"|'(?P<sq>[^']*)')",
    re.IGNORECASE,
)
EXTERNAL_RE = re.compile(r"^(?:[A-Za-z][A-Za-z0-9+.-]*:|//)")


class Block(NamedTuple):
    info: str  # first word of the info string, lower-cased ("" when absent)
    body: str  # lines between the fences joined with "\n" (no final newline)
    line: int  # 1-based line of the opening fence
    source: Optional[Tuple[int, str]]  # (marker line, marker path) when marked


class Scan(NamedTuple):
    blocks: List[Block]
    links: List[Tuple[int, str]]  # (line, target) outside code
    dangling: List[Tuple[int, str]]  # source markers not followed by a fence


def normalise_lf(text: str) -> str:
    return text.replace("\r\n", "\n")


def drop_final_newline(text: str) -> str:
    return text[:-1] if text.endswith("\n") else text


class _Open:
    """A fenced block that has been opened but not closed yet."""

    def __init__(self, char: str, length: int, indent: int, info: str, line: int,
                 marker: Optional[Tuple[int, str]]) -> None:
        self.char, self.length, self.indent = char, length, indent
        self.info, self.line, self.marker = info, line, marker
        self.body: List[str] = []

    def closes(self, line: str) -> bool:
        stripped = line.strip()
        return len(stripped) >= self.length and set(stripped) == {self.char}

    def add(self, line: str) -> None:
        cut = 0
        while cut < self.indent and cut < len(line) and line[cut] in " \t":
            cut += 1
        self.body.append(line[cut:])

    def finish(self) -> Block:
        words = self.info.split()
        return Block(words[0].lower() if words else "", "\n".join(self.body), self.line, self.marker)


def _opening(line: str) -> Optional[Tuple[str, int, int, str]]:
    m = FENCE_OPEN_RE.match(line)
    if not m:
        return None
    fence, info = m.group("fence"), m.group("info")
    if fence[0] == "`" and "`" in info:  # `` ```code``` `` on one line is inline code
        return None
    return fence[0], len(fence), len(m.group("indent")), info


def _targets(line: str) -> List[str]:
    """Link targets on one line of prose (inline code already removed)."""
    ref = REF_DEF_RE.match(line)
    if ref:
        return [(ref.group(1) if ref.group(1) is not None else ref.group(2)).strip()]
    found = []
    for lm in LINK_RE.finditer(line):
        found.append((lm.group("angle") if lm.group("angle") is not None else lm.group("plain")).strip())
    for hm in HTML_REF_RE.finditer(line):
        found.append(html.unescape(hm.group("dq") if hm.group("dq") is not None else hm.group("sq")).strip())
    return found


def scan_markdown(text: str) -> Scan:
    """Split Markdown into fenced blocks, links outside code and dangling source markers."""
    blocks: List[Block] = []
    links: List[Tuple[int, str]] = []
    dangling: List[Tuple[int, str]] = []
    pending: Optional[Tuple[int, str]] = None
    cur: Optional[_Open] = None
    for no, line in enumerate(normalise_lf(text).split("\n"), 1):
        if cur is not None:
            if cur.closes(line):
                blocks.append(cur.finish())
                cur = None
            else:
                cur.add(line)
            continue
        opening = _opening(line)
        if opening is not None:
            cur = _Open(opening[0], opening[1], opening[2], opening[3], no, pending)
            pending = None
            continue
        if pending is not None:
            dangling.append(pending)
            pending = None
        marker = SOURCE_RE.match(line)
        if marker:
            pending = (no, marker.group("path"))
            continue
        prose = INLINE_CODE_RE.sub("", ESCAPED_RE.sub("", line))
        links.extend((no, target) for target in _targets(prose))
    if cur is not None:  # an unclosed fence runs to the end of the file
        blocks.append(cur.finish())
    if pending is not None:
        dangling.append(pending)
    return Scan(blocks, links, dangling)


def _read(path: Path) -> Tuple[Optional[str], str]:
    """Return (text, "") or (None, reason); text is decoded as UTF-8."""
    try:
        return path.read_bytes().decode("utf-8"), ""
    except (OSError, UnicodeDecodeError) as exc:
        return None, str(exc) or exc.__class__.__name__


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _within(root: Path, path: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _inside(root: Path, raw: str) -> Optional[Path]:
    """root/raw lexically normalised (symlinks not followed), or None when it leaves the repo."""
    candidate = Path(os.path.normpath(str(root / raw)))
    return candidate if _within(root, candidate) else None


def exists_exact(root: Path, dest: Path) -> bool:
    """True when dest (inside root) exists with exactly this letter case in every component.

    Decided by directory listings only, so a case-insensitive file system (Windows, macOS)
    reports the same answer as GitHub's case-sensitive one.
    """
    current = root
    for part in dest.relative_to(root).parts:
        try:
            names = os.listdir(str(current))
        except OSError:
            return False
        if part not in names:
            return False
        current = current / part
    return True


def collect_markdown(root: Path, entries: Sequence[Path]) -> List[Path]:
    """Markdown files named by (or found recursively under) entries, sorted, no duplicates."""
    found = {}
    for entry in entries:
        if entry.is_dir():
            for p in entry.rglob("*.md"):
                if p.is_file() and not any(part in SKIP_DIRS for part in p.relative_to(entry).parts):
                    found[_rel(root, p)] = p
        else:
            found[_rel(root, entry)] = entry
    return [found[key] for key in sorted(found)]


def link_problem(root: Path, md: Path, target: str) -> Optional[str]:
    """Message when a relative link target is unusable, else None."""
    if not target or target.startswith("#") or EXTERNAL_RE.match(target):
        return None
    path_part = unquote(target.split("#", 1)[0].split("?", 1)[0])
    if not path_part:
        return None
    base = root if path_part.startswith("/") else md.parent
    dest = Path(os.path.normpath(str(base / path_part.lstrip("/"))))
    if not _within(root, dest):
        return f"link leaves the repository -> {target}"
    if not exists_exact(root, dest):
        return f"broken link -> {target}"
    return None


def source_problem(root: Path, marker_path: str, body: str) -> Optional[str]:
    """Message when a source-marked block does not match its file, else None."""
    src = _inside(root, marker_path)
    if src is None or os.path.isabs(marker_path):
        return f"source path must be repo-relative and inside the repo -> {marker_path}"
    if not exists_exact(root, src) or not src.is_file():
        return f"source file not found -> {marker_path}"
    if not _within(root.resolve(), src.resolve()):
        return f"source file resolves outside the repository (symlink?) -> {marker_path}"
    text, reason = _read(src)
    if text is None:
        return f"cannot read source file -> {marker_path} ({reason})"
    if drop_final_newline(normalise_lf(text)) != body:
        return f"code block differs from source file -> {marker_path}"
    return None


def check(root: Path, diagrams: Optional[Path], docs: Sequence[Path]) -> List[str]:
    """Return one `path: message` string per problem (empty list when the docs are clean)."""
    issues: List[str] = []
    scans = []
    for md in collect_markdown(root, docs):
        text, reason = _read(md)
        if text is None:
            issues.append(f"{_rel(root, md)}: cannot read file ({reason})")
            continue
        scans.append((md, _rel(root, md), scan_markdown(text[1:] if text.startswith("\ufeff") else text)))

    if diagrams is not None:
        mermaid_bodies = {b.body for _, _, scan in scans for b in scan.blocks if b.info == "mermaid"}
        mmd_files = {_rel(root, p): p for p in diagrams.rglob("*.mmd") if p.is_file()}
        for rel in sorted(mmd_files):
            text, reason = _read(mmd_files[rel])
            if text is None:
                issues.append(f"{rel}: cannot read file ({reason})")
            elif drop_final_newline(normalise_lf(text)) not in mermaid_bodies:
                issues.append(f"{rel}: not identical to the body of any ```mermaid block in the scanned "
                              f"docs (drift or missing)")

    for md, rel, scan in scans:
        found: List[Tuple[int, str]] = []
        for line, marker_path in scan.dangling:
            found.append((line, f"line {line}: source marker not followed by a fenced block -> {marker_path}"))
        for block in scan.blocks:
            if block.source is not None:
                marker_line, marker_path = block.source
                message = source_problem(root, marker_path, block.body)
                if message:
                    found.append((marker_line, f"line {marker_line}: {message}"))
        for line, target in scan.links:
            message = link_problem(root, md, target)
            if message:
                found.append((line, f"line {line}: {message}"))
        issues.extend(f"{rel}: {message}" for _, message in sorted(found, key=lambda item: item[0]))
    return issues


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="check_docs.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--root", required=True, type=Path, help="repository root")
    ap.add_argument("--diagrams", metavar="DIR", default=None,
                    help=f"folder with *.mmd sources, relative to --root (default: {DEFAULT_DIAGRAMS}, "
                         "skipped when absent)")
    ap.add_argument("--docs", metavar="PATH", nargs="+", default=None,
                    help="Markdown files or folders (scanned recursively), relative to --root "
                         f"(default: {' '.join(DEFAULT_DOCS)}; absent defaults are skipped)")
    return ap


def harden_output_streams() -> None:
    """Never crash on a console/pipe whose encoding cannot represent a path or link target."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="backslashreplace")
            except (OSError, ValueError):
                pass


def _usage_error(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    harden_output_streams()
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 on bad arguments, 0 for --help
        return exc.code if isinstance(exc.code, int) else 2
    if not args.root.is_dir():
        return _usage_error(f"root is not a directory: {args.root}")
    root = args.root.resolve()

    diagrams: Optional[Path] = None
    diagrams_raw = args.diagrams if args.diagrams is not None else DEFAULT_DIAGRAMS
    diagrams_path = _inside(root, diagrams_raw)
    if diagrams_path is None:
        return _usage_error(f"--diagrams must stay inside the root: {diagrams_raw}")
    if diagrams_path.is_dir():
        diagrams = diagrams_path
    elif args.diagrams is not None:
        return _usage_error(f"diagrams folder not found: {diagrams_raw}")

    explicit = args.docs is not None
    docs: List[Path] = []
    for raw in (args.docs if explicit else DEFAULT_DOCS):
        path = _inside(root, raw)
        if path is None:
            return _usage_error(f"--docs entry must stay inside the root: {raw}")
        if path.exists():
            docs.append(path)
        elif explicit:
            return _usage_error(f"docs path not found: {raw}")
    if not docs:
        return _usage_error(f"none of the default docs paths exist ({' '.join(DEFAULT_DOCS)}); pass --docs")

    issues = check(root, diagrams, docs)
    if issues:
        print("\n".join(issues))
        return 1
    print("ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
