#!/usr/bin/env python3
"""Prepare and lint HTML that is pasted into the Medium editor.

Subcommands:

    build INPUT.html -o OUT.html
        Adds Medium code-block attributes to every <pre>, puts a single space
        on empty lines inside <pre> (a truly empty line splits one code box
        into several), and entity-encodes every non-ASCII character in the
        whole document as &#NNN; (Windows PowerShell 5.1
        ``Set-Clipboard -AsHtml`` mangles non-ASCII). Apart from line endings
        (CRLF is read as LF) and that encoding, markup outside <pre> is kept
        as is: build does not convert tables, inline code, markdown leftovers
        or image URLs; check reports those for the author to fix.

    check FILE.html [--repo-raw-prefix URL_PREFIX ...]
        Lints a paste file. Exits 1 and lists every issue when it finds
        markdown leftovers, tables, inline code, <pre> without code-block
        attributes, empty lines inside <pre>, raw.githubusercontent.com
        images whose ref is not a 7-40 hex commit SHA, or non-ASCII
        characters. Exits 0 when clean. All output is ASCII (non-ASCII text is
        shown as \\uXXXX escapes), so a cp1252 or ascii console or redirect
        cannot crash it.

Exit codes: 0 ok, 1 check failed, 2 usage or I/O error.
Requires Python 3.9+ and the standard library only.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, TextIO, Tuple
from urllib.parse import urlsplit

# File extension (no dot, lower case) -> Medium code-block language.
EXT_TO_LANG: Dict[str, str] = {
    "java": "java",
    "py": "python",
    "js": "javascript",
    "mjs": "javascript",
    "cjs": "javascript",
    "ts": "typescript",
    "mts": "typescript",
    "cts": "typescript",
    "kt": "kotlin",
    "go": "go",
    "rs": "rust",
    "cs": "csharp",
    "rb": "ruby",
    "sh": "bash",
    "sql": "sql",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "xml": "xml",
    "html": "html",
    "htm": "html",
    "css": "css",
}

# `language-<name>` class values -> Medium language (canonical names map to
# themselves; unknown names are plain text, mode 0).
LANG_ALIASES: Dict[str, str] = dict(EXT_TO_LANG)
LANG_ALIASES.update({lang: lang for lang in EXT_TO_LANG.values()})
LANG_ALIASES.update(
    {
        "python3": "python",
        "node": "javascript",
        "nodejs": "javascript",
        "golang": "go",
        "c#": "csharp",
        "shell": "bash",
        "zsh": "bash",
    }
)

PRE_RE = re.compile(r"<pre(?=[\s>])([^>]*)>(.*?)</pre\s*>", re.I | re.S)
PRE_OPEN_RE = re.compile(r"<pre(?=[\s>])([^>]*)>", re.I)
ATTR_RE = re.compile(r"""([\w:-]+)\s*(?:=\s*(?:"([^"]*)"|'([^']*)'|([^\s>"']+)))?""")
LANG_CLASS_RE = re.compile(r"(?:^|\s)(?:language|lang)-(\S+)")
CODE_WRAP_RE = re.compile(r"^\s*<code\b([^>]*)>(.*)</code\s*>\s*$", re.I | re.S)
LABEL_RE = re.compile(r"<strong>\s*([^<]+?)\s*</strong>\s*(?:</p>|<br\s*/?>)?\s*$", re.I)
IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
SHA_RE = re.compile(r"[0-9a-fA-F]{7,40}")
NON_ASCII_RE = re.compile(r"[^\x00-\x7f]")
LABEL_WINDOW = 300
MAX_NON_ASCII_ISSUES = 20
RAW_HOST = "raw.githubusercontent.com"


class Issue(NamedTuple):
    line: int
    code: str
    message: str


def ascii_safe(text: str) -> str:
    """Escape non-ASCII as backslash sequences so any console encoding can print it."""
    return text.encode("ascii", "backslashreplace").decode("ascii")


def emit(text: str, stream: Optional[TextIO] = None) -> None:
    print(ascii_safe(text), file=stream if stream is not None else sys.stdout)


def parse_attrs(attr_text: str) -> Dict[str, str]:
    """Return lower-cased attribute names mapped to their (unquoted) values."""
    attrs: Dict[str, str] = {}
    for match in ATTR_RE.finditer(attr_text):
        value = match.group(2) or match.group(3) or match.group(4) or ""
        attrs.setdefault(match.group(1).lower(), html.unescape(value))
    return attrs


def resolve_language(name: str) -> Optional[str]:
    return LANG_ALIASES.get(name.strip().lower())


def language_from_label(label: str) -> Optional[str]:
    """`src/Duck.java` -> `java`; labels without a known extension -> None."""
    name = label.strip().rstrip(":").strip()
    if "." not in name:
        return None
    return EXT_TO_LANG.get(name.rsplit(".", 1)[1].lower())


