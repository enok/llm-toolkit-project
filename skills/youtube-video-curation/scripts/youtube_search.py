#!/usr/bin/env python3
"""Curate YouTube explainer videos: search, parse, rank, and verify.

Python 3.9+, standard library only. Subcommands:

  search "<query>" [--limit N] [--json] [--out FILE]
      Fetch a YouTube results page and parse the embedded ytInitialData.
  parse FILE.html [--json] [--out FILE]
      Same parsing, offline, from a saved results page.
  rank FILE.json --language <lang> [--top N] [--json]
      Apply the deterministic ranking rubric (see references/ranking-rubric.md).
  verify ID [ID ...] [--json]
      Confirm each video ID is real through the oEmbed endpoint. An ID that
      starts with "-" works as is (or after `--`).

Exit codes: 0 ok, 1 check failed (no results, an ID did not verify),
2 usage error, file error, or network error.

YouTube is frequently blocked in cloud sandboxes. Run `search` and `verify` on a
machine with normal internet access; `parse` and `rank` work offline.
"""

from __future__ import annotations

import argparse
import http.client
import json
import math
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SEARCH_URL = "https://www.youtube.com/results"
OEMBED_URL = "https://www.youtube.com/oembed"
WATCH_URL = "https://www.youtube.com/watch?v="

# Browser-like headers. The CONSENT/SOCS cookie skips the EU consent interstitial,
# which otherwise replaces the results page and carries no ytInitialData.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Cookie": "CONSENT=YES+1; SOCS=CAI",
}

DEFAULT_TIMEOUT = 30.0
MAX_BYTES = 16 * 1024 * 1024

# Ranking rubric constants (keep in sync with references/ranking-rubric.md).
LENGTH_MIN_SECONDS = 120
LENGTH_MAX_SECONDS = 1800
LENGTH_TARGET_SECONDS = 600
SHORT_MAX_SECONDS = 60
MIN_AGE_YEARS = 0.25
UNKNOWN_AGE_YEARS = 1.0
CHANNEL_POOL_CAP = 3
PREFERRED_CHANNEL_SCORE = 10

OEMBED_DEFINITE_FAILURE_CODES = (400, 401, 404)

# Upper clamp for numeric fields read from JSON, so float math cannot overflow.
MAX_VIEWS = 10 ** 15

# Hosts a response may come from after redirects (consent pages live on google.com).
ALLOWED_HOST_SUFFIXES = (".youtube.com", ".google.com")
ALLOWED_HOSTS = ("youtube.com", "google.com")

# argv marker that protects an ID starting with "-" from argparse (NUL cannot occur in real argv).
DASH_ID_MARK = "\0dash\0"


class ParseError(ValueError):
    """The page or JSON file does not have the expected structure."""


class FetchError(OSError):
    """A response could not be used (for example, it was too large)."""


# --------------------------------------------------------------------------- #
# Small parsers
# --------------------------------------------------------------------------- #


def is_valid_video_id(value) -> bool:
    """True only for an 11-character YouTube ID. fullmatch avoids the `$` newline quirk."""
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_-]{11}", value) is not None


_VIEWS_RE = re.compile(r"^\s*(\d[\d,]*(?:\.\d+)?)\s*(k|m|b|thousand|million|billion)?\b", re.I)
_SUFFIX = {"k": 1e3, "thousand": 1e3, "m": 1e6, "million": 1e6, "b": 1e9, "billion": 1e9}


def parse_views(text):
    """Parse '1,234,567 views', '9.8M views', '1 view', 'No views' into an int, else None."""
    if not isinstance(text, str):
        return None
    lowered = text.strip().lower()
    if lowered.startswith("no views") or lowered.startswith("no watching"):
        return 0
    match = _VIEWS_RE.match(lowered)
    if not match:
        return None
    try:
        number = float(match.group(1).replace(",", ""))
    except ValueError:
        return None
    multiplier = _SUFFIX.get((match.group(2) or "").lower(), 1)
    scaled = number * multiplier
    if not math.isfinite(scaled):
        return None
    return int(round(scaled))


