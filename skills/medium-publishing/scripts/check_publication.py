#!/usr/bin/env python3
"""Check the publishing shape of a study LinkedIn post or Medium article.

Subcommands (every limit below can come from a profile, see "Limits"):

    post FILE [--profile PATH] [--max-chars N] [--max-hashtags N] [--hook-chars N]
              [--require-link URL ...] [--alias TAG=PHRASE ...] [--forbid TERM ...]
        FILE is the plain text of a LinkedIn post. Fails when any of these hold:
          chars     total characters (line ends are one character each, leading and
                    trailing blank space is not counted) exceed --max-chars;
          hashtags  more than --max-hashtags hashtags (``#Word`` at a word boundary,
                    letter first; a ``#`` inside a URL, inside a word such as ``C#``
                    or in an entity such as ``&#39;`` is not a hashtag);
          hook      the hook (the text before the first blank line) is longer than
                    --hook-chars characters;
          link      a --require-link URL is not in the text (a link counts when it
                    equals the URL, ignoring a trailing ``/`` and trailing sentence
                    punctuation, or when it is the URL plus ``?query`` or ``#anchor``);
          topic     a hashtag is not backed by the text. CamelCase is split and
                    compared case-insensitively, so ``#SystemDesign`` needs
                    "system design" in the post body, outside the hashtag tokens and
                    outside URLs. The joined spelling ("systemdesign") and any
                    ``--alias TAG=PHRASE`` phrase also back a tag (repeatable;
                    TAG may carry its ``#``; an alias adds to, never replaces, the
                    CamelCase reading);
          forbid    a --forbid term occurs in the hook (case-insensitive, repeatable).

    article FILE [--profile PATH] [--title TEXT] [--subtitle TEXT] [--forbid-title TERM ...]
                 [--max-words N] [--max-code-blocks N] [--max-code-lines N]
                 [--min-images N] [--max-images N] [--action-heading REGEX]
        FILE is a Markdown or HTML article (decided by the file name, ignoring a
        trailing ``.txt``; otherwise by looking for HTML block tags). Markdown
        headings are ATX headings (``# Title``); Setext headings, YAML front matter
        and code fences inside block quotes are not recognised. Fails when:
          title-length / title-forbidden   the title (--title, else the first H1:
                    a ``# `` line or the first ``<h1>``) is longer than 100
                    characters or holds a --forbid-title term (case-insensitive,
                    repeatable; used for the pattern name);
          subtitle-length / subtitle-forbidden   the --subtitle (optional) is longer
                    than 140 characters or holds a --forbid-title term;
          words     the body has more than --max-words words; Markdown code blocks
                    (fenced or indented) and HTML ``<pre>`` blocks, image lines (``![](...)``,
                    ``<img>``, ``<figure>`` with its caption) and the first H1 are
                    not counted (inline code is), and a token needs a letter or digit
                    to be a word;
          code-blocks   more than --max-code-blocks code blocks (Markdown: fenced
                    blocks, also nested in list items at any indent, and indented
                    blocks of CommonMark; HTML: ``<pre>``);
          code-lines    a code block has more than --max-code-lines lines (blank
                    lines inside count, blank lines at its start and end do not);
          images-min / images-max   fewer than --min-images or more than
                    --max-images images: Markdown ``![alt](src)``,
                    ``![alt][ref]`` and HTML ``<img>`` outside code blocks and
                    inline code;
          action-heading   no heading (the title excepted) matches the regex
                    --action-heading, case-insensitive, default "next step";
          markdown-link   an HTML article still holds a Markdown link (``](http``);
          title         no title is found and none is passed;
          fence         a Markdown code fence is never closed.

Limits: each limit is the first of these that is set:
    1. its command-line flag (an explicit flag always wins);
    2. ``--profile PATH``: the first fenced ``json`` block of a Markdown file, an
       object with a ``post`` and an ``article`` section, for example
       ``{"post": {"max_chars": 1300, "max_hashtags": 5, "hook_chars": 200},
         "article": {"max_words": 1500, "max_code_blocks": 1, "max_code_lines": 15,
                     "min_images": 2, "max_images": 3}}``.
       Only the section of the subcommand is read. A key that is absent is skipped,
       a key that is not listed here is ignored, a listed key must hold a whole
       number of 0 or more. No such block, a block that is not valid JSON, or a
       wrong value is an input error (exit 2);
    3. the built-in default: post 1300 characters, 5 hashtags, hook 200;
       article 1500 words, 1 code block, 15 lines per block, 2 to 3 images.
The title (100 characters) and subtitle (140) limits are fixed.

Output is one line per finding, ``violation: FILE: rule: message`` (``FILE:LINE:``
when a line is known), then nothing else. On success it prints one summary line
``ok: FILE: ...`` with the measured values against the limits that applied.

Exit codes: 0 every rule holds, 1 at least one rule fails, 2 usage or input error
(bad option, missing, unreadable, non-UTF-8 or empty file, invalid regex, bad
profile). Any non-zero exit means: do not publish. Requires Python 3.9+ and the
standard library only; files are read as UTF-8 (a BOM and CRLF line ends are
accepted); all output is ASCII.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Sequence, TextIO, Tuple

TITLE_MAX_CHARS = 100
SUBTITLE_MAX_CHARS = 140
DEFAULT_ACTION_HEADING = "next step"

# Built-in limits, used when neither a command-line flag nor a profile sets one.
DEFAULTS: Dict[str, Dict[str, int]] = {
    "post": {"max_chars": 1300, "max_hashtags": 5, "hook_chars": 200},
    "article": {"max_words": 1500, "max_code_blocks": 1, "max_code_lines": 15, "min_images": 2, "max_images": 3},
}


class InputError(Exception):
    """A usage or input problem that is not a rule failure (exit 2)."""


class Finding(NamedTuple):
    rule: str
    message: str
    line: int = 0


class Report(NamedTuple):
    findings: List[Finding]
    summary: str


def safe(text: str) -> str:
    """ASCII-only rendering of text taken from the checked file or the command line."""
    return text.encode("ascii", "backslashreplace").decode("ascii")


def normalise_newlines(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def count_words(text: str) -> int:
    return sum(1 for token in text.split() if any(ch.isalnum() for ch in token))


def contains_term(text: str, term: str) -> bool:
    return squash(term).casefold() in squash(text).casefold()


# --------------------------------------------------------------------------- post

_URL = re.compile(r"(?:https?://|www\.)[^\s<>\"']+", re.I)
_HASHTAG = re.compile(r"(?<![\w&#/])#([^\W\d_]\w*)")
_URL_TRAILING = ".,;:!?)]}'\""


def mask_urls(text: str) -> str:
    """Blank out URLs, keeping every offset and line break where it was."""
    return _URL.sub(lambda m: " " * len(m.group(0)), text)


def find_hashtags(text: str) -> List[Tuple[int, str]]:
    """(line, name) of every hashtag, URLs excluded."""
    found: List[Tuple[int, str]] = []
    for number, line in enumerate(mask_urls(text).split("\n"), 1):
        for m in _HASHTAG.finditer(line):
            found.append((number, m.group(1)))
    return found


def split_camel(name: str) -> List[str]:
    """``SystemDesign`` -> [system, design]; ``LLMOps`` -> [llm, ops]; ``Java25`` -> [java, 25]."""
    words: List[str] = []
    current = ""
    for i, ch in enumerate(name):
        if not ch.isalnum():
            if current:
                words.append(current)
            current = ""
            continue
        prev = name[i - 1] if i else ""
        nxt = name[i + 1] if i + 1 < len(name) else ""
        boundary = False
        if current:
            if ch.isupper() and (prev.islower() or prev.isdigit()):
                boundary = True
            elif ch.isupper() and prev.isupper() and nxt.islower():
                boundary = True
            elif ch.isdigit() != prev.isdigit():
                boundary = True
        if boundary:
            words.append(current)
            current = ""
        current += ch
    if current:
        words.append(current)
    return [w.casefold() for w in words]


def words_of(text: str) -> str:
    return " ".join(re.sub(r"[\W_]+", " ", text.casefold()).split())


def tag_key(tag: str) -> str:
    return tag.lstrip("#").casefold()


def post_urls(text: str) -> List[str]:
    return [m.group(0).rstrip(_URL_TRAILING) for m in re.finditer(r"https?://[^\s<>\"']+", text, re.I)]


def link_present(required: str, urls: Sequence[str]) -> bool:
    want = required.strip().rstrip(_URL_TRAILING + "/")
    for url in urls:
        got = url.rstrip(_URL_TRAILING + "/")
        if got == want or (got.startswith(want) and got[len(want):len(want) + 1] in ("?", "#")):
            return True
    return False


def check_post(
    text: str,
    max_chars: int = DEFAULTS["post"]["max_chars"],
    max_hashtags: int = DEFAULTS["post"]["max_hashtags"],
    hook_chars: int = DEFAULTS["post"]["hook_chars"],
    require_links: Sequence[str] = (),
    aliases: Optional[Dict[str, List[str]]] = None,
    forbid: Sequence[str] = (),
) -> Report:
    text = normalise_newlines(text).strip()
    findings: List[Finding] = []

    total = len(text)
    if total > max_chars:
        findings.append(Finding("chars", "%d characters, max %d (over by %d)" % (total, max_chars, total - max_chars)))

    tags = find_hashtags(text)
    if len(tags) > max_hashtags:
        findings.append(Finding("hashtags", "%d hashtags, max %d: %s" % (
            len(tags), max_hashtags, " ".join("#" + safe(name) for _, name in tags))))

    hook = re.split(r"\n[ \t]*\n", text, maxsplit=1)[0].strip()
    if len(hook) > hook_chars:
        findings.append(Finding("hook", "hook is %d characters, max %d (over by %d); the hook is the text before the "
                                        "first blank line" % (len(hook), hook_chars, len(hook) - hook_chars)))

    urls = post_urls(text)
    matched_links = 0
    for link in require_links:
        if link_present(link, urls):
            matched_links += 1
        else:
            findings.append(Finding("link", "required link is missing: %s" % safe(link)))

    body = " %s " % words_of(_HASHTAG.sub(" ", mask_urls(text)))
    alias_map = aliases or {}
    seen = set()
    backed = 0
    unique_tags: List[str] = []
    for _, name in tags:
        if name.casefold() not in seen:
            seen.add(name.casefold())
            unique_tags.append(name)
    for name in unique_tags:
        parts = split_camel(name)
        phrases = [" ".join(parts), "".join(parts)] + [words_of(p) for p in alias_map.get(tag_key(name), [])]
        if any(p and " %s " % p in body for p in phrases):
            backed += 1
        else:
            findings.append(Finding("topic", "#%s is not backed by the post text; expected \"%s\" outside the "
                                             "hashtags and URLs (or an --alias)" % (safe(name), safe(phrases[0]))))

    for term in forbid:
        if contains_term(hook, term):
            findings.append(Finding("forbid", "hook contains forbidden term \"%s\"" % safe(term)))

    summary = "post chars=%d/%d hashtags=%d/%d hook=%d/%d links=%d/%d topics=%d/%d" % (
        total, max_chars, len(tags), max_hashtags, len(hook), hook_chars,
        matched_links, len(require_links), backed, len(unique_tags))
    return Report(findings, summary)


# ------------------------------------------------------------------------ article


class CodeBlock(NamedTuple):
    line: int
    lines: int


class Parsed(NamedTuple):
    title: Optional[str]
    headings: List[str]
    words: int
    code_blocks: List[CodeBlock]
    unclosed_fences: List[int]
    markdown_link_lines: List[int]
    images: int


def code_line_count(block_text: str) -> int:
    lines = block_text.split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return len(lines)


_FENCE = re.compile(r"^[ \t]*(?P<fence>`{3,}|~{3,})(?P<info>.*)$")
_ATX = re.compile(r"^(#{1,6})(?:[ \t]+(.*))?$")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_MD_IMAGE_REF = re.compile(r"!\[[^\]]*\]\[[^\]]*\]")
_HTML_IMG = re.compile(r"<img\b", re.I)
_MD_LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
_HTML_TAG = re.compile(r"</?[A-Za-z][^>]*>")
_LIST_START = re.compile(r"([-*+]|\d{1,9}[.)])( +|$)")
_LINK_DEFINITION = re.compile(r"^ {0,3}\[[^\]]+\]:\s*\S+")
_THEMATIC_BREAK = re.compile(r"([-*_])(?:[ \t]*\1){2,}")
_SETEXT_UNDERLINE = re.compile(r"=+|-+")
_CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
_HELD_OPEN, _HELD_CLOSE = "\ue000", "\ue001"
_HELD = re.compile("%s(\\d+)%s" % (_HELD_OPEN, _HELD_CLOSE))


def hold_code_spans(line: str) -> Tuple[str, List[str]]:
    """Swap every inline code span for a placeholder, so ``List<String>`` or ``<img>`` in backticks is plain text."""
    spans: List[str] = []

    def hold(m: "re.Match[str]") -> str:
        spans.append(m.group(2))
        return "%s%d%s" % (_HELD_OPEN, len(spans) - 1, _HELD_CLOSE)

    return _CODE_SPAN.sub(hold, line), spans


def markdown_prose(line: str) -> str:
    line, spans = hold_code_spans(line)
    line = _MD_IMAGE.sub(" ", line)
    line = _MD_IMAGE_REF.sub(" ", line)
    line = _MD_LINK.sub(r"\1", line)
    line = _HTML_TAG.sub(" ", line)
    return _HELD.sub(lambda m: spans[int(m.group(1))], line)


def count_markdown_images(line: str) -> int:
    line = hold_code_spans(line)[0]
    return len(_MD_IMAGE.findall(line)) + len(_MD_IMAGE_REF.findall(line)) + len(_HTML_IMG.findall(line))


def indent_of(line: str) -> int:
    """Columns of leading white space (a tab advances to the next multiple of four)."""
    return len(line[: len(line) - len(line.lstrip(" \t"))].expandtabs(4))


def list_item_offset(rest: str) -> Optional[int]:
    """Columns from the marker to the item content when ``rest`` starts a list item, else None."""
    m = _LIST_START.match(rest)
    if not m:
        return None
    gap = len(m.group(2))
    return len(m.group(1)) + (gap if 1 <= gap <= 4 and rest[m.end():].strip() else 1)


def parse_markdown(text: str) -> Parsed:
    """Collect title, headings, word count, code blocks and images of a Markdown article.

    Code blocks are fenced blocks (a fence inside a list item may sit at any depth) and
    indented blocks: a run of lines indented four columns past the enclosing list item
    content (or past the margin), started after a blank line or a block that is not a
    paragraph, as in CommonMark. A line right after a paragraph line continues that
    paragraph, so it never starts a code block.
    """
    title: Optional[str] = None
    headings: List[str] = []
    prose: List[str] = []
    blocks: List[CodeBlock] = []
    unclosed: List[int] = []
    images = 0
    fence: Optional[Tuple[str, int, int, bool]] = None  # (char, length, opening line, closes at any indent)
    indented: Optional[Tuple[int, int]] = None  # (content column of the container, opening line)
    buffer: List[str] = []
    in_comment = False
    items: List[int] = []  # content column of every open list item, outermost first
    paragraph = False  # the previous line was a paragraph line
    for number, raw in enumerate(text.split("\n"), 1):
        line = raw
        if fence is not None:
            m = _FENCE.match(line)
            if (m and m.group("fence")[0] == fence[0] and len(m.group("fence")) >= fence[1]
                    and not m.group("info").strip() and (fence[3] or indent_of(line) <= 3)):
                blocks.append(CodeBlock(fence[2], code_line_count("\n".join(buffer))))
                fence, buffer, paragraph = None, [], False
            else:
                buffer.append(line)
            continue
        if indented is not None:
            if not line.strip():
                buffer.append("")
                continue
            if indent_of(line) >= indented[0] + 4:
                buffer.append(line)
                continue
            blocks.append(CodeBlock(indented[1], code_line_count("\n".join(buffer))))
            indented, buffer, paragraph = None, [], False
        if in_comment:
            if "-->" not in line:
                continue
            line = line.split("-->", 1)[1]
            in_comment = False
        line = re.sub(r"<!--.*?-->", " ", line)
        if "<!--" in line:
            line = line.split("<!--", 1)[0]
            in_comment = True
        if not raw.strip():
            paragraph = False
            continue
        if not line.strip():
            # a line that held only a comment is an HTML block: it ends a paragraph and a list it does not sit in
            while items and indent_of(raw) < items[-1]:
                items.pop()
            paragraph = False
            continue
        column = indent_of(line)
        rest = line.strip()
        inside = not items or column >= items[-1]  # a setext underline must sit in the container of its paragraph
        if _THEMATIC_BREAK.fullmatch(rest) or (paragraph and inside and _SETEXT_UNDERLINE.fullmatch(rest)):
            if column - max([c for c in items if c <= column], default=0) <= 3:
                while items and column < items[-1]:
                    items.pop()
                paragraph = False  # a thematic break or a setext underline ends the paragraph
                continue
        fence_open = _FENCE.match(line)
        if fence_open and fence_open.group("fence")[0] == "`" and "`" in fence_open.group("info"):
            fence_open = None
        offset = list_item_offset(rest)
        if offset is not None and paragraph and inside:
            marker = rest.split(None, 1)[0]
            if marker == rest or (marker[0].isdigit() and marker[:-1] != "1"):
                offset = None  # only a bullet or "1." with content can interrupt a paragraph of its own container
        atx = _ATX.match(rest)
        if _LINK_DEFINITION.match(line) and column <= 3:
            continue
        if paragraph and not (fence_open or offset is not None or atx or rest.startswith(">")):
            images += count_markdown_images(line)
            prose.append(markdown_prose(line))  # lazy continuation of the paragraph
            continue
        open_items = list(items)
        while items and column < items[-1]:
            items.pop()
        base = items[-1] if items else 0
        relative = column - base
        if fence_open and (items or relative <= 3):
            fence = (fence_open.group("fence")[0], len(fence_open.group("fence")), number, bool(items) or relative > 3)
            continue
        if relative >= 4 and not paragraph:
            indented, buffer = (base, number), [line]
            continue
        if relative >= 4:
            items[:] = open_items  # a lazy continuation line leaves its list items open
            images += count_markdown_images(line)
            prose.append(markdown_prose(line))
            continue
        if atx:
            images += count_markdown_images(rest)
            heading_text = squash(markdown_prose(re.sub(r"[ \t]+#+[ \t]*$", "", atx.group(2) or "")))
            paragraph = False
            if len(atx.group(1)) == 1 and title is None:
                title = heading_text
                continue
            headings.append(heading_text)
            prose.append(heading_text)
            continue
        if offset is not None:
            items.append(column + offset)
        images += count_markdown_images(line)
        item = _LIST_START.match(rest) if offset is not None else None
        content = rest[item.end():] if item else line
        prose.append(markdown_prose(content))
        paragraph = bool(content.strip())  # an empty list item holds no paragraph
    if fence is not None:
        unclosed.append(fence[2])
        blocks.append(CodeBlock(fence[2], code_line_count("\n".join(buffer))))
    if indented is not None:
        blocks.append(CodeBlock(indented[1], code_line_count("\n".join(buffer))))
    return Parsed(title, headings, count_words(html.unescape("\n".join(prose))), blocks, unclosed, [], images)


class _HtmlArticle(HTMLParser):
    BLOCK = {"p", "div", "section", "article", "li", "ul", "ol", "blockquote", "br", "hr", "table", "tr", "td", "th",
             "h1", "h2", "h3", "h4", "h5", "h6", "figcaption", "header", "footer", "main", "aside", "dl", "dt", "dd"}
    SKIP = {"script", "style", "title"}
    HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: Optional[str] = None
        self.headings: List[str] = []
        self.text: List[str] = []
        self.blocks: List[CodeBlock] = []
        self._pre = 0
        self._figure = 0
        self._skip = 0
        self._code: List[str] = []
        self._code_line = 0
        self._heading: Optional[Tuple[str, List[str]]] = None
        self.images = 0

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        if tag == "img" and not self._pre and not self._skip:
            self.images += 1
        if tag in self.SKIP:
            self._skip += 1
        elif tag == "pre":
            self._pre += 1
            if self._pre == 1:
                self._code, self._code_line = [], self.getpos()[0]
        elif tag == "figure":
            self._figure += 1
        elif tag in self.HEADINGS and not self._pre and not self._figure:
            self._heading = (tag, [])
        if tag == "br" and self._pre:
            self._code.append("\n")
        elif tag in self.BLOCK and not self._pre:
            self.text.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.SKIP and self._skip:
            self._skip -= 1
        elif tag == "pre" and self._pre:
            self._pre -= 1
            if self._pre == 0:
                self.blocks.append(CodeBlock(self._code_line, code_line_count("".join(self._code))))
        elif tag == "figure" and self._figure:
            self._figure -= 1
        elif self._heading and self._heading[0] == tag:
            heading_text = squash("".join(self._heading[1]))
            self._heading = None
            if tag == "h1" and self.title is None:
                self.title = heading_text
            else:
                self.headings.append(heading_text)
                self.text.append(" %s " % heading_text)
        if tag in self.BLOCK and tag != "br" and not self._pre:
            self.text.append("\n")

    def finish(self) -> None:
        """Count a ``<pre>`` that the file never closes, so it cannot hide from the code limits."""
        if self._pre:
            self.blocks.append(CodeBlock(self._code_line, code_line_count("".join(self._code))))
            self._pre = 0

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        if self._pre:
            self._code.append(data)
        elif self._figure:
            return
        elif self._heading:
            self._heading[1].append(data)
        else:
            self.text.append(data)


def parse_html(text: str) -> Parsed:
    parser = _HtmlArticle()
    parser.feed(text)
    parser.close()
    parser.finish()
    leftover = [n for n, line in enumerate(text.split("\n"), 1) for _ in range(line.count("](http"))]
    return Parsed(parser.title, parser.headings, count_words("".join(parser.text)), parser.blocks, [], leftover,
                  parser.images)


def detect_format(name: str, text: str) -> str:
    lowered = name.lower()
    if lowered.endswith(".txt"):
        lowered = lowered[: -len(".txt")]
    if lowered.endswith((".html", ".htm")):
        return "html"
    if lowered.endswith((".md", ".markdown")):
        return "markdown"
    return "html" if re.search(r"<(?:h[1-6]|p|pre|figure|div|section|article)\b", text, re.I) else "markdown"


def check_article(
    text: str,
    fmt: str,
    title: Optional[str] = None,
    subtitle: Optional[str] = None,
    forbid_title: Sequence[str] = (),
    max_words: int = DEFAULTS["article"]["max_words"],
    max_code_blocks: int = DEFAULTS["article"]["max_code_blocks"],
    max_code_lines: int = DEFAULTS["article"]["max_code_lines"],
    action_heading: str = DEFAULT_ACTION_HEADING,
    min_images: int = DEFAULTS["article"]["min_images"],
    max_images: int = DEFAULTS["article"]["max_images"],
) -> Report:
    action = re.compile(action_heading, re.I)
    text = normalise_newlines(text)
    parsed = parse_html(text) if fmt == "html" else parse_markdown(text)
    findings: List[Finding] = []

    shown_title = squash(title) if title is not None else parsed.title
    if shown_title is None:
        findings.append(Finding("title", "no title found; start the article with a first-level heading (\"# Title\" "
                                         "or <h1>) or pass --title"))
    else:
        if len(shown_title) > TITLE_MAX_CHARS:
            findings.append(Finding("title-length", "title is %d characters, max %d (over by %d)" % (
                len(shown_title), TITLE_MAX_CHARS, len(shown_title) - TITLE_MAX_CHARS)))
        for term in forbid_title:
            if contains_term(shown_title, term):
                findings.append(Finding("title-forbidden", "title contains forbidden term \"%s\"" % safe(term)))

    shown_subtitle = squash(subtitle) if subtitle is not None else None
    if shown_subtitle is not None:
        if len(shown_subtitle) > SUBTITLE_MAX_CHARS:
            findings.append(Finding("subtitle-length", "subtitle is %d characters, max %d (over by %d)" % (
                len(shown_subtitle), SUBTITLE_MAX_CHARS, len(shown_subtitle) - SUBTITLE_MAX_CHARS)))
        for term in forbid_title:
            if contains_term(shown_subtitle, term):
                findings.append(Finding("subtitle-forbidden", "subtitle contains forbidden term \"%s\"" % safe(term)))

    if parsed.words > max_words:
        findings.append(Finding("words", "%d words, max %d (over by %d); code blocks, image lines and the title are "
                                         "not counted" % (parsed.words, max_words, parsed.words - max_words)))

    if len(parsed.code_blocks) > max_code_blocks:
        findings.append(Finding("code-blocks", "%d code blocks, max %d" % (len(parsed.code_blocks), max_code_blocks)))

    for index, block in enumerate(parsed.code_blocks, 1):
        if block.lines > max_code_lines:
            findings.append(Finding("code-lines", "code block %d has %d lines, max %d" % (
                index, block.lines, max_code_lines), block.line))

    for line in parsed.unclosed_fences:
        findings.append(Finding("fence", "code fence is never closed", line))

    if parsed.images < min_images:
        findings.append(Finding("images-min", "%d image%s, min %d (short by %d)" % (
            parsed.images, "" if parsed.images == 1 else "s", min_images, min_images - parsed.images)))
    if parsed.images > max_images:
        findings.append(Finding("images-max", "%d images, max %d (over by %d)" % (
            parsed.images, max_images, parsed.images - max_images)))

    if not any(action.search(h) for h in parsed.headings):
        findings.append(Finding("action-heading", "no section heading matches /%s/i; end with a call-to-action section "
                                                  "(next step)" % safe(action_heading)))

    if parsed.markdown_link_lines:
        findings.append(Finding("markdown-link", "%d leftover Markdown link(s) (\"](http\") in the HTML article; "
                                                 "convert them to <a href> links" % len(parsed.markdown_link_lines),
                                parsed.markdown_link_lines[0]))

    matching = next((h for h in parsed.headings if action.search(h)), "-")
    summary = "article format=%s title=%s/%d subtitle=%s/%d words=%d/%d code_blocks=%d/%d longest_code=%d/%d " \
              "images=%d[%d-%d] action_heading=\"%s\"" % (
                  fmt,
                  "-" if shown_title is None else len(shown_title), TITLE_MAX_CHARS,
                  "-" if shown_subtitle is None else len(shown_subtitle), SUBTITLE_MAX_CHARS,
                  parsed.words, max_words,
                  len(parsed.code_blocks), max_code_blocks,
                  max((b.lines for b in parsed.code_blocks), default=0), max_code_lines,
                  parsed.images, min_images, max_images,
                  safe(matching))
    return Report(findings, summary)


# ------------------------------------------------------------------------ profile


_PROFILE_FENCE = re.compile(r"^ {0,3}(?P<fence>`{3,}|~{3,})[ \t]*(?P<info>.*)$")


def first_json_block(text: str) -> Optional[Tuple[int, str]]:
    """(line of the opening fence, content) of the first fenced block tagged ``json``, else None.

    Blocks of other languages are skipped whole, so a ``json`` fence shown inside them
    is not taken. A ``json`` block that is never closed is an input error.
    """
    opened: Optional[Tuple[str, int, bool, int]] = None  # (fence char, length, is json, line)
    buffer: List[str] = []
    for number, line in enumerate(normalise_newlines(text).split("\n"), 1):
        m = _PROFILE_FENCE.match(line)
        if opened is None:
            if m and not (m.group("fence")[0] == "`" and "`" in m.group("info")):
                words = m.group("info").split()
                opened = (m.group("fence")[0], len(m.group("fence")), bool(words) and words[0].lower() == "json", number)
                buffer = []
            continue
        if m and m.group("fence")[0] == opened[0] and len(m.group("fence")) >= opened[1] and not m.group("info").strip():
            if opened[2]:
                return opened[3], "\n".join(buffer)
            opened = None
        else:
            buffer.append(line)
    if opened is not None and opened[2]:
        raise InputError("the json block opened on line %d is never closed" % opened[3])
    return None


def parse_profile(text: str, section: str) -> Dict[str, int]:
    """The limits one profile sets for ``section`` ("post" or "article"); unknown keys are ignored."""
    block = first_json_block(text)
    if block is None:
        raise InputError("no fenced json block found; add one with ```json ... ``` holding the settings")
    start, body = block
    try:
        data = json.loads(body)
    except ValueError as exc:
        line = getattr(exc, "lineno", 1)
        raise InputError("malformed json in the first json block (line %d, column %d): %s" % (
            start + line, getattr(exc, "colno", 1), safe(getattr(exc, "msg", str(exc)))))
    if not isinstance(data, dict):
        raise InputError("the json block must be an object with \"post\" and \"article\" sections")
    values = data.get(section)
    if values is None:
        return {}
    if not isinstance(values, dict):
        raise InputError("\"%s\" must be an object" % section)
    limits: Dict[str, int] = {}
    for key in DEFAULTS[section]:
        if key not in values:
            continue
        value = values[key]
        if type(value) is not int or value < 0:
            raise InputError("\"%s.%s\" must be a whole number of 0 or more, got %s" % (
                section, key, safe(json.dumps(value))[:40]))
        limits[key] = value
    return limits


def resolve_limits(args: argparse.Namespace) -> Dict[str, int]:
    """Every limit of the subcommand: explicit flag, else profile, else built-in default."""
    section = args.command
    from_profile: Dict[str, int] = {}
    if args.profile is not None:
        text = read_text(args.profile, "profile")
        try:
            from_profile = parse_profile(text, section)
        except InputError as exc:
            raise InputError("profile %s: %s" % (safe(args.profile), exc))
    limits: Dict[str, int] = {}
    for key, default in DEFAULTS[section].items():
        flag = getattr(args, key)
        limits[key] = flag if flag is not None else from_profile.get(key, default)
    return limits


# ---------------------------------------------------------------------------- CLI


def non_negative(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("not an integer: %s" % safe(value))
    if number < 0:
        raise argparse.ArgumentTypeError("must be 0 or more: %s" % safe(value))
    return number


def non_empty(value: str) -> str:
    if not value.strip():
        raise argparse.ArgumentTypeError("must not be empty")
    return value


def alias_pair(value: str) -> Tuple[str, str]:
    tag, sep, phrase = value.partition("=")
    if not sep or not tag.lstrip("#").strip() or not words_of(phrase):
        raise argparse.ArgumentTypeError("expected TAG=PHRASE, got: %s" % safe(value))
    return tag_key(tag.strip()), phrase.strip()


def regex_text(value: str) -> str:
    try:
        re.compile(value, re.I)
    except re.error as exc:
        raise argparse.ArgumentTypeError("invalid regular expression %s: %s" % (safe(value), safe(str(exc))))
    return value


def add_limit(parser: argparse.ArgumentParser, section: str, key: str, help_text: str) -> None:
    parser.add_argument("--" + key.replace("_", "-"), type=non_negative, default=None, metavar="N",
                        help="%s (profile key %s.%s; default %d)" % (help_text, section, key, DEFAULTS[section][key]))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_publication.py",
        description="Check the publishing shape of a study LinkedIn post or Medium article "
        "(exit 0 ok, 1 rule failure, 2 usage or input error; any non-zero exit: do not publish).",
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="{post,article}")
    profile_help = ("Markdown file whose first ```json block sets the limits; a flag overrides the profile, "
                    "the profile overrides the default")

    post = sub.add_parser("post", help="check a plain-text LinkedIn post",
                          description="Check a plain-text LinkedIn post: length, hashtags, hook, links, hashtag topics.")
    post.add_argument("file", metavar="FILE", help="plain-text post")
    post.add_argument("--profile", type=non_empty, metavar="PATH", help=profile_help)
    add_limit(post, "post", "max_chars", "total characters")
    add_limit(post, "post", "max_hashtags", "hashtags")
    add_limit(post, "post", "hook_chars", "characters before the first blank line")
    post.add_argument("--require-link", action="append", default=[], type=non_empty, metavar="URL",
                      help="URL the post must contain (repeatable)")
    post.add_argument("--alias", action="append", default=[], type=alias_pair, metavar="TAG=PHRASE",
                      help="extra phrase that backs a hashtag, e.g. OOP=object-oriented (repeatable)")
    post.add_argument("--forbid", action="append", default=[], type=non_empty, metavar="TERM",
                      help="term that must not appear in the hook, case-insensitive (repeatable)")

    article = sub.add_parser("article", help="check a Markdown or HTML article",
                             description="Check a Markdown or HTML article: title, subtitle, words, code blocks, "
                                         "images, next-step section.")
    article.add_argument("file", metavar="FILE", help="Markdown (.md) or HTML (.html) article; a trailing .txt is ignored")
    article.add_argument("--profile", type=non_empty, metavar="PATH", help=profile_help)
    article.add_argument("--title", type=non_empty, metavar="TEXT", help="title to check instead of the first H1")
    article.add_argument("--subtitle", metavar="TEXT", help="subtitle to check (optional)")
    article.add_argument("--forbid-title", action="append", default=[], type=non_empty, metavar="TERM",
                         help="term that must not appear in the title or subtitle, e.g. the pattern name (repeatable)")
    add_limit(article, "article", "max_words", "body words")
    add_limit(article, "article", "max_code_blocks", "code blocks")
    add_limit(article, "article", "max_code_lines", "lines per code block")
    add_limit(article, "article", "min_images", "minimum images, Markdown ![](...) or HTML <img>")
    add_limit(article, "article", "max_images", "maximum images")
    article.add_argument("--action-heading", type=regex_text, default=DEFAULT_ACTION_HEADING, metavar="REGEX",
                         help="regex a section heading must match, case-insensitive (default \"next step\")")
    return parser


def read_text(name: str, what: str) -> str:
    """A UTF-8 file (a BOM is dropped); a missing, unreadable, undecodable or empty file is an InputError."""
    try:
        text = Path(name).read_text(encoding="utf-8-sig")
    except UnicodeError:
        raise InputError("%s is not valid UTF-8 text (save it as UTF-8, not UTF-16): %s" % (what, safe(name)))
    except OSError as exc:
        raise InputError("cannot read %s %s: %s" % (what, safe(name), safe(exc.strerror or str(exc))))
    if not text.strip():
        raise InputError("empty %s: %s" % (what, safe(name)))
    return text


def write_report(name: str, report: Report, out: TextIO) -> int:
    for finding in report.findings:
        where = "%s:%d" % (safe(name), finding.line) if finding.line else safe(name)
        out.write("violation: %s: %s: %s\n" % (where, finding.rule, finding.message))
    if not report.findings:
        out.write("ok: %s: %s\n" % (safe(name), report.summary))
    return 1 if report.findings else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
        limits = resolve_limits(args)
        if args.command == "article" and limits["min_images"] > limits["max_images"]:
            parser.error("minimum images (%d) is larger than maximum images (%d); check --min-images, --max-images "
                         "and the profile" % (limits["min_images"], limits["max_images"]))
        text = read_text(args.file, "file")
    except SystemExit as exc:  # argparse exits 0 for --help and 2 for usage errors
        code = exc.code
        return code if isinstance(code, int) else (0 if code is None else 2)
    except InputError as exc:
        sys.stderr.write("error: %s\n" % exc)
        return 2
    if args.command == "post":
        aliases: Dict[str, List[str]] = {}
        for tag, phrase in args.alias:
            aliases.setdefault(tag, []).append(phrase)
        report = check_post(text, limits["max_chars"], limits["max_hashtags"], limits["hook_chars"],
                            args.require_link, aliases, args.forbid)
    else:
        report = check_article(text, detect_format(args.file, text), args.title, args.subtitle, args.forbid_title,
                               limits["max_words"], limits["max_code_blocks"], limits["max_code_lines"],
                               args.action_heading, limits["min_images"], limits["max_images"])
    return write_report(args.file, report, sys.stdout)


if __name__ == "__main__":
    sys.exit(main())