def unwrap_code(body: str) -> Tuple[str, str]:
    """Strip a sole `<code>` wrapper; return (inner body, the code element's class)."""
    match = CODE_WRAP_RE.match(body)
    if not match:
        return body, ""
    inner = match.group(2)
    if re.search(r"</?code\b", inner, re.I):
        return body, ""
    return inner, parse_attrs(match.group(1)).get("class", "")


def detect_language(pre_attrs: Dict[str, str], code_class: str, label_window: str) -> Optional[str]:
    """First resolvable source wins: pre class, code class, existing attr, label."""
    candidates: List[Optional[str]] = []
    for class_value in (pre_attrs.get("class", ""), code_class):
        found = LANG_CLASS_RE.search(class_value)
        candidates.append(resolve_language(found.group(1)) if found else None)
    existing = pre_attrs.get("data-code-block-lang", "")
    candidates.append(resolve_language(existing) if existing else None)
    label = LABEL_RE.search(label_window[-LABEL_WINDOW:])
    candidates.append(language_from_label(label.group(1)) if label else None)
    for candidate in candidates:
        if candidate:
            return candidate
    return None


def space_blank_lines(body: str) -> str:
    """Put one space on every empty interior line (first/last stay untouched)."""
    lines = body.split("\n")
    last = len(lines) - 1
    return "\n".join(" " if (line == "" and 0 < index < last) else line for index, line in enumerate(lines))


def entity_encode(text: str) -> str:
    return NON_ASCII_RE.sub(lambda match: "&#%d;" % ord(match.group()), text)


def build_html(text: str) -> Tuple[str, List[Optional[str]]]:
    """Return (paste-ready ASCII html, language per <pre> block; None = plain)."""
    pieces: List[str] = []
    languages: List[Optional[str]] = []
    cursor = 0
    for match in PRE_RE.finditer(text):
        pieces.append(text[cursor : match.start()])
        body, code_class = unwrap_code(match.group(2))
        language = detect_language(parse_attrs(match.group(1)), code_class, text[cursor : match.start()])
        body = space_blank_lines(body)
        if language:
            opening = '<pre data-code-block-mode="2" data-code-block-lang="%s">' % language
        else:
            opening = '<pre data-code-block-mode="0">'
        pieces.append(opening + body + "</pre>")
        languages.append(language)
        cursor = match.end()
    pieces.append(text[cursor:])
    return entity_encode("".join(pieces)), languages


def mask_pre_bodies(text: str) -> str:
    """Blank out <pre> contents (keeping newlines) so offsets and lines stay valid."""

    def mask(match: "re.Match[str]") -> str:
        whole = match.group(0)
        start = match.start(2) - match.start(0)
        end = match.end(2) - match.start(0)
        return whole[:start] + re.sub(r"[^\n]", " ", whole[start:end]) + whole[end:]

    return PRE_RE.sub(mask, text)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def snippet(text: str, offset: int, width: int = 40) -> str:
    line_start = text.rfind("\n", 0, offset) + 1
    line_end = text.find("\n", offset)
    line_end = len(text) if line_end == -1 else line_end
    return text[max(line_start, offset - 10) : min(line_end, offset + width)].strip()


def normalise_prefix(prefix: str) -> str:
    return prefix if prefix.endswith("/") else prefix + "/"


def check_image(src: str, prefixes: Sequence[str]) -> List[Tuple[str, str]]:
    problems: List[Tuple[str, str]] = []
    if prefixes and not any(src.startswith(prefix) for prefix in prefixes):
        problems.append(("image-prefix", "image outside the expected repo prefix: %s" % src))
    parts = urlsplit(src)
    if (parts.hostname or "").lower() == RAW_HOST:
        segments = parts.path.split("/")  # ['', owner, repo, ref, path...]
        ref = segments[3] if len(segments) > 4 else ""
        if not SHA_RE.fullmatch(ref):
            problems.append(
                (
                    "image-unpinned",
                    "raw.githubusercontent.com image is not pinned to a 7-40 hex commit SHA "
                    "(ref segment %r): %s" % (ref, src),
                )
            )
    return problems