def parse_length(text):
    """Parse '14:32' or '1:02:03' into seconds, else None."""
    if not isinstance(text, str):
        return None
    parts = text.strip().split(":")
    if not 2 <= len(parts) <= 3 or not all(p.isdigit() for p in parts):
        return None
    numbers = [int(p) for p in parts]
    if any(n > 59 for n in numbers[1:]):
        return None
    seconds = 0
    for number in numbers:
        seconds = seconds * 60 + number
    return seconds


_AGE_RE = re.compile(r"(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago", re.I)
_AGE_YEARS = {
    "second": 1 / (365 * 24 * 3600),
    "minute": 1 / (365 * 24 * 60),
    "hour": 1 / (365 * 24),
    "day": 1 / 365,
    "week": 7 / 365,
    "month": 1 / 12,
    "year": 1.0,
}


def parse_age_years(text):
    """Parse '3 years ago' / 'Streamed 5 months ago' into years (float), else None."""
    if not isinstance(text, str):
        return None
    match = _AGE_RE.search(text)
    if not match:
        return None
    return int(match.group(1)) * _AGE_YEARS[match.group(2).lower()]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# ytInitialData extraction and videoRenderer parsing
# --------------------------------------------------------------------------- #

_MARKER_RE = re.compile(
    r"""(?:var\s+ytInitialData\s*=\s*|window\[\s*["']ytInitialData["']\s*\]\s*=\s*)"""
)


def extract_initial_data(html: str) -> dict:
    """Decode the ytInitialData object with raw_decode (no fragile end-of-script regex)."""
    decoder = json.JSONDecoder()
    found_marker = False
    for match in _MARKER_RE.finditer(html):
        found_marker = True
        try:
            data, _end = decoder.raw_decode(html, match.end())
        except (ValueError, RecursionError):
            continue  # a decoy mention such as a comment (or absurd nesting); try the next marker
        if isinstance(data, dict):
            return data
    if found_marker:
        raise ParseError("ytInitialData marker found but its JSON could not be decoded")
    raise ParseError(
        "ytInitialData not found (blocked page, consent page, or YouTube markup change)"
    )


def _text(node) -> str:
    if isinstance(node, str):
        return node
    if isinstance(node, dict):
        simple = node.get("simpleText")
        if isinstance(simple, str):
            return simple
        runs = node.get("runs")
        if isinstance(runs, list):
            return "".join(r.get("text", "") for r in runs if isinstance(r, dict))
    return ""


def iter_video_renderers(data):
    """Yield every videoRenderer dict in document order (iterative walk)."""
    stack = [data]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            renderer = node.get("videoRenderer")
            if isinstance(renderer, dict):
                yield renderer
            stack.extend(reversed(list(node.values())))
        elif isinstance(node, list):
            stack.extend(reversed(node))


def _overlay_status(renderer: dict):
    """Return (style, text) of the time-status overlay, if present."""
    for overlay in renderer.get("thumbnailOverlays") or []:
        status = overlay.get("thumbnailOverlayTimeStatusRenderer") if isinstance(overlay, dict) else None
        if isinstance(status, dict):
            return status.get("style"), _text(status.get("text"))
    return None, ""


def _is_live_renderer(renderer: dict, views_text: str) -> bool:
    if "upcomingEventData" in renderer:
        return True
    if "watching" in views_text.lower():
        return True
    for badge in renderer.get("badges") or []:
        meta = badge.get("metadataBadgeRenderer") if isinstance(badge, dict) else None
        if isinstance(meta, dict) and (
            meta.get("style") == "BADGE_STYLE_TYPE_LIVE_NOW"
            or str(meta.get("label", "")).strip().upper() == "LIVE"
        ):
            return True
    style, _ = _overlay_status(renderer)
    return style == "LIVE"


