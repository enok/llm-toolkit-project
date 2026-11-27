#!/usr/bin/env python3
"""Lint a browser-automation JavaScript snippet that uploads an image to LinkedIn.

Usage:

    check_upload_target.py SNIPPET_FILE [SNIPPET_FILE ...]

Save the snippet you are about to run through the browser tool's JavaScript
executor to a file and run this check first. The check reads the snippet text
only; it never runs the snippet and cannot see the browser tool's own
file-upload action (confirm separately that the action targets the proxy
input). It prints one ``violation: FILE:LINE: ...`` line per problem and exits
1 when it finds any of these:

    1. The text mentions ``attachment-input``. Inputs with that id prefix belong
       to the LinkedIn messaging overlay, not to the "Create post" composer, so a
       file forwarded there lands in a chat draft.
    2. A file-input selector (``input[type=file]``, ``input[type="file"]``,
       ``[type=file]``) is queried on ``document`` (also ``document.body``,
       ``document.documentElement``, ``window.document`` or ``deep(document, ...)``),
       or appears anywhere outside a ``root.querySelector(...)`` / ``deep(root, ...)``
       call whose root is not the document. A document-wide query returns the
       messaging overlay's inputs too.
    3. Files are forwarded to an element that is not the temporary proxy input
       with id ``tmp-upload-proxy`` that the image attach recipe creates. Forms
       recognised: ``X.files = ...`` (the dot may start a new line),
       ``X['files'] = ...``, ``Object.defineProperty(X, 'files', ...)``,
       ``Object.assign(X, {files: ...})``, ``Reflect.set(X, 'files', ...)`` and
       ``Object.getOwnPropertyDescriptor(..., 'files').set.call(X, ...)``. Any
       other use of the quoted name ``'files'`` is reported too, so that new
       spellings fail closed.

Comments count: the check does not parse JavaScript, so a banned token inside a
comment is reported too. Reword the comment or remove the line.

Exit codes: 0 no violation, 1 at least one violation, 2 usage or I/O error
(missing, unreadable or empty file). Treat every non-zero exit as "do not run
the snippet". Requires Python 3.9+ and the standard library only. All output is
ASCII.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import List, NamedTuple, Optional, Sequence, TextIO, Tuple

PROXY_ID = "tmp-upload-proxy"
MESSAGING_MARKER = "attachment-input"

# A quoted JavaScript string literal: the quote, the body (escapes allowed), the same quote.
_STR = r"(?P<q>[\"'`])(?P<sel>(?:\\.|(?!(?P=q)).)*)(?P=q)"
_FILE_SELECTOR = re.compile(r"\[\s*type\s*=\s*\\?[\"']?\s*file\b", re.I)
_QUERY_CALL = re.compile(
    r"(?P<recv>[A-Za-z_$][\w$.]*?)\s*\.\s*querySelector(?:All)?\s*\(\s*" + _STR, re.S
)
_DEEP_CALL = re.compile(r"\bdeep\s*\(\s*(?P<recv>[A-Za-z_$][\w$.]*)\s*,\s*" + _STR, re.S)
_DOCUMENT_WIDE = {"document", "window.document", "document.body", "document.documentElement", "document.head"}

_QFILES = r"[\"'`]files[\"'`]"
_QFILES_TOKEN = re.compile(_QFILES)
_DOT_FILES_ASSIGN = re.compile(r"\.\s*files\s*=(?![=>])")
_BRACKET_FILES_ASSIGN = re.compile(r"\[\s*" + _QFILES + r"\s*\]\s*=(?![=>])")
_DEFINE_FILES = re.compile(r"Object\s*\.\s*defineProperty\s*\(\s*(?P<expr>[^,]+?)\s*,\s*" + _QFILES, re.S)
_REFLECT_FILES = re.compile(r"Reflect\s*\.\s*set\s*\(\s*(?P<expr>[^,]+?)\s*,\s*" + _QFILES, re.S)
_ASSIGN_FILES = re.compile(
    r"Object\s*\.\s*assign\s*\(\s*(?P<expr>[^,]+?)\s*,\s*\{[^{}]*?[\"'`]?\bfiles\b[\"'`]?\s*(?::|,|\})", re.S
)
_DESCRIPTOR_FILES = re.compile(
    r"getOwnPropertyDescriptor\s*\([^()]*?" + _QFILES + r"\s*\)\s*\)?\s*\??\.\s*set\s*\.\s*(?:call|apply)"
    r"\s*\(\s*(?P<expr>[^,)]+?)\s*[,)]",
    re.S,
)
_IDENT = re.compile(r"^[A-Za-z_$][\w$]*$")


class Violation(NamedTuple):
    line: int
    message: str


def safe(text: str) -> str:
    """ASCII-only rendering of text taken from the snippet."""
    return text.encode("ascii", "backslashreplace").decode("ascii")


def line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _skip_space_back(text: str, i: int) -> int:
    while i > 0 and text[i - 1].isspace():
        i -= 1
    return i


def receiver_before(text: str, pos: int) -> Tuple[int, str]:
    """Return (start, source) of the member-expression that ends just before ``pos``.

    Walks backwards over identifiers, ``.`` links (newlines allowed) and balanced
    ``(...)`` / ``[...]`` groups, so ``document.getElementById('x')`` and ``a[0]``
    are returned whole and ``(a || b)`` is returned as the group.
    """
    i = _skip_space_back(text, pos)
    end = i
    while True:
        moved = False
        while i > 0 and text[i - 1] in ")]":
            close = text[i - 1]
            opener = "(" if close == ")" else "["
            depth = 0
            j = i - 1
            while j >= 0:
                if text[j] == close:
                    depth += 1
                elif text[j] == opener:
                    depth -= 1
                    if depth == 0:
                        break
                j -= 1
            if j < 0:
                return i, text[i:end].strip()
            i = j
            moved = True
        j = i
        while j > 0 and (text[j - 1].isalnum() or text[j - 1] in "_$"):
            j -= 1
        if j < i:
            i = j
            moved = True
        if not moved:
            break
        k = _skip_space_back(text, i)
        if k > 0 and text[k - 1] == "." and not (k > 1 and text[k - 2] == "."):
            i = _skip_space_back(text, k - 1)
            continue
        break
    return i, text[i:end].strip()


def rhs_after(text: str, pos: int) -> str:
    """Source of the right-hand side that starts at ``pos`` (after an ``=``).

    Stops at ``;`` or ``,`` outside brackets, or at a line end outside brackets
    unless the next line continues a member chain with ``.``. Leading blank space,
    newlines included, is skipped, so a declaration split over two lines is read whole.
    """
    n = len(text)
    i = pos
    while i < n and text[i].isspace():
        i += 1
    start = i
    depth = 0
    quote = ""
    while i < n:
        c = text[i]
        if quote:
            if c == "\\":
                i += 2
                continue
            if c == quote:
                quote = ""
        elif c in "\"'`":
            quote = c
        elif c in "([{":
            depth += 1
        elif c in ")]}":
            depth -= 1
            if depth < 0:
                break
        elif depth == 0 and c in ";,":
            break
        elif depth == 0 and c == "\n":
            j = i
            while j < n and text[j].isspace():
                j += 1
            if not (j < n and text[j] == "."):
                break
        i += 1
    return text[start:i]


def refers_to_proxy(expr: str, text: str) -> bool:
    """True when ``expr`` is, or is a variable that holds, the proxy input."""
    expr = expr.strip()
    if PROXY_ID in expr:
        return True
    if not _IDENT.match(expr):
        return False
    name = re.escape(expr)
    for m in re.finditer(r"(?<![\w$.])%s\s*=(?![=>])" % name, text):
        if PROXY_ID in rhs_after(text, m.end()):
            return True
    id_set = re.search(
        r"(?<![\w$.])%s\s*\.\s*id\s*=\s*[\"'`]%s[\"'`]|(?<![\w$.])%s\s*\.\s*setAttribute\s*\(\s*[\"']id[\"']\s*,\s*[\"']%s[\"']"
        % (name, re.escape(PROXY_ID), name, re.escape(PROXY_ID)),
        text,
    )
    return bool(id_set)


def file_selector_violations(text: str) -> List[Violation]:
    calls = []  # (start, end, receiver) of the selector string of every recognised query call
    for pattern in (_QUERY_CALL, _DEEP_CALL):
        for m in pattern.finditer(text):
            calls.append((m.start("sel"), m.end("sel"), re.sub(r"\s+", "", m.group("recv"))))
    found: List[Violation] = []
    for m in _FILE_SELECTOR.finditer(text):
        owner = next((c for c in calls if c[0] <= m.start() < c[1]), None)
        line = line_of(text, m.start())
        if owner is None:
            found.append(Violation(line, (
                "file-input selector outside a scoped query; query only the proxy input '%s' you created"
                % PROXY_ID)))
        elif owner[2] in _DOCUMENT_WIDE:
            found.append(Violation(line, (
                "document-wide file-input query on '%s'; query only the proxy input '%s' you created"
                % (safe(owner[2]), PROXY_ID))))
    return found


def forwarding_violations(text: str) -> List[Violation]:
    found: List[Violation] = []
    covered: List[Tuple[int, int]] = []  # spans of quoted 'files' tokens already judged

    def judge(expr: str, pos: int) -> None:
        if not expr or not refers_to_proxy(expr, text):
            found.append(Violation(line_of(text, pos), (
                "forwards files to '%s', not to the proxy input '%s'"
                % (safe(expr[-80:] or "?"), PROXY_ID))))

    for m in _DOT_FILES_ASSIGN.finditer(text):
        start, expr = receiver_before(text, m.start())
        judge(expr, start)
    for m in _BRACKET_FILES_ASSIGN.finditer(text):
        start, expr = receiver_before(text, m.start())
        judge(expr, start)
        covered.append(m.span())
    for pattern in (_DEFINE_FILES, _REFLECT_FILES, _ASSIGN_FILES, _DESCRIPTOR_FILES):
        for m in pattern.finditer(text):
            judge(m.group("expr").strip(), m.start("expr"))
            covered.append(m.span())

    for m in _QFILES_TOKEN.finditer(text):
        if not any(a <= m.start() < b for a, b in covered):
            found.append(Violation(line_of(text, m.start()), (
                "unrecognised use of the quoted name 'files'; set files only on the proxy input '%s' "
                "with 'proxy.files = ...'" % PROXY_ID)))
    return found


def check_text(text: str) -> List[Violation]:
    found: List[Violation] = []

    for m in re.finditer(re.escape(MESSAGING_MARKER), text, re.I):
        found.append(Violation(line_of(text, m.start()), (
            "references '%s'; those inputs belong to the messaging overlay, never to the post composer"
            % MESSAGING_MARKER)))

    found.extend(file_selector_violations(text))
    found.extend(forwarding_violations(text))
    return sorted(set(found))


def check_file(path: Path, out: TextIO) -> int:
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise OSError("empty snippet file: %s" % safe(str(path)))
    violations = check_text(text)
    for v in violations:
        out.write("violation: %s:%d: %s\n" % (safe(str(path)), v.line, v.message))
    if not violations:
        out.write("ok: %s\n" % safe(str(path)))
    return 1 if violations else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_upload_target.py",
        description="Lint a browser-automation JS snippet for LinkedIn upload-target mistakes "
        "(exit 0 ok, 1 violation, 2 usage or I/O error; any non-zero exit: do not run the snippet).",
    )
    parser.add_argument("snippets", nargs="+", metavar="SNIPPET_FILE", help="text file holding the JS snippet to lint")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse exits 0 for --help and 2 for usage errors
        code = exc.code
        return code if isinstance(code, int) else (0 if code is None else 2)
    status = 0
    for name in args.snippets:
        try:
            status = max(status, check_file(Path(name), sys.stdout))
        except (OSError, UnicodeError) as exc:
            sys.stderr.write("error: %s\n" % safe(str(exc)))
            return 2
    return status


if __name__ == "__main__":
    sys.exit(main())