def check_html(text: str, repo_raw_prefixes: Sequence[str] = ()) -> List[Issue]:
    issues: List[Issue] = []
    masked = mask_pre_bodies(text)
    prefixes = [normalise_prefix(prefix) for prefix in repo_raw_prefixes]

    for match in re.finditer(r"\]\(http", masked):
        issues.append(
            Issue(
                line_of(masked, match.start()),
                "markdown-leftover",
                "markdown link leftover '](http' near: %s" % snippet(masked, match.start()),
            )
        )
    for match in re.finditer(r"<table\b", masked, re.I):
        issues.append(
            Issue(
                line_of(masked, match.start()),
                "table",
                "<table> is not supported by Medium; convert to a list or a plain <pre>",
            )
        )
    for match in re.finditer(r"<code\b", masked, re.I):
        issues.append(
            Issue(
                line_of(masked, match.start()),
                "inline-code",
                "<code> outside <pre> (Medium has no inline code); convert to plain text",
            )
        )
    for match in PRE_OPEN_RE.finditer(text):
        attrs = parse_attrs(match.group(1))
        mode = attrs.get("data-code-block-mode")
        line = line_of(text, match.start())
        if mode is None:
            issues.append(Issue(line, "pre-attrs", "<pre> without data-code-block-mode"))
        elif mode not in ("0", "2"):
            issues.append(Issue(line, "pre-attrs", "<pre> with unsupported data-code-block-mode=%r" % mode))
        elif mode == "2" and not attrs.get("data-code-block-lang", "").strip():
            issues.append(Issue(line, "pre-attrs", '<pre data-code-block-mode="2"> without data-code-block-lang'))
    for match in PRE_RE.finditer(text):
        lines = match.group(2).split("\n")
        blank = [index for index, line in enumerate(lines) if line == "" and 0 < index < len(lines) - 1]
        if blank:
            issues.append(
                Issue(
                    line_of(text, match.start(2)) + blank[0],
                    "pre-blank-line",
                    "%d empty line(s) inside <pre> would split the Medium code box; "
                    "put a single space on each (run build)" % len(blank),
                )
            )
    for match in IMG_RE.finditer(masked):
        src = parse_attrs(match.group(0)[4:-1]).get("src", "")
        for code, message in check_image(src, prefixes):
            issues.append(Issue(line_of(masked, match.start()), code, message))

    per_line: Dict[int, List[str]] = {}
    for match in NON_ASCII_RE.finditer(text):
        per_line.setdefault(line_of(text, match.start()), []).append(match.group())
    for count, line in enumerate(sorted(per_line)):
        if count == MAX_NON_ASCII_ISSUES:
            issues.append(
                Issue(line, "non-ascii", "(+%d more lines with non-ASCII characters)" % (len(per_line) - count))
            )
            break
        chars = per_line[line]
        issues.append(
            Issue(
                line,
                "non-ascii",
                "%d non-ASCII character(s) left (first U+%04X); run build to entity-encode"
                % (len(chars), ord(chars[0])),
            )
        )
    return sorted(issues, key=lambda issue: (issue.line, issue.code))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def run_build(args: argparse.Namespace) -> int:
    if args.input.resolve() == args.output.resolve():
        emit("error: output must differ from input (the source is never overwritten)", sys.stderr)
        return 2
    built, languages = build_html(read_text(args.input))
    args.output.write_bytes(built.encode("ascii"))
    counts: Dict[str, int] = {}
    for language in languages:
        key = language or "plain"
        counts[key] = counts.get(key, 0) + 1
    detail = ", ".join("%s=%d" % (key, counts[key]) for key in sorted(counts)) or "none"
    emit("built %s: %d pre blocks (%s), %d bytes" % (args.output, len(languages), detail, len(built)))
    return 0


def run_check(args: argparse.Namespace) -> int:
    text = read_text(args.file)
    issues = check_html(text, args.repo_raw_prefix)
    for issue in issues:
        emit("%s:%d: %s: %s" % (args.file, issue.line, issue.code, issue.message))
    if issues:
        emit("%d issue(s) in %s" % (len(issues), args.file))
        return 1
    blocks = len(PRE_OPEN_RE.findall(text))
    images = len(IMG_RE.findall(mask_pre_bodies(text)))
    emit("OK: %s (%d pre blocks, %d images)" % (args.file, blocks, images))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="medium_paste_html.py",
        description="Prepare (build) and lint (check) HTML that is pasted into the Medium editor.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="add code-block attributes, space blank lines, entity-encode non-ASCII")
    build.add_argument("input", type=Path, help="source HTML (UTF-8)")
    build.add_argument("-o", "--output", type=Path, required=True, help="paste-ready ASCII HTML to write")
    build.set_defaults(handler=run_build)

    check = commands.add_parser("check", help="lint a paste file; exit 1 when issues are found")
    check.add_argument("file", type=Path, help="paste HTML to lint")
    check.add_argument(
        "--repo-raw-prefix",
        action="append",
        default=[],
        metavar="URL_PREFIX",
        help="expected image URL prefix, repeatable (for example "
        "https://raw.githubusercontent.com/<owner>/<repo>/); any <img> outside it is an issue. "
        "A raw.githubusercontent.com ref counts as pinned when it is 7-40 hex characters, so a "
        "branch or tag named like a hex string would pass",
    )
    check.set_defaults(handler=run_check)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits 0 for --help and 2 for usage errors
        code = exc.code
        return code if isinstance(code, int) else (0 if code is None else 2)
    try:
        return int(args.handler(args))
    except (OSError, UnicodeError) as exc:
        emit("error: %s" % exc, sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