def video_from_renderer(renderer: dict):
    video_id = renderer.get("videoId")
    if not isinstance(video_id, str) or not video_id:
        return None
    title = _text(renderer.get("title"))
    channel = _text(renderer.get("ownerText")) or _text(renderer.get("longBylineText")) or _text(
        renderer.get("shortBylineText")
    )
    views_text = _text(renderer.get("viewCountText"))
    length_text = _text(renderer.get("lengthText"))
    if not length_text:
        style, overlay_text = _overlay_status(renderer)
        if style in (None, "DEFAULT"):
            length_text = overlay_text.strip()
    snippets = []
    for snippet in renderer.get("detailedMetadataSnippets") or []:
        if isinstance(snippet, dict):
            snippets.append(_text(snippet.get("snippetText")))
    snippets.append(_text(renderer.get("descriptionSnippet")))
    description = " ".join(s.strip() for s in snippets if s and s.strip())

    endpoint = renderer.get("navigationEndpoint") if isinstance(renderer.get("navigationEndpoint"), dict) else {}
    meta = (endpoint.get("commandMetadata") or {}).get("webCommandMetadata") or {}
    nav_url = meta.get("url") if isinstance(meta.get("url"), str) else ""
    watch = endpoint.get("watchEndpoint") if isinstance(endpoint.get("watchEndpoint"), dict) else {}

    length_seconds = parse_length(length_text)
    return {
        "id": video_id,
        "title": title,
        "channel": channel,
        "views": parse_views(views_text),
        "views_text": views_text,
        "published": _text(renderer.get("publishedTimeText")),
        "length": length_text,
        "length_seconds": length_seconds,
        "description": description,
        "is_short": nav_url.startswith("/shorts/")
        or (length_seconds is not None and length_seconds <= SHORT_MAX_SECONDS),
        "is_live": _is_live_renderer(renderer, views_text),
        "is_playlist": bool(watch.get("playlistId")) or nav_url.startswith("/playlist"),
        "url": WATCH_URL + video_id,
    }


def parse_search_html(html: str) -> list:
    """Return the de-duplicated video list from a results page, in page order."""
    data = extract_initial_data(html)
    seen = set()
    videos = []
    attempted = 0
    malformed = 0
    for renderer in iter_video_renderers(data):
        attempted += 1
        try:
            video = video_from_renderer(renderer)
        except (TypeError, AttributeError, ValueError, KeyError):
            malformed += 1  # a changed field shape must not take down the whole page
            continue
        if video is None or video["id"] in seen:
            continue
        seen.add(video["id"])
        videos.append(video)
    if attempted and malformed == attempted:
        raise ParseError("every videoRenderer had unexpected field types (YouTube markup change?)")
    return videos


# --------------------------------------------------------------------------- #
# Networking
# --------------------------------------------------------------------------- #


def is_allowed_url(url: str) -> bool:
    """True for https URLs on youtube.com or google.com hosts only."""
    try:
        parts = urllib.parse.urlsplit(url)
        host = (parts.hostname or "").lower()
    except ValueError:
        return False
    return parts.scheme == "https" and (host in ALLOWED_HOSTS or host.endswith(ALLOWED_HOST_SUFFIXES))


def build_request(url: str) -> urllib.request.Request:
    """Browser-like request. The consent cookie is an *unredirected* header: urllib
    drops those on redirects, so the cookie goes only to the first host contacted."""
    headers = {k: v for k, v in HEADERS.items() if k != "Cookie"}
    request = urllib.request.Request(url, headers=headers)
    if "Cookie" in HEADERS:
        request.add_unredirected_header("Cookie", HEADERS["Cookie"])
    return request


def http_get(url: str, timeout: float) -> str:
    """GET one page. Every transport problem surfaces as OSError (HTTPError included);
    http.client errors such as IncompleteRead become FetchError."""
    request = build_request(url)
    try:
        response = urllib.request.urlopen(request, timeout=timeout)
    except urllib.error.HTTPError as exc:
        try:
            exc.close()  # release the socket; fp may be absent on hand-built errors
        except Exception:  # pragma: no cover - depends on the Python version
            pass
        raise
    except http.client.HTTPException as exc:
        raise FetchError("%s: %s" % (type(exc).__name__, exc))
    try:
        final_url = getattr(response, "geturl", lambda: None)()
        if isinstance(final_url, str) and not is_allowed_url(final_url):
            raise FetchError("redirected to an unexpected host: %s" % urllib.parse.urlsplit(final_url).hostname)
        data = response.read(MAX_BYTES + 1)
    except http.client.HTTPException as exc:  # IncompleteRead, BadStatusLine, ...
        raise FetchError("%s: %s" % (type(exc).__name__, exc))
    finally:
        response.close()
    if len(data) > MAX_BYTES:
        raise FetchError("response larger than %d bytes" % MAX_BYTES)
    return data.decode("utf-8", "replace")


