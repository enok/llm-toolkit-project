#!/usr/bin/env python3
"""Run-log tooling for the run-retrospective skill (workflow self-improvement loop).

Validates, appends to, and analyses a JSON Lines log of workflow run records
(schema 1, one object per line). Python 3.9+, standard library only.

Usage:
  run_retro.py validate   [--log PATH]
  run_retro.py append     --record FILE|-  [--log PATH]
  run_retro.py summary    [--workflow NAME] [--window N=5] [--json] [--log PATH]
  run_retro.py candidates [--threshold N=2] [--json] [--log PATH]
  run_retro.py preflight  --workflow NAME [--limit N=5] [--include-global] [--log PATH]
  run_retro.py signatures [--workflow NAME] [--json] [--log PATH]

Log location: --log PATH, else env LLM_RUN_LOG, else ~/.llm-toolkit/run-log.jsonl.
Exit codes: 0 ok, 1 validation/check failed, 2 usage or IO error. Invalid input
(deeply nested JSON, lone surrogates, oversized lines) is a validation error, never a traceback.
`validate` and `append` also print non-fatal "warning:" lines on stderr for likely
under-reporting (exit code unchanged); see underreporting_warnings.

Pure functions for reuse and tests: validate_record, load_records, summarize,
find_candidates, preflight, list_signatures (plus generate_run_id, resolve_log_path,
append_record, underreporting_warnings).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import date as _date
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

SCHEMA_VERSION = 1
MAX_LINE_BYTES = 8 * 1024
ENV_LOG = "LLM_RUN_LOG"
DEFAULT_WINDOW = 5
DEFAULT_THRESHOLD = 2
DEFAULT_LIMIT = 5
TOP_RECURRING = 10

OUTCOMES = ("success", "partial", "failed", "escalated", "abandoned")
CATEGORIES = (
    "spec-gap",
    "wrong-assumption",
    "env-constraint",
    "tool-misuse",
    "platform-quirk",
    "quality-defect",
    "validation-gap",
    "tier-misassignment",
    "scope-drift",
    "coordination",
    "safety-near-miss",
)
SEVERITIES = ("low", "medium", "high", "critical")
SEVERE_SEVERITIES = ("high", "critical")
SOURCES = ("self-review", "validator", "ci", "user", "tool-error", "post-release")
LEVELS = ("learning", "checklist", "guard", "rule")  # ladder order, lowest first
LEVEL_RANK = {level: rank for rank, level in enumerate(LEVELS, start=1)}

METRIC_KEYS = ("tasks", "first_pass", "iterations", "user_corrections", "escaped_defects", "tool_errors")
REQUIRED_KEYS = ("schema", "date", "workflow", "outcome", "metrics", "mistakes", "promotions")
OPTIONAL_KEYS = ("run_id", "agent", "task_shape", "notes")
MISTAKE_KEYS = ("signature", "category", "severity", "source", "summary", "fix", "prevented_by")
PROMOTION_KEYS = ("signature", "level", "asset")

MAX_SIGNATURE = 80
MAX_SUMMARY = 200
MAX_FIX = 200
MAX_TASK_SHAPE = 120
MAX_NOTES = 500
MAX_RUN_ID = 128
MAX_WORKFLOW = 80  # date(10) + workflow + hash(6) + 2 hyphens stays well under MAX_RUN_ID

DATE_RE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
KEBAB_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
SIGNATURE_RE = re.compile(r"[a-z-]+/[a-z0-9]+(?:-[a-z0-9]+)*")
DRIVE_RE = re.compile(r"[A-Za-z]:")

PRIVACY_PATTERNS = (
    ("an email address", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("an AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("a GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}")),
    ("a Slack token", re.compile(r"xox[abpr]-")),
    ("a private key block", re.compile(r"-----BEGIN")),
    ("a credential assignment", re.compile(r"(?i)(password|secret|token)\s*[:=]\s*\S+")),
    ("a URL with a query string", re.compile(r"[A-Za-z][A-Za-z0-9+.-]*://\S*\?")),
)

Record = Dict[str, Any]


# --------------------------------------------------------------------------- validation


def _is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _safe(text: str) -> str:
    """Escape lone surrogates so a message is always printable and encodable."""
    return text.encode("utf-8", "backslashreplace").decode("utf-8")


def _one_of(values: Iterable[str]) -> str:
    return ", ".join(values)


def _check_keys(obj: Dict[str, Any], required: Tuple[str, ...], optional: Tuple[str, ...], path: str, errors: List[str]) -> None:
    prefix = path + ": " if path else ""
    for key in required:
        if key not in obj:
            errors.append("%smissing required key '%s'" % (prefix, key))
    allowed = set(required) | set(optional)
    for key in sorted(str(k) for k in obj):
        if key not in allowed:
            errors.append("%sunknown key '%s'" % (prefix, _safe(key)))


def _check_text(errors: List[str], path: str, value: Any, max_len: Optional[int], allow_empty: bool = True) -> None:
    if not isinstance(value, str):
        errors.append("%s: must be a string" % path)
    elif not allow_empty and not value.strip():
        errors.append("%s: must not be empty" % path)
    elif max_len is not None and len(value) > max_len:
        errors.append("%s: must be at most %d characters (got %d)" % (path, max_len, len(value)))


def _check_enum(errors: List[str], path: str, value: Any, allowed: Tuple[str, ...]) -> bool:
    if isinstance(value, str) and value in allowed:
        return True
    errors.append("%s: must be one of %s" % (path, _one_of(allowed)))
    return False


def asset_path_error(value: Any) -> Optional[str]:
    """Return why `value` is not an acceptable repo-relative path, or None."""
    if not isinstance(value, str):
        return "must be a string"
    if not value.strip():
        return "must not be empty"
    if DRIVE_RE.match(value):
        return "must be repo-relative (no drive letter)"
    if value.startswith("/"):
        return "must be repo-relative (no leading '/')"
    if "\\" in value:
        return "must use forward slashes"
    if any(segment == ".." for segment in value.split("/")):
        return "must not contain '..'"
    return None


def _check_signature(errors: List[str], path: str, value: Any) -> bool:
    if not isinstance(value, str):
        errors.append("%s: must be a string" % path)
    elif len(value) > MAX_SIGNATURE:
        errors.append("%s: must be at most %d characters (got %d)" % (path, MAX_SIGNATURE, len(value)))
    elif not SIGNATURE_RE.fullmatch(value):
        errors.append("%s: must match <category>/<kebab-slug> (lowercase, e.g. spec-gap/missing-criterion)" % path)
    else:
        return True
    return False


def _validate_mistake(item: Any, path: str, errors: List[str]) -> None:
    if not isinstance(item, dict):
        errors.append("%s: must be an object" % path)
        return
    _check_keys(item, MISTAKE_KEYS, (), path, errors)
    signature_ok = "signature" in item and _check_signature(errors, path + ".signature", item["signature"])
    if "category" in item:
        category = item["category"]
        if _check_enum(errors, path + ".category", category, CATEGORIES) and signature_ok:
            prefix = item["signature"].split("/", 1)[0]
            if prefix != category:
                errors.append("%s.category: must equal the signature prefix '%s'" % (path, prefix))
    if "severity" in item:
        _check_enum(errors, path + ".severity", item["severity"], SEVERITIES)
    if "source" in item:
        _check_enum(errors, path + ".source", item["source"], SOURCES)
    if "summary" in item:
        _check_text(errors, path + ".summary", item["summary"], MAX_SUMMARY, allow_empty=False)
    if "fix" in item:
        _check_text(errors, path + ".fix", item["fix"], MAX_FIX)
    if "prevented_by" in item and item["prevented_by"] is not None:
        problem = asset_path_error(item["prevented_by"])
        if problem:
            errors.append("%s.prevented_by: %s (or null)" % (path, problem))


def _validate_promotion(item: Any, path: str, errors: List[str]) -> None:
    if not isinstance(item, dict):
        errors.append("%s: must be an object" % path)
        return
    _check_keys(item, PROMOTION_KEYS, (), path, errors)
    if "signature" in item:
        _check_signature(errors, path + ".signature", item["signature"])
    if "level" in item:
        _check_enum(errors, path + ".level", item["level"], LEVELS)
    if "asset" in item:
        problem = asset_path_error(item["asset"])
        if problem:
            errors.append("%s.asset: %s" % (path, problem))


def _validate_metrics(metrics: Any, errors: List[str]) -> None:
    if not isinstance(metrics, dict):
        errors.append("metrics: must be an object")
        return
    _check_keys(metrics, METRIC_KEYS, (), "metrics", errors)
    ints: Dict[str, int] = {}
    for key in METRIC_KEYS:
        if key not in metrics:
            continue
        value = metrics[key]
        if _is_int(value) and value >= 0:
            ints[key] = value
        else:
            errors.append("metrics.%s: must be a non-negative integer" % key)
    if "first_pass" in ints and "tasks" in ints and ints["first_pass"] > ints["tasks"]:
        errors.append("metrics.first_pass: must not exceed metrics.tasks")
    if "iterations" in ints and "tasks" in ints and ints["tasks"] > 0 and ints["iterations"] < ints["tasks"]:
        errors.append("metrics.iterations: must be >= metrics.tasks when tasks > 0")


def _render_path(node: Any) -> str:
    parts: List[str] = []
    while node is not None:
        node, label = node
        parts.append(label)
    return "".join(reversed(parts))


def _lint_privacy(value: Any, path: str, errors: List[str]) -> None:
    """Flag secrets/identifiers and unencodable text in every string value.

    Iterative (no recursion limit on deeply nested input) and never echoes a match.
    """
    stack: List[Tuple[Any, Any]] = [((None, path), value)]
    while stack:
        node, item = stack.pop()
        if isinstance(item, str):
            where = _render_path(node) or "record"
            try:
                item.encode("utf-8")
            except UnicodeEncodeError:
                errors.append("%s: contains a character that cannot be encoded as UTF-8 (lone surrogate)" % where)
                continue
            for label, pattern in PRIVACY_PATTERNS:
                if pattern.search(item):
                    errors.append("%s: privacy lint: contains %s" % (where, label))
        elif isinstance(item, dict):
            keys = list(item)
            for key in reversed(keys):
                label = ("." if (node[0] is not None or node[1]) else "") + _safe(str(key))
                stack.append(((node, label), item[key]))
        elif isinstance(item, list):
            for index in range(len(item) - 1, -1, -1):
                stack.append(((node, "[%d]" % index), item[index]))


def validate_record(record: Any, existing_run_ids: Optional[Iterable[str]] = None) -> List[str]:
    """Return a list of error strings for one run record (empty list = valid).

    `existing_run_ids` enables the uniqueness check for a record that carries
    its own `run_id`. The 8 KiB line cap is checked separately (line_size_error)
    because it applies to the serialized line.
    """
    if not isinstance(record, dict):
        return ["record must be a JSON object"]
    errors: List[str] = []
    _check_keys(record, REQUIRED_KEYS, OPTIONAL_KEYS, "", errors)

    if "schema" in record and not (_is_int(record["schema"]) and record["schema"] == SCHEMA_VERSION):
        errors.append("schema: must be the integer %d" % SCHEMA_VERSION)
    if "date" in record:
        value = record["date"]
        if not isinstance(value, str) or not DATE_RE.fullmatch(value):
            errors.append("date: must be YYYY-MM-DD")
        else:
            try:
                _date.fromisoformat(value)
            except ValueError:
                errors.append("date: not a real calendar date")
    if "workflow" in record:
        value = record["workflow"]
        if not isinstance(value, str) or len(value) > MAX_WORKFLOW or not KEBAB_RE.fullmatch(value):
            errors.append("workflow: must be a kebab-case name of at most %d characters (^[a-z0-9]+(-[a-z0-9]+)*$)" % MAX_WORKFLOW)
    if "outcome" in record:
        _check_enum(errors, "outcome", record["outcome"], OUTCOMES)
    if "run_id" in record:
        value = record["run_id"]
        if not isinstance(value, str) or len(value) > MAX_RUN_ID or not KEBAB_RE.fullmatch(value):
            errors.append("run_id: must be a kebab-case id of at most %d characters" % MAX_RUN_ID)
        elif existing_run_ids is not None and value in set(existing_run_ids):
            errors.append("run_id: '%s' already exists in the log" % value)
    if "agent" in record:
        _check_text(errors, "agent", record["agent"], None, allow_empty=False)
    if "task_shape" in record:
        _check_text(errors, "task_shape", record["task_shape"], MAX_TASK_SHAPE)
    if "notes" in record:
        _check_text(errors, "notes", record["notes"], MAX_NOTES)
    if "metrics" in record:
        _validate_metrics(record["metrics"], errors)
    for key, validator in (("mistakes", _validate_mistake), ("promotions", _validate_promotion)):
        if key not in record:
            continue
        items = record[key]
        if not isinstance(items, list):
            errors.append("%s: must be a list" % key)
            continue
        for index, item in enumerate(items):
            validator(item, "%s[%d]" % (key, index), errors)
        if key == "mistakes":
            first_index: Dict[str, int] = {}
            for index, item in enumerate(items):
                sig = item.get("signature") if isinstance(item, dict) else None
                if isinstance(sig, str):
                    if sig in first_index:
                        errors.append(
                            "mistakes[%d].signature: duplicates mistakes[%d]; list each signature once per record and merge its symptoms"
                            % (index, first_index[sig])
                        )
                    else:
                        first_index[sig] = index

    _lint_privacy(record, "", errors)
    return errors


def underreporting_warnings(record: Record) -> List[str]:
    """Non-fatal under-reporting hints for a *valid* record (the Goodhart guard made checkable).

    1. escaped_defects > 0 without a mistake sourced ci, user or post-release
    2. user_corrections > 0 without a user-sourced mistake
    3. first_pass < tasks, or tool_errors > 0, with an empty mistakes list
    """
    metrics = record["metrics"]
    sources = {mistake["source"] for mistake in record["mistakes"]}
    found: List[str] = []
    if metrics["escaped_defects"] > 0 and not sources & {"ci", "user", "post-release"}:
        found.append(
            "escaped_defects is %d but no mistake has source ci, user or post-release (possible under-reporting)"
            % metrics["escaped_defects"]
        )
    if metrics["user_corrections"] > 0 and "user" not in sources:
        found.append(
            "user_corrections is %d but no mistake has source user (possible under-reporting)" % metrics["user_corrections"]
        )
    if not record["mistakes"]:
        reasons = []
        if metrics["first_pass"] < metrics["tasks"]:
            reasons.append("first_pass (%d) < tasks (%d)" % (metrics["first_pass"], metrics["tasks"]))
        if metrics["tool_errors"] > 0:
            reasons.append("tool_errors is %d" % metrics["tool_errors"])
        if reasons:
            found.append("%s but mistakes is empty (possible under-reporting)" % " and ".join(reasons))
    return found


def canonical_json(record: Record) -> str:
    """The exact serialization used for log lines."""
    return json.dumps(record, ensure_ascii=False, sort_keys=True)


def line_size_error(line: str) -> Optional[str]:
    size = len(line.encode("utf-8"))
    if size > MAX_LINE_BYTES:
        return "line is %d bytes; the maximum is %d (8 KiB)" % (size, MAX_LINE_BYTES)
    return None


def generate_run_id(record: Record) -> str:
    """`<date>-<workflow>-<first 6 hex of sha1 of the canonical record without run_id>`."""
    body = {key: value for key, value in record.items() if key != "run_id"}
    digest = hashlib.sha1(canonical_json(body).encode("utf-8"), usedforsecurity=False).hexdigest()[:6]
    return "%s-%s-%s" % (record["date"], record["workflow"], digest)


# --------------------------------------------------------------------------- log IO


def resolve_log_path(flag: Optional[str] = None, environ: Optional[Dict[str, str]] = None) -> Path:
    """--log flag, then env LLM_RUN_LOG, then ~/.llm-toolkit/run-log.jsonl."""
    env = os.environ if environ is None else environ
    if flag:
        return Path(flag).expanduser()
    value = env.get(ENV_LOG)
    if value:
        return Path(value).expanduser()
    return Path.home() / ".llm-toolkit" / "run-log.jsonl"


def _no_duplicate_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key '%s'" % _safe(key))
        result[key] = value
    return result


def _reject_constant(name: str) -> Any:
    raise ValueError("invalid JSON constant %s" % name)


def parse_json(text: str) -> Any:
    """json.loads that rejects duplicate keys, NaN/Infinity and absurd nesting (raises ValueError)."""
    try:
        return json.loads(text, object_pairs_hook=_no_duplicate_keys, parse_constant=_reject_constant)
    except RecursionError:
        raise ValueError("JSON nesting is too deep") from None


def _read_log_lines(path: Path) -> List[Tuple[int, int, Optional[str]]]:
    """(line_no, byte_length, text-or-None-if-not-UTF-8) for every non-blank line."""
    try:
        data = path.read_bytes()
    except FileNotFoundError:
        return []
    if data.startswith(b"\xef\xbb\xbf"):
        data = data[3:]
    chunks = data.split(b"\n")
    if chunks and chunks[-1] == b"":
        chunks.pop()
    lines: List[Tuple[int, int, Optional[str]]] = []
    for number, raw in enumerate(chunks, start=1):
        chunk = raw[:-1] if raw.endswith(b"\r") else raw
        if not chunk.strip():
            continue
        try:
            text: Optional[str] = chunk.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        lines.append((number, len(chunk), text))
    return lines


def load_records(path: Path, warnings: Optional[List[str]] = None) -> Tuple[List[Record], List[str]]:
    """Read and validate a log. Returns (valid records in log order, ["line N: error", ...]).

    A missing log is empty. Blank lines are ignored (but still counted in line
    numbers). Records that fail validation, or repeat an earlier run_id, are
    reported in the error list and left out of the record list. When `warnings`
    is a list, "line N: <hint>" under-reporting hints for valid records are added to it.
    """
    records: List[Record] = []
    errors: List[str] = []
    first_line_of: Dict[str, int] = {}
    for number, size, text in _read_log_lines(Path(path)):
        if text is None:
            errors.append("line %d: not valid UTF-8" % number)
            continue
        problems: List[str] = []
        if size > MAX_LINE_BYTES:
            problems.append("line is %d bytes; the maximum is %d (8 KiB)" % (size, MAX_LINE_BYTES))
        try:
            record = parse_json(text)
        except ValueError as exc:
            errors.append("line %d: invalid JSON: %s" % (number, exc))
            errors.extend("line %d: %s" % (number, problem) for problem in problems)
            continue
        problems += validate_record(record)
        run_id = record.get("run_id") if isinstance(record, dict) else None
        if isinstance(run_id, str):
            if run_id in first_line_of:
                problems.append("run_id: '%s' duplicates line %d" % (_safe(run_id), first_line_of[run_id]))
            else:
                first_line_of[run_id] = number
        if problems:
            errors.extend("line %d: %s" % (number, problem) for problem in problems)
        else:
            records.append(record)
            if warnings is not None:
                warnings.extend("line %d: %s" % (number, hint) for hint in underreporting_warnings(record))
    return records, errors


def existing_run_ids(path: Path) -> Set[str]:
    """Every string run_id found in the log, tolerant of invalid lines."""
    found: Set[str] = set()
    for _number, _size, text in _read_log_lines(Path(path)):
        if text is None:
            continue
        try:
            record = parse_json(text)
        except ValueError:
            continue
        if isinstance(record, dict) and isinstance(record.get("run_id"), str):
            found.add(record["run_id"])
    return found


def _write_line(path: Path, line: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = b""
    try:
        with open(path, "rb") as handle:
            handle.seek(0, os.SEEK_END)
            if handle.tell() > 0:
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) != b"\n":
                    prefix = b"\n"  # never glue onto an unterminated last line
    except FileNotFoundError:
        pass
    with open(path, "ab") as handle:
        handle.write(prefix + line.encode("utf-8") + b"\n")


def append_record(path: Path, record: Any, warnings: Optional[List[str]] = None) -> Tuple[Optional[str], List[str]]:
    """Validate and append one record. Returns (run_id, []) or (None, errors); writes nothing on error.

    The final record (including a generated run_id) is validated again before writing, so
    append can never write a line that `validate` rejects. When `warnings` is a list,
    under-reporting hints for the appended record are added to it.
    """
    path = Path(path)
    existing = existing_run_ids(path)
    errors = validate_record(record, existing)
    if errors:
        return None, errors
    final = dict(record)
    if "run_id" not in final:
        run_id = generate_run_id(final)
        if run_id in existing:
            return None, [
                "run_id: '%s' already exists in the log (an identical record was already appended; "
                "give this run a distinct run_id or different notes)" % run_id
            ]
        final["run_id"] = run_id
    errors = validate_record(final)
    if errors:
        return None, errors
    line = canonical_json(final)
    problem = line_size_error(line)
    if problem:
        return None, [problem]
    _write_line(path, line)
    if warnings is not None:
        warnings.extend(underreporting_warnings(final))
    return final["run_id"], []


# --------------------------------------------------------------------------- analysis


def _ratio(numerator: float, denominator: float) -> Optional[float]:
    return None if denominator == 0 else numerator / denominator


def _round(value: Optional[float]) -> Optional[float]:
    return None if value is None else round(value, 4)


def _delta(last: Optional[float], prev: Optional[float]) -> Optional[float]:
    return None if last is None or prev is None else _round(last - prev)


def _chronological(records: List[Record]) -> List[Record]:
    """Oldest first: ISO date, ties broken by log order."""
    return [record for _idx, record in sorted(enumerate(records), key=lambda pair: (pair[1]["date"], pair[0]))]


def _window_stats(runs: List[Record]) -> Dict[str, Optional[float]]:
    tasks = sum(r["metrics"]["tasks"] for r in runs)
    first_pass = sum(r["metrics"]["first_pass"] for r in runs)
    iterations = sum(r["metrics"]["iterations"] for r in runs)
    corrections = sum(r["metrics"]["user_corrections"] for r in runs)
    escapes = sum(r["metrics"]["escaped_defects"] for r in runs)
    count = len(runs)
    return {
        "fpy": _ratio(first_pass, tasks),
        "correction_rate": _ratio(corrections, count),
        "escape_rate": _ratio(escapes, count),
        "rework": _ratio(iterations - tasks, tasks),
    }


def signature_stats(records: List[Record]) -> Dict[str, Dict[str, Any]]:
    """Per-signature facts, in first-seen log order.

    count            distinct runs that recorded the signature
    workflows        distinct workflows (first-seen order)
    last_seen        latest run date (ties: later log position)
    severe           any high/critical occurrence, or a safety-near-miss
    fix/prevented_by latest non-empty fix / non-null prevented_by
    highest_level    highest promoted level recorded anywhere, else None
    ineffective      an occurrence in a run strictly after the earliest run that
                     recorded the highest promoted level (the current prevention
                     level failed; a higher-level promotion resets the flag)
    """
    stats: Dict[str, Dict[str, Any]] = {}
    promotions: Dict[str, List[Tuple[Tuple[str, int], str]]] = {}
    for idx, record in enumerate(records):
        key = (record["date"], idx)
        seen: Set[str] = set()
        for mistake in record["mistakes"]:
            sig = mistake["signature"]
            info = stats.get(sig)
            if info is None:
                info = stats[sig] = {
                    "signature": sig,
                    "first_idx": idx,
                    "keys": [],
                    "workflows": [],
                    "severe": False,
                    "fix_key": None,
                    "fix": "",
                    "pb_key": None,
                    "prevented_by": None,
                }
            if sig not in seen:
                seen.add(sig)
                info["keys"].append(key)
            if record["workflow"] not in info["workflows"]:
                info["workflows"].append(record["workflow"])
            if mistake["severity"] in SEVERE_SEVERITIES or mistake["category"] == "safety-near-miss":
                info["severe"] = True
            if mistake["fix"] and (info["fix_key"] is None or key >= info["fix_key"]):
                info["fix_key"], info["fix"] = key, mistake["fix"]
            if mistake["prevented_by"] and (info["pb_key"] is None or key >= info["pb_key"]):
                info["pb_key"], info["prevented_by"] = key, mistake["prevented_by"]
        for promotion in record["promotions"]:
            promotions.setdefault(promotion["signature"], []).append((key, promotion["level"]))
    for sig, info in stats.items():
        info["count"] = len(info["keys"])
        info["last_seen"] = max(info["keys"])[0]
        recorded = promotions.get(sig, [])
        highest = max((level for _key, level in recorded), key=lambda lv: LEVEL_RANK[lv], default=None)
        info["highest_level"] = highest
        if highest is None:
            info["ineffective"] = False
        else:
            anchor = min(key for key, level in recorded if level == highest)
            info["ineffective"] = any(key > anchor for key in info["keys"])
    return stats


def _sorted_signatures(infos: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """count desc, last seen desc, then first-seen log order (stable multi-pass sort)."""
    items = list(infos)
    items.sort(key=lambda i: i["first_idx"])
    items.sort(key=lambda i: i["last_seen"], reverse=True)
    items.sort(key=lambda i: i["count"], reverse=True)
    return items


def summarize(records: List[Record], workflow: Optional[str] = None, window: int = DEFAULT_WINDOW) -> Dict[str, Any]:
    """Per-workflow metrics (last window vs the previous window) and recurring signatures."""
    if window < 1:
        raise ValueError("window must be >= 1")
    if workflow is not None:
        records = [r for r in records if r["workflow"] == workflow]
    by_workflow: Dict[str, List[Record]] = {}
    for record in records:
        by_workflow.setdefault(record["workflow"], []).append(record)
    workflows: List[Dict[str, Any]] = []
    for name in sorted(by_workflow):
        runs = _chronological(by_workflow[name])
        last = runs[-window:]
        prev = runs[-2 * window:-window] if len(runs) > window else []
        now = _window_stats(last)
        before = _window_stats(prev) if prev else None
        entry: Dict[str, Any] = {
            "workflow": name,
            "runs": len(runs),
            "window_runs": len(last),
            "prev_window_runs": len(prev),
            "fpy_last": _round(now["fpy"]),
            "fpy_prev": _round(before["fpy"]) if before else None,
            "fpy_delta": _delta(now["fpy"], before["fpy"]) if before else None,
        }
        for metric in ("correction_rate", "escape_rate", "rework"):
            entry[metric] = _round(now[metric])
            entry[metric + "_delta"] = _delta(now[metric], before[metric]) if before else None
        workflows.append(entry)
    recurring = []
    for info in _sorted_signatures(i for i in signature_stats(records).values() if i["count"] >= 2)[:TOP_RECURRING]:
        recurring.append(
            {
                "signature": info["signature"],
                "count": info["count"],
                "workflows": sorted(info["workflows"]),
                "last_seen": info["last_seen"],
                "promoted_level": info["highest_level"] or "none",
                "ineffective": info["ineffective"],
            }
        )
    return {"window": window, "total_runs": len(records), "workflows": workflows, "recurring": recurring}


def _next_level(level: Optional[str]) -> str:
    if level is None:
        return LEVELS[0]
    index = LEVELS.index(level)
    return LEVELS[min(index + 1, len(LEVELS) - 1)]


def find_candidates(records: List[Record], threshold: int = DEFAULT_THRESHOLD) -> List[Dict[str, Any]]:
    """Signatures that need promotion, with the proposed next ladder level.

    Applicable decisions, in priority order (the highest level wins; priority breaks ties):
      1. ineffective prevention -> next level above the highest recorded (rule stays rule: escalate)
      2. seen in 3+ distinct workflows, no rule yet -> rule
      3. high/critical/safety-near-miss with no guard-or-higher promotion -> guard
      4. count >= threshold and not yet promoted to that level or above ->
         learning (count 1, threshold 1) / checklist (count 2) / guard (count >= 3)
    """
    if threshold < 1:
        raise ValueError("threshold must be >= 1")
    found: List[Dict[str, Any]] = []
    for info in signature_stats(records).values():
        highest = info["highest_level"]
        rank = LEVEL_RANK.get(highest, 0)
        options: List[Tuple[str, str]] = []
        if info["ineffective"]:
            if highest == "rule":
                options.append(("rule", "ineffective prevention: recurred after a rule promotion; escalate for redesign"))
            else:
                options.append((_next_level(highest), "ineffective prevention: recurred after the %s promotion" % highest))
        if len(info["workflows"]) >= 3 and rank < LEVEL_RANK["rule"]:
            options.append(("rule", "cross-workflow pattern: seen in %d distinct workflows" % len(info["workflows"])))
        if info["severe"] and rank < LEVEL_RANK["guard"]:
            options.append(("guard", "high/critical/safety-near-miss without a guard"))
        if info["count"] >= threshold:
            level = "learning" if info["count"] == 1 else "checklist" if info["count"] == 2 else "guard"
            if LEVEL_RANK[level] > rank:
                options.append((level, "seen in %d runs, not yet promoted to %s" % (info["count"], level)))
        if not options:
            continue
        level, reason = options[0]
        for candidate_level, candidate_reason in options[1:]:
            if LEVEL_RANK[candidate_level] > LEVEL_RANK[level]:
                level, reason = candidate_level, candidate_reason
        found.append(
            {
                "signature": info["signature"],
                "level": level,
                "reason": reason,
                "count": info["count"],
                "last_seen": info["last_seen"],
                "workflows": sorted(info["workflows"]),
                "promoted_level": highest or "none",
                "first_idx": info["first_idx"],
            }
        )
    found.sort(key=lambda c: c["first_idx"])
    found.sort(key=lambda c: c["last_seen"], reverse=True)
    found.sort(key=lambda c: c["count"], reverse=True)
    found.sort(key=lambda c: LEVEL_RANK[c["level"]], reverse=True)
    for candidate in found:
        del candidate["first_idx"]
    return found


def _pitfall(info: Dict[str, Any], scope: str) -> Dict[str, Any]:
    return {
        "signature": info["signature"],
        "count": info["count"],
        "last_seen": info["last_seen"],
        "fix": info["fix"],
        "prevented_by": info["prevented_by"],
        "workflows": sorted(info["workflows"]),
        "scope": scope,
    }


def preflight(records: List[Record], workflow: str, limit: int = DEFAULT_LIMIT, include_global: bool = False) -> Dict[str, Any]:
    """Pitfalls to read before starting `workflow`.

    `pitfalls`: the workflow's own signatures ranked by (count desc, last seen desc,
    first-seen log order), top `limit`. `global`: with include_global, signatures seen
    in 2+ distinct workflows (counted across the whole log) not already listed, same
    ranking and limit.
    """
    if limit < 1:
        raise ValueError("limit must be >= 1")
    own_records = [r for r in records if r["workflow"] == workflow]
    own = _sorted_signatures(signature_stats(own_records).values())[:limit]
    pitfalls = [_pitfall(info, "workflow") for info in own]
    shown = {p["signature"] for p in pitfalls}
    globals_: List[Dict[str, Any]] = []
    if include_global:
        everywhere = [
            info
            for info in signature_stats(records).values()
            if len(info["workflows"]) >= 2 and info["signature"] not in shown
        ]
        globals_ = [_pitfall(info, "global") for info in _sorted_signatures(everywhere)[:limit]]
    return {"workflow": workflow, "pitfalls": pitfalls, "global": globals_}


def list_signatures(records: List[Record], workflow: Optional[str] = None) -> List[Dict[str, Any]]:
    """Every recorded signature (count = distinct runs), for reusing slugs before inventing one.

    Sorted by count desc, last seen desc, signature asc. `promoted_level` is the highest
    promoted level recorded, or "none". With `workflow`, only that workflow's runs count.
    """
    if workflow is not None:
        records = [r for r in records if r["workflow"] == workflow]
    items = list(signature_stats(records).values())
    items.sort(key=lambda i: i["signature"])
    items.sort(key=lambda i: i["last_seen"], reverse=True)
    items.sort(key=lambda i: i["count"], reverse=True)
    return [
        {
            "signature": info["signature"],
            "count": info["count"],
            "workflows": sorted(info["workflows"]),
            "last_seen": info["last_seen"],
            "promoted_level": info["highest_level"] or "none",
        }
        for info in items
    ]


# --------------------------------------------------------------------------- formatting


def _num(value: Optional[float], signed: bool = False) -> str:
    if value is None:
        return "n/a"
    return ("%+.3f" if signed else "%.3f") % value


def format_summary(data: Dict[str, Any]) -> str:
    lines = ["window: %d runs (last window vs the previous window)" % data["window"]]
    for wf in data["workflows"]:
        lines.append("workflow: %s" % wf["workflow"])
        lines.append("  runs: %d (last window %d, previous window %d)" % (wf["runs"], wf["window_runs"], wf["prev_window_runs"]))
        lines.append("  first-pass yield: %s (previous %s, delta %s)" % (_num(wf["fpy_last"]), _num(wf["fpy_prev"]), _num(wf["fpy_delta"], True)))
        lines.append("  correction rate: %s per run (delta %s)" % (_num(wf["correction_rate"]), _num(wf["correction_rate_delta"], True)))
        lines.append("  escape rate: %s per run (delta %s)" % (_num(wf["escape_rate"]), _num(wf["escape_rate_delta"], True)))
        lines.append("  rework: %s (delta %s)" % (_num(wf["rework"]), _num(wf["rework_delta"], True)))
    if data["recurring"]:
        lines.append("recurring signatures:")
        for sig in data["recurring"]:
            lines.append(
                "  %dx %s  last seen %s  promoted: %s  ineffective: %s"
                % (sig["count"], sig["signature"], sig["last_seen"], sig["promoted_level"], "yes" if sig["ineffective"] else "no")
            )
    else:
        lines.append("recurring signatures: none")
    return "\n".join(lines)


def format_candidates(candidates: List[Dict[str, Any]]) -> str:
    if not candidates:
        return "no candidates"
    lines = []
    for item in candidates:
        lines.append(
            "%-9s %s  (count %d, last seen %s, promoted: %s)\n          %s"
            % (item["level"], item["signature"], item["count"], item["last_seen"], item["promoted_level"], item["reason"])
        )
    return "\n".join(lines)


def format_signatures(items: List[Dict[str, Any]]) -> str:
    return "\n".join(
        "%dx %s  last seen %s  promoted: %s  workflows: %s"
        % (i["count"], i["signature"], i["last_seen"], i["promoted_level"], ", ".join(i["workflows"]))
        for i in items
    )


def format_preflight(data: Dict[str, Any]) -> str:
    if not data["pitfalls"] and not data["global"]:
        return "no known pitfalls for %s" % _safe(data["workflow"])

    def block(title: str, items: List[Dict[str, Any]]) -> List[str]:
        out = [title]
        for number, item in enumerate(items, start=1):
            seen = "seen %dx, last %s" % (item["count"], item["last_seen"])
            if item["scope"] == "global":
                seen += ", across %d workflows" % len(item["workflows"])
            out.append("%d. %s - %s" % (number, item["signature"], seen))
            out.append("   fix: %s" % (item["fix"] or "(none recorded)"))
            out.append("   prevented by: %s" % (item["prevented_by"] or "(none)"))
        return out

    lines: List[str] = []
    if data["pitfalls"]:
        lines += block("known pitfalls for %s:" % _safe(data["workflow"]), data["pitfalls"])
    if data["global"]:
        lines += block("cross-workflow pitfalls (seen in 2+ workflows):", data["global"])
    return "\n".join(lines)


# --------------------------------------------------------------------------- CLI


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("must be an integer >= 1 (got %r)" % value) from None
    if number < 1:
        raise argparse.ArgumentTypeError("must be an integer >= 1 (got %r)" % value)
    return number


def _load_for_analysis(args: argparse.Namespace) -> List[Record]:
    records, errors = load_records(resolve_log_path(args.log))
    if errors:
        print(
            "warning: skipped %d invalid log problem(s); run `validate` to list them" % len(errors),
            file=sys.stderr,
        )
    return records


def _print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False))


def _print_warnings(warnings: List[str]) -> None:
    for warning in warnings:
        print("warning: %s" % warning, file=sys.stderr)


def cmd_validate(args: argparse.Namespace) -> int:
    warnings: List[str] = []
    records, errors = load_records(resolve_log_path(args.log), warnings)
    _print_warnings(warnings)
    if errors:
        for error in errors:
            print(error)
        return 1
    print("ok: %d records" % len(records))
    return 0


def _decode_record_bytes(data: bytes) -> str:
    """UTF-8 (BOM tolerated), or UTF-16 when a BOM says so (Windows PowerShell 5.1 redirection)."""
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16")
    return data.decode("utf-8-sig")


def _read_record_text(source: str) -> str:
    if source == "-":
        buffer = getattr(sys.stdin, "buffer", None)
        if buffer is not None:
            return _decode_record_bytes(buffer.read())
        return sys.stdin.read()
    return _decode_record_bytes(Path(source).read_bytes())


def cmd_append(args: argparse.Namespace) -> int:
    try:
        text = _read_record_text(args.record)
    except UnicodeDecodeError:
        print("error: record is not valid UTF-8 (UTF-16 is accepted only with a BOM)", file=sys.stderr)
        return 1
    try:
        record = parse_json(text)
    except ValueError as exc:
        print("error: invalid JSON: %s" % exc, file=sys.stderr)
        return 1
    warnings: List[str] = []
    run_id, errors = append_record(resolve_log_path(args.log), record, warnings)
    if errors:
        for error in errors:
            print("error: %s" % error, file=sys.stderr)
        return 1
    _print_warnings(warnings)
    print(run_id)
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    data = summarize(_load_for_analysis(args), workflow=args.workflow, window=args.window)
    if args.json:
        _print_json(data)
    elif data["total_runs"] == 0:
        print("no runs recorded" + (" for %s" % _safe(args.workflow) if args.workflow else ""))
    else:
        print(format_summary(data))
    return 0


def cmd_candidates(args: argparse.Namespace) -> int:
    candidates = find_candidates(_load_for_analysis(args), threshold=args.threshold)
    if args.json:
        _print_json({"threshold": args.threshold, "candidates": candidates})
    else:
        print(format_candidates(candidates))
    return 0


def cmd_signatures(args: argparse.Namespace) -> int:
    items = list_signatures(_load_for_analysis(args), workflow=args.workflow)
    if args.json:
        _print_json({"signatures": items})
    elif not items:
        print("no signatures recorded" + (" for %s" % _safe(args.workflow) if args.workflow else ""))
    else:
        print(format_signatures(items))
    return 0


def cmd_preflight(args: argparse.Namespace) -> int:
    data = preflight(_load_for_analysis(args), args.workflow, limit=args.limit, include_global=args.include_global)
    print(format_preflight(data))
    return 0


def build_parser() -> argparse.ArgumentParser:
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--log", metavar="PATH", help="run log (default: $%s or ~/.llm-toolkit/run-log.jsonl)" % ENV_LOG)

    parser = argparse.ArgumentParser(prog="run_retro.py", description="Validate, append to and analyse the workflow run log.")
    sub = parser.add_subparsers(dest="command", required=True, metavar="{validate,append,summary,candidates,preflight,signatures}")

    p = sub.add_parser("validate", parents=[common], help="validate every line of the log")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("append", parents=[common], help="validate and append one record")
    p.add_argument("--record", required=True, metavar="FILE|-", help="JSON file with one record, or - for stdin")
    p.set_defaults(func=cmd_append)

    p = sub.add_parser("summary", parents=[common], help="per-workflow metrics and recurring signatures")
    p.add_argument("--workflow", help="limit to one workflow")
    p.add_argument("--window", type=_positive_int, default=DEFAULT_WINDOW, help="runs per window (default %d)" % DEFAULT_WINDOW)
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_summary)

    p = sub.add_parser("candidates", parents=[common], help="signatures that need promotion")
    p.add_argument("--threshold", type=_positive_int, default=DEFAULT_THRESHOLD, help="recurrence count that triggers a candidate (default %d)" % DEFAULT_THRESHOLD)
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_candidates)

    p = sub.add_parser("preflight", parents=[common], help="known pitfalls to read before starting a workflow")
    p.add_argument("--workflow", required=True, help="workflow name")
    p.add_argument("--limit", type=_positive_int, default=DEFAULT_LIMIT, help="max pitfalls per section (default %d)" % DEFAULT_LIMIT)
    p.add_argument("--include-global", action="store_true", help="also list signatures seen in 2+ workflows")
    p.set_defaults(func=cmd_preflight)

    p = sub.add_parser("signatures", parents=[common], help="list every recorded signature (reuse before inventing a new one)")
    p.add_argument("--workflow", help="limit to one workflow")
    p.add_argument("--json", action="store_true", help="machine-readable output")
    p.set_defaults(func=cmd_signatures)
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2
    try:
        return args.func(args)
    except OSError as exc:
        print("error: %s" % exc, file=sys.stderr)
        return 2


def _configure_streams() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    _configure_streams()
    raise SystemExit(main())