def search_url(query: str) -> str:
    return SEARCH_URL + "?hl=en&gl=US&search_query=" + urllib.parse.quote(query)


def oembed_url(video_id: str) -> str:
    return OEMBED_URL + "?format=json&url=" + urllib.parse.quote(WATCH_URL + video_id, safe="")


def verify_id(video_id: str, timeout: float = DEFAULT_TIMEOUT) -> dict:
    """Check one ID. Invalid-format IDs never reach the network."""
    result = {"id": video_id, "ok": False, "title": "", "channel": "", "error": "", "network_error": False}
    if not is_valid_video_id(video_id):
        result["error"] = "invalid id format (expected 11 characters of [A-Za-z0-9_-])"
        return result
    result["url"] = WATCH_URL + video_id
    try:
        body = http_get(oembed_url(video_id), timeout)
    except urllib.error.HTTPError as exc:  # must precede URLError/OSError
        if exc.code in OEMBED_DEFINITE_FAILURE_CODES:
            reason = "not found or private" if exc.code == 404 else "embedding disabled or unavailable"
            result["error"] = "HTTP %d (%s)" % (exc.code, reason)
        else:
            result["network_error"] = True
            result["error"] = "HTTP %d (endpoint unreachable or blocked)" % exc.code
        return result
    except OSError as exc:  # URLError, timeouts, FetchError
        result["network_error"] = True
        result["error"] = "network error: %s" % str(getattr(exc, "reason", exc))[:120]
        return result
    try:
        payload = json.loads(body)
        result["title"] = str(payload["title"])
        result["channel"] = str(payload["author_name"])
    except (ValueError, KeyError, TypeError):
        result["error"] = "unexpected oEmbed payload"
        return result
    result["ok"] = True
    return result


# --------------------------------------------------------------------------- #
# Ranking
# --------------------------------------------------------------------------- #

LANGUAGE_ALIASES = {
    "py": "python",
    "js": "javascript",
    "ecmascript": "javascript",
    "node": "javascript",
    "nodejs": "javascript",
    "ts": "typescript",
    "golang": "go",
    "c#": "csharp",
    "cs": "csharp",
    "c++": "cpp",
    "kt": "kotlin",
}

LANGUAGE_TERMS = {
    "python": ["python"],
    "javascript": ["javascript", "ecmascript", "node.js", "nodejs", "js"],
    "typescript": ["typescript", "ts"],
    "java": ["java"],
    "csharp": ["c#", "csharp", "c sharp"],
    "cpp": ["c++", "cpp"],
    "go": ["golang", "go language", "in go"],
    "rust": ["rust"],
    "kotlin": ["kotlin"],
    "swift": ["swift"],
    "ruby": ["ruby"],
    "php": ["php"],
    "scala": ["scala"],
    "dart": ["dart"],
}
# "go" is too ambiguous in prose to count as a conflicting language.
CONFLICT_EXCLUDED = {"go"}

CODE_WORDS_RE = re.compile(
    r"\b(code|coding|implementation|implementing|implement|example|examples|tutorial|"
    r"programming|hands-on|walkthrough|project|build|building)\b",
    re.I,
)

NON_ENGLISH_MARKERS_RE = re.compile(
    r"\b(hindi|espanol|español|portugues|português|deutsch|francais|français|bangla|tamil|"
    r"telugu|urdu|arabic|turkce|türkçe|bahasa)\b",
    re.I,
)


def canonical_language(language: str) -> str:
    name = language.strip().lower()
    return LANGUAGE_ALIASES.get(name, name)


def _term_pattern(term: str):
    return re.compile(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])")


def language_patterns(language: str) -> list:
    canonical = canonical_language(language)
    terms = LANGUAGE_TERMS.get(canonical, [canonical])
    return [_term_pattern(t) for t in terms]


def _mentions(patterns, text: str) -> bool:
    lowered = text.lower()
    return any(p.search(lowered) for p in patterns)


def conflicting_languages(title: str, requested: str) -> list:
    """Other known languages named in the title when the requested one is not."""
    canonical = canonical_language(requested)
    if _mentions(language_patterns(canonical), title):
        return []
    found = []
    for name in LANGUAGE_TERMS:
        if name == canonical or name in CONFLICT_EXCLUDED:
            continue
        if _mentions([_term_pattern(t) for t in LANGUAGE_TERMS[name]], title):
            found.append(name)
    return found


def looks_non_english(title: str) -> bool:
    letters = [c for c in title if c.isalpha()]
    if not letters:
        return False
    non_latin = sum(1 for c in letters if ord(c) > 0x24F)
    if non_latin / len(letters) > 0.3:
        return True
    return NON_ENGLISH_MARKERS_RE.search(title) is not None


def language_tier(item: dict, patterns) -> int:
    """3 language+code words in title/snippet, 2 language in title, 1 language in snippet, 0 none."""
    title = item.get("title") or ""
    description = item.get("description") or ""
    in_title = _mentions(patterns, title)
    in_description = _mentions(patterns, description)
    has_code_word = bool(CODE_WORDS_RE.search(title) or CODE_WORDS_RE.search(description))
    if in_title and has_code_word:
        return 3
    if in_title:
        return 2
    if in_description:
        return 1
    return 0


def views_per_year(item: dict) -> float:
    views = item.get("views") or 0
    age = parse_age_years(item.get("published") or "")
    if age is None:
        age = UNKNOWN_AGE_YEARS
    return views / max(age, MIN_AGE_YEARS)


def views_bucket(per_year: float) -> int:
    """Half-decade buckets so channel and length can decide among comparable videos."""
    return int(math.floor(math.log10(per_year + 1) * 2))


def _finite_int(value):
    """int(value) for a real, finite JSON number; None for bool, text, NaN, or Infinity."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return int(value)


def normalize_item(raw) -> dict:
    """Accept parser output or older hand-written/one-off JSON (string views and length).

    Odd numerics never abort a ranking: a negative ("unknown" sentinel), NaN, or
    Infinity count is treated as unknown, and huge counts are clamped."""
    if not isinstance(raw, dict):
        raise ParseError("result entries must be JSON objects")
    views_raw = raw.get("views")
    views_text = str(raw.get("views_text") or "")
    if isinstance(views_raw, str):
        views_text = views_text or views_raw
        views = parse_views(views_raw)
    else:
        views = _finite_int(views_raw)
        if views is None:
            views = parse_views(views_text)
    if views is not None:
        views = None if views < 0 else min(views, MAX_VIEWS)
    length = str(raw.get("length") or "")
    length_seconds = _finite_int(raw.get("length_seconds"))
    if length_seconds is None or length_seconds < 0:
        length_seconds = parse_length(length)
    video_id = raw.get("id") if isinstance(raw.get("id"), str) else (raw.get("videoId") or "")
    return {
        "id": str(video_id),
        "title": str(raw.get("title") or ""),
        "channel": str(raw.get("channel") or ""),
        "views": views,
        "views_text": views_text,
        "published": str(raw.get("published") or ""),
        "length": length,
        "length_seconds": length_seconds,
        "description": str(raw.get("description") or ""),
        "is_short": bool(raw.get("is_short")),
        "is_live": bool(raw.get("is_live")),
        "is_playlist": bool(raw.get("is_playlist")),
        "url": str(raw.get("url") or (WATCH_URL + str(video_id))),
    }


def disqualification_reasons(item: dict, language: str, allow_non_english: bool) -> list:
    reasons = []
    if not is_valid_video_id(item["id"]):
        reasons.append("invalid-id")
    length_seconds = item["length_seconds"]
    if (
        item["is_short"]
        or "#shorts" in item["title"].lower()
        or (length_seconds is not None and length_seconds <= SHORT_MAX_SECONDS)
    ):
        reasons.append("short")
    if item["is_live"] or "watching" in item["views_text"].lower():
        reasons.append("live")
    if item["is_playlist"] or "/playlist" in item["url"]:
        reasons.append("playlist")
    if not allow_non_english and looks_non_english(item["title"]):
        reasons.append("non-english")
    for other in conflicting_languages(item["title"], language):
        reasons.append("other-code-language:" + other)
    return reasons


def rank_results(items, language: str, allow_non_english: bool = False, preferred_channels=()):
    """Return (ranked, disqualified). Pure and deterministic: same input, same order."""
    normalized = []
    seen = set()
    for raw in items:
        item = normalize_item(raw)
        key = item["id"] or ("title:" + item["title"])
        if key in seen:
            continue
        seen.add(key)
        normalized.append(item)

    patterns = language_patterns(language)
    preferred = {c.strip().lower() for c in preferred_channels if c.strip()}
    qualified = []
    disqualified = []
    for item in normalized:
        reasons = disqualification_reasons(item, language, allow_non_english)
        if reasons:
            disqualified.append(dict(item, reasons=reasons))
        else:
            qualified.append(item)

    pool = Counter(i["channel"].strip().lower() for i in qualified if i["channel"].strip())
    scored = []
    for item in qualified:
        channel_key = item["channel"].strip().lower()
        per_year = views_per_year(item)
        length_seconds = item["length_seconds"]
        length_ok = length_seconds is not None and LENGTH_MIN_SECONDS <= length_seconds <= LENGTH_MAX_SECONDS
        score = {
            "language_tier": language_tier(item, patterns),
            "views_per_year": int(round(per_year)),
            "views_bucket": views_bucket(per_year),
            "channel_score": PREFERRED_CHANNEL_SCORE
            if channel_key in preferred
            else min(pool.get(channel_key, 0), CHANNEL_POOL_CAP),
            "length_ok": bool(length_ok),
            "was_stream": item["published"].strip().lower().startswith("streamed"),
        }
        distance = abs(length_seconds - LENGTH_TARGET_SECONDS) if length_seconds is not None else 10 ** 9
        sort_key = (
            -score["language_tier"],
            -score["views_bucket"],
            -score["channel_score"],
            -int(score["length_ok"]),
            int(score["was_stream"]),
            distance,
            -(item["views"] or 0),
            item["id"],
        )
        scored.append((sort_key, dict(item, score=score)))
    scored.sort(key=lambda pair: pair[0])
    ranked = []
    for position, (_key, entry) in enumerate(scored, start=1):
        entry["rank"] = position
        ranked.append(entry)
    return ranked, disqualified


# --------------------------------------------------------------------------- #
# File and output helpers
# --------------------------------------------------------------------------- #


def read_text_file(path: Path) -> str:
    """Read text robustly: UTF-8 (with or without BOM) or UTF-16 (Windows PowerShell `>`)."""
    data = path.read_bytes()
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        return data.decode("utf-16", "replace")
    return data.decode("utf-8-sig", "replace")


def write_json_file(path: Path, payload) -> None:
    # write_bytes: Path.write_text(newline=...) needs Python 3.10, and this keeps LF on Windows.
    path.write_bytes((json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))


def load_results(path: Path):
    """Load a results file: a list, {"results": [...]}, or {query: [...], ...}."""
    try:
        payload = json.loads(read_text_file(path))
    except (ValueError, RecursionError) as exc:
        raise ParseError("%s is not valid JSON: %s" % (path, exc))
    meta = {}
    if isinstance(payload, list):
        items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        items = payload["results"]
        meta = {k: payload[k] for k in ("query", "pulled_at") if k in payload}
    elif isinstance(payload, dict) and all(isinstance(v, list) for v in payload.values()) and payload:
        items = [entry for value in payload.values() for entry in value]
    else:
        raise ParseError("unexpected JSON shape in %s (expected a list or an object with 'results')" % path)
    return items, meta


def format_item(item: dict, index=None) -> str:
    prefix = "%2d. " % index if index is not None else ""
    return "%s%s  %s | %s | %s | %s | %s" % (
        prefix,
        item["id"],
        item["title"],
        item["channel"] or "?",
        item["length"] or "?",
        item["views_text"] or "?",
        item["published"] or "?",
    )


def _positive_int(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be >= 1")
    return number


def _positive_float(value: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number <= 0:
        raise argparse.ArgumentTypeError("must be a finite number > 0")
    return number


def _err(message: str) -> None:
    print("error: " + message, file=sys.stderr)


BLOCKED_HINT = (
    "hint: YouTube is often blocked in cloud sandboxes; run this command on the user's machine."
)


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #


def _emit_results(videos: list, envelope: dict, as_json: bool, out) -> int:
    # Never replace a curated --out file with an empty result.
    wrote = bool(out) and bool(videos)
    if wrote:
        write_json_file(Path(out), envelope)
    if as_json:
        print(json.dumps(envelope, indent=2, ensure_ascii=False))
    else:
        for index, video in enumerate(videos, start=1):
            print(format_item(video, index))
        if wrote:
            print("wrote %d results to %s" % (len(videos), out))
    if not videos:
        _err("no videos found in the page" + ("; %s left untouched" % out if out else ""))
        return 1
    return 0


def cmd_search(args) -> int:
    try:
        html = http_get(search_url(args.query), args.timeout)
    except OSError as exc:
        _err("could not fetch search results: %s" % str(getattr(exc, "reason", exc))[:160])
        print(BLOCKED_HINT, file=sys.stderr)
        return 2
    try:
        videos = parse_search_html(html)[: args.limit]
    except ParseError as exc:
        _err(str(exc))
        print(BLOCKED_HINT, file=sys.stderr)
        return 2
    envelope = {"query": args.query, "pulled_at": utc_now_iso(), "results": videos}
    return _emit_results(videos, envelope, args.json, args.out)


def cmd_parse(args) -> int:
    path = Path(args.file)
    try:
        html = read_text_file(path)
        videos = parse_search_html(html)[: args.limit]
    except (OSError, ParseError) as exc:
        _err(str(exc))
        return 2
    saved = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    envelope = {"source": path.name, "pulled_at": saved, "results": videos}
    return _emit_results(videos, envelope, args.json, args.out)


def cmd_rank(args) -> int:
    try:
        items, meta = load_results(Path(args.file))
        ranked, disqualified = rank_results(
            items,
            args.language,
            allow_non_english=args.allow_non_english,
            preferred_channels=args.prefer_channel or [],
        )
    except (OSError, ParseError) as exc:
        _err(str(exc))
        return 2
    top = ranked[: args.top]
    if args.json:
        print(
            json.dumps(
                {
                    "language": canonical_language(args.language),
                    "pulled_at": meta.get("pulled_at"),
                    "ranked": top,
                    "disqualified": disqualified,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if top else 1
    print(
        "Ranked for language=%s (pulled %s; %d candidates, %d qualified)"
        % (
            canonical_language(args.language),
            meta.get("pulled_at") or "unknown",
            len(ranked) + len(disqualified),
            len(ranked),
        )
    )
    for entry in top:
        score = entry["score"]
        print(format_item(entry, entry["rank"]))
        print(
            "      lang_tier=%d views/yr=%s channel=%d length=%s%s  %s"
            % (
                score["language_tier"],
                format(score["views_per_year"], ","),
                score["channel_score"],
                "ok" if score["length_ok"] else "outside-2-30min",
                " stream" if score["was_stream"] else "",
                entry["url"],
            )
        )
    if disqualified:
        print(
            "Disqualified (%d): %s"
            % (len(disqualified), "; ".join("%s %s" % (d["id"], ",".join(d["reasons"])) for d in disqualified))
        )
    if not top:
        _err("no qualified candidates")
        return 1
    print("Next: confirm the code and audio by eye, then run `verify <id> ...` on the winner and backups.")
    return 0


def cmd_verify(args) -> int:
    results = [verify_id(video_id, args.timeout) for video_id in args.ids]
    verified_at = utc_now_iso()
    if args.json:
        print(json.dumps({"verified_at": verified_at, "results": results}, indent=2, ensure_ascii=False))
    else:
        for result in results:
            if result["ok"]:
                print("OK    %s  %s | %s" % (result["id"], result["title"], result["channel"]))
            else:
                print("FAIL  %s  %s" % (result["id"], result["error"]))
        print("verified_at: " + verified_at)
    if any(r["network_error"] for r in results):
        _err("could not reach the oEmbed endpoint for at least one ID; nothing can be claimed verified")
        print(BLOCKED_HINT, file=sys.stderr)
        return 2
    return 0 if all(r["ok"] for r in results) else 1


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtube_search.py",
        description="Search, parse, rank, and verify YouTube explainer videos (stdlib only).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_output(p):
        p.add_argument("--json", action="store_true", help="print JSON instead of text")
        p.add_argument("--out", metavar="FILE", help="also write the JSON envelope to FILE (UTF-8)")

    p_search = sub.add_parser("search", help="fetch and parse a YouTube results page")
    p_search.add_argument("query")
    p_search.add_argument("--limit", type=_positive_int, default=10)
    p_search.add_argument("--timeout", type=_positive_float, default=DEFAULT_TIMEOUT)
    add_output(p_search)
    p_search.set_defaults(func=cmd_search)

    p_parse = sub.add_parser("parse", help="parse a saved results page offline")
    p_parse.add_argument("file", metavar="FILE.html")
    p_parse.add_argument("--limit", type=_positive_int, default=1000)
    add_output(p_parse)
    p_parse.set_defaults(func=cmd_parse)

    p_rank = sub.add_parser("rank", help="rank parsed results with the rubric")
    p_rank.add_argument("file", metavar="FILE.json")
    p_rank.add_argument("--language", required=True, help="requested code language, e.g. java, python")
    p_rank.add_argument("--top", type=_positive_int, default=5)
    p_rank.add_argument("--prefer-channel", action="append", metavar="NAME", help="trusted channel (repeatable)")
    p_rank.add_argument("--allow-non-english", action="store_true", help="do not disqualify non-English titles")
    p_rank.add_argument("--json", action="store_true", help="print JSON instead of text")
    p_rank.set_defaults(func=cmd_rank)

    p_verify = sub.add_parser(
        "verify",
        help="verify video IDs through oEmbed",
        description='Verify video IDs through oEmbed. An ID that starts with "-" is accepted as is; '
        "after `--` every argument is an ID.",
    )
    p_verify.add_argument("ids", nargs="+", metavar="ID")
    p_verify.add_argument("--timeout", type=_positive_float, default=DEFAULT_TIMEOUT)
    p_verify.add_argument("--json", action="store_true", help="print JSON instead of text")
    p_verify.set_defaults(func=cmd_verify)
    return parser


def protect_dash_ids(argv) -> list:
    """About 1 in 64 real IDs starts with "-", which argparse reads as an option.
    For `verify`, mark such tokens so they parse as positionals (before any `--`)."""
    tokens = list(argv)
    if not tokens or tokens[0] != "verify":
        return tokens
    protected = [tokens[0]]
    after_separator = False
    for previous, token in zip(tokens, tokens[1:]):
        if token == "--":
            after_separator = True
        elif not after_separator and previous != "--timeout" and re.fullmatch(r"-[A-Za-z0-9_-]{10}", token):
            token = DASH_ID_MARK + token
        protected.append(token)
    return protected


def main(argv=None) -> int:
    # Titles may hold characters the Windows console codepage cannot encode.
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(errors="replace")
            except (OSError, ValueError):
                pass
    parser = build_parser()
    try:
        args = parser.parse_args(protect_dash_ids(sys.argv[1:] if argv is None else argv))
    except SystemExit as exc:  # argparse exits 2 on usage errors and 0 on --help
        return int(exc.code) if isinstance(exc.code, int) else 2
    if args.command == "verify":
        args.ids = [i[len(DASH_ID_MARK):] if i.startswith(DASH_ID_MARK) else i for i in args.ids]
    try:
        return args.func(args)
    except OSError as exc:
        _err(str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
