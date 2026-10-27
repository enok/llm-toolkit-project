#!/usr/bin/env python3
"""Validate a TASKS_TABLE.md ledger against the Tasks table contract.

The contract lives in tool-subagents/agent-orchestrator.md, section "Tasks table
contract: columns, assets, tokens, prints, checkpoints (MANDATORY)". This script
is the mechanical guard for it: 13 exact columns, per-row cell rules, the three
footer rows with their arithmetic, and the assets manifest above the table.

Usage:
    python scripts/check_tasks_table.py <path> [--session <substring>] [--strict]

A file is split into one section per `## Session:` header; a file with no such
header is one anonymous section. Output is one line per finding
(`FAIL|WARN <session-label> row <#>: <message>`) and a summary line. Exit code
is 1 when any FAIL was reported, 2 when the file cannot be read, otherwise 0.

Pure standard library; runs unchanged on Windows, Linux, and macOS.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

COLUMNS = (
    "#", "Wave", "Task", "Assets", "Model/Effort", "Status", "Evidence",
    "PR link(s)", "CI/CD run link(s)", "Tokens", "% Complete", "SLA", "Remaining SLA",
)
LEGACY_PREFIX = ("#", "task", "model/effort")
STATUSES = frozenset({
    "pending", "running", "validating", "refining", "blocked", "paused",
    "completed", "failed", "escalated",
})
TERMINAL = frozenset({"completed", "failed", "escalated"})
FOOTERS = (
    "Total (all tasks)",
    "Total (remaining/not completed)",
    "Remaining SLA to complete all tasks (critical path)",
)
FOOTER_KEYS = tuple(f.casefold() for f in FOOTERS)
MAX_SLA_MINUTES = 30

C_NUM, C_WAVE, C_TASK, C_ASSETS, C_MODEL, C_STATUS = 0, 1, 2, 3, 4, 5
C_TOKENS, C_SLA, C_REMAINING = 9, 11, 12

SESSION_RE = re.compile(r"^##\s+Session:")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
WAVE_RE = re.compile(r"^W\d+$")
HHMM_RE = re.compile(r"^(\d{2,3}):([0-5]\d)$")
TOKEN_RE = re.compile(r"^(~?)(\d+(?:\.\d)?)([KM])$")
EST_RE = re.compile(r"^est\.\s*\S")
SEPARATOR_CELL_RE = re.compile(r"^:?-+:?$")
MANIFEST_FIELDS = ("Route", "Rules in force", "Agents", "Helpers")
ASSET_KINDS = ("skill", "rule", "workflow", "wf", "agent", "script")
ASSET_SUFFIX_RE = re.compile(r"\.(md|py)$")


class Finding:
    def __init__(self, level: str, label: str, row: str, message: str) -> None:
        self.level = level
        self.label = label
        self.row = row
        self.message = message

    def render(self) -> str:
        return f"{self.level} {self.label} row {self.row}: {self.message}"


class Section:
    def __init__(self, header: str, label: str, lines: list) -> None:
        self.header = header  # the `## Session:` line, "" for an anonymous section
        self.label = label
        self.lines = lines


# --------------------------------------------------------------------------- parsing


def bare(cell: str) -> str:
    """Strip whitespace and markdown bold/code wrapping from a cell."""
    return cell.strip().strip("*`").strip()


def norm(cell: str) -> str:
    return cell.replace("*", "").replace("`", "").strip().casefold()


def split_cells(line: str) -> list:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", body)]


def is_separator(cells: list) -> bool:
    return bool(cells) and all(SEPARATOR_CELL_RE.match(c) for c in cells)


def session_label(header: str, fallback: str) -> str:
    text = header.split("Session:", 1)[1].strip() if "Session:" in header else ""
    for sep in (" — ", " – ", " -- "):
        text = text.split(sep, 1)[0]
    text = text.strip()
    if not text:
        return fallback
    return text if len(text) <= 60 else text[:57] + "..."


def split_sections(text: str, default_label: str) -> list:
    sections = []
    preamble = []
    current = None
    in_fence = False
    for line in text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
        if not in_fence and SESSION_RE.match(line):
            current = Section(line, session_label(line, "(unnamed session)"), [])
            sections.append(current)
        elif current is not None:
            current.lines.append(line)
        else:
            preamble.append(line)
    if not sections:
        return [Section("", default_label, preamble)]
    return sections


def find_table(lines: list):
    """Return (start_index, table_lines) of the first table whose first header cell is `#`."""
    runs = []
    run = []
    start = 0
    in_fence = False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            if run:
                runs.append((start, run))
                run = []
            continue
        stripped = line.strip()
        if not in_fence and stripped.startswith("|"):
            if not run:
                start = i
            run.append(stripped)
        elif run:
            runs.append((start, run))
            run = []
    if run:
        runs.append((start, run))
    for start, run in runs:
        if norm(split_cells(run[0])[0]) == "#":
            return start, run
    return None


def parse_hhmm(cell: str):
    match = HHMM_RE.match(bare(cell))
    if not match:
        return None
    return int(match.group(1)) * 60 + int(match.group(2))


def fmt_hhmm(minutes: int) -> str:
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def parse_status(cell: str):
    word = re.match(r"[a-z]+", bare(cell).strip("`_").casefold())
    if word and word.group(0) in STATUSES:
        return word.group(0)
    return None


def parse_tokens(cell: str):
    """Return (kind, thousands, approx); kind is num|dash|est|empty|invalid."""
    text = bare(cell)
    if text == "":
        return "empty", 0.0, False
    if text == "—":
        return "dash", 0.0, False
    if EST_RE.match(text):
        return "est", 0.0, False
    match = TOKEN_RE.match(text)
    if match:
        value = float(match.group(2)) * (1000.0 if match.group(3) == "M" else 1.0)
        return "num", value, bool(match.group(1))
    return "invalid", 0.0, False


def parse_count(cell: str):
    text = bare(cell)
    return int(text) if text.isdigit() else None


def short(value: str) -> str:
    value = value.strip()
    return value if len(value) <= 40 else value[:37] + "..."


# --------------------------------------------------------------------------- checks


def check_header(header: list, add) -> bool:
    if header == list(COLUMNS):
        return True
    missing = [c for c in COLUMNS if c not in header]
    extra = [c for c in header if c not in COLUMNS]
    if missing or extra or len(header) != len(COLUMNS):
        parts = []
        if missing:
            parts.append("missing " + ", ".join(missing))
        if extra:
            parts.append("unexpected " + ", ".join(extra))
        if len(header) != len(COLUMNS):
            parts.append(f"{len(header)} columns, expected {len(COLUMNS)}")
        add("FAIL", "header", "header columns: " + "; ".join(parts))
    else:
        add("FAIL", "header", "header columns are out of order (expected: " + " | ".join(COLUMNS) + ")")
    return False


def asset_items(cell: str) -> list:
    """Return (item, basename, stem) for each asset in an Assets cell; exempt items are skipped."""
    text = bare(cell)
    if text.casefold().startswith("none"):
        return []
    items = []
    for part in text.split("\u00b7"):
        item = part.strip().strip("*`").strip()
        if not item:
            continue
        kind, sep, rest = item.partition(":")
        name = rest.strip() if sep and kind.strip().casefold() in ASSET_KINDS else item
        base = re.split(r"[\\/]", name)[-1].strip().strip("*`").strip()
        stem = ASSET_SUFFIX_RE.sub("", base)
        if stem == "INTENTS" or not stem:
            continue
        items.append((item, base, stem))
    return items


def mentioned(manifest: str, name: str) -> bool:
    return bool(name) and re.search(r"(?<![\w-])" + re.escape(name) + r"(?![\w-])", manifest) is not None


def check_task_row(cells: list, label: str, manifest: str, add):
    """Check one 13-cell task row; return its parsed facts for the footer arithmetic."""
    facts = {"status": None, "tokens": None, "sla": None, "rem": None}
    if not WAVE_RE.match(cells[C_WAVE]):
        add("FAIL", label, f"Wave '{short(cells[C_WAVE])}' does not match W<number>")
    if cells[C_ASSETS] in ("", "—", "-"):
        add("FAIL", label, "Assets is empty (name the assets, or write 'none (inline)')")
    else:
        for item, base, stem in asset_items(cells[C_ASSETS]):
            if not any(mentioned(manifest, name) for name in {base, stem}):
                add("FAIL", label, f"Assets item '{short(item)}' is not mentioned in the manifest above the table")

    status = parse_status(cells[C_STATUS])
    facts["status"] = status
    if status is None:
        add("FAIL", label, f"Status '{short(cells[C_STATUS])}' is not one of: " + ", ".join(sorted(STATUSES)))
    terminal = status in TERMINAL

    sla = parse_hhmm(cells[C_SLA])
    rem = parse_hhmm(cells[C_REMAINING])
    facts["sla"], facts["rem"] = sla, rem
    if sla is None:
        add("FAIL", label, f"SLA '{short(cells[C_SLA])}' is not HH:MM")
    elif sla > MAX_SLA_MINUTES:
        add("FAIL", label, f"SLA {fmt_hhmm(sla)} exceeds the 00:30 cap; split the task")
    if rem is None:
        add("FAIL", label, f"Remaining SLA '{short(cells[C_REMAINING])}' is not HH:MM")
    else:
        if terminal and rem != 0:
            add("FAIL", label, f"Status {status} requires Remaining SLA 00:00, got {fmt_hhmm(rem)}")
        if sla is not None and rem > sla:
            add("WARN", label, f"Remaining SLA {fmt_hhmm(rem)} exceeds baseline SLA {fmt_hhmm(sla)} (possible breach)")

    kind, value, approx = parse_tokens(cells[C_TOKENS])
    facts["tokens"] = (kind, value, approx)
    if kind == "invalid":
        add("FAIL", label, f"Tokens '{short(cells[C_TOKENS])}' is not 12.3K, ~12.3K, 1.2M, est. <band>, or —")
    elif terminal and kind in ("empty", "dash", "est"):
        add("FAIL", label, f"Status {status} requires Tokens (actual usage or a ~estimate), got '{short(cells[C_TOKENS]) or 'empty'}'")
    return facts


def check_tokens_total(cell: str, facts: list, add) -> None:
    """Sum the numeric rows (a dash or est. row counts 0) and compare with the total.

    Planned bands are never summed, so the total must equal the numeric sum
    within max(0.2K, 1%), and it carries a leading ~ exactly when at least one
    summed value does. Values are in K.
    """
    total_kind, total_value, total_approx = parse_tokens(cell)
    kinds = [f["tokens"] for f in facts if f["tokens"] is not None]
    if any(k[0] == "invalid" for k in kinds):
        return  # already reported on the row; the sum would be meaningless
    numeric = sum(k[1] for k in kinds if k[0] == "num")
    label = "footer"
    if total_kind == "invalid":
        add("FAIL", label, f"Total (all tasks) Tokens '{short(cell)}' is not 12.3K, ~12.3K, 1.2M, est. <band>, or \u2014")
        return
    if total_kind != "num":
        if numeric > 0:
            add("FAIL", label, f"Total (all tasks) Tokens is '{short(cell) or 'empty'}' but the rows sum to {numeric:.1f}K")
        elif total_kind == "est":
            add("FAIL", label, f"Total (all tasks) Tokens '{short(cell)}' is a band; with nothing spent the total is \u2014 or 0.0K")
        return
    has_approx = any(k[0] == "num" and k[2] for k in kinds)
    if has_approx and not total_approx:
        add("FAIL", label, "Total (all tasks) Tokens must carry a leading ~ because a summed row is a ~ estimate")
    elif total_approx and not has_approx:
        add("FAIL", label, "Total (all tasks) Tokens carries ~ but no summed row is a ~ estimate")
    tolerance = max(0.2, 0.01 * numeric)
    if abs(total_value - numeric) > tolerance:
        add("FAIL", label, f"Total (all tasks) Tokens {cell.strip()} != sum of rows {numeric:.1f}K")


def check_footers(footer_cells: dict, facts: list, task_count: int, rows_ok: bool, add) -> None:
    label = "footer"
    total = footer_cells.get(FOOTERS[0])
    if total:
        count = parse_count(total[C_TASK])
        if count is None:
            add("FAIL", label, f"{FOOTERS[0]}: count '{short(total[C_TASK])}' (Task cell) is not a number")
        elif count != task_count:
            add("FAIL", label, f"{FOOTERS[0]}: count {count} != {task_count} task rows")
        if rows_ok:
            check_tokens_total(total[C_TOKENS], facts, add)
        slas = [f["sla"] for f in facts]
        total_sla = parse_hhmm(total[C_SLA])
        if total_sla is None:
            add("FAIL", label, f"{FOOTERS[0]}: SLA '{short(total[C_SLA])}' is not HH:MM")
        elif rows_ok and None not in slas and total_sla != sum(slas):
            add("FAIL", label, f"{FOOTERS[0]}: SLA {fmt_hhmm(total_sla)} != sum of baselines {fmt_hhmm(sum(slas))}")

    remaining_sum = None
    rems = [f["rem"] for f in facts]
    if rows_ok and None not in rems:
        remaining_sum = sum(rems)

    remaining = footer_cells.get(FOOTERS[1])
    if remaining:
        count = parse_count(remaining[C_TASK])
        open_rows = sum(1 for f in facts if f["status"] != "completed")
        if count is None:
            add("FAIL", label, f"{FOOTERS[1]}: count '{short(remaining[C_TASK])}' (Task cell) is not a number")
        elif rows_ok and count != open_rows:
            add("FAIL", label, f"{FOOTERS[1]}: count {count} != {open_rows} non-completed rows")
        rem_total = parse_hhmm(remaining[C_REMAINING])
        if rem_total is None:
            add("FAIL", label, f"{FOOTERS[1]}: Remaining SLA '{short(remaining[C_REMAINING])}' is not HH:MM")
        elif remaining_sum is not None and rem_total != remaining_sum:
            add("FAIL", label, f"{FOOTERS[1]}: Remaining SLA {fmt_hhmm(rem_total)} != sum of row Remaining SLA {fmt_hhmm(remaining_sum)}")

    path = footer_cells.get(FOOTERS[2])
    if path:
        path_sla = parse_hhmm(path[C_REMAINING])
        if path_sla is None:
            add("FAIL", label, f"{FOOTERS[2]}: Remaining SLA '{short(path[C_REMAINING])}' is not HH:MM")
        elif remaining_sum is not None and path_sla > remaining_sum:
            add("FAIL", label, f"{FOOTERS[2]}: {fmt_hhmm(path_sla)} exceeds the remaining sum {fmt_hhmm(remaining_sum)}")


def check_section(section: Section, strict: bool) -> list:
    findings = []

    def add(level: str, row: str, message: str) -> None:
        findings.append(Finding(level, section.label, row, message))

    found = find_table(section.lines)
    if found is None:
        add("FAIL", "-", "no tasks table found")
        return findings
    start, run = found
    header = split_cells(run[0])
    header_norm = [norm(c) for c in header]

    if tuple(header_norm[:3]) == LEGACY_PREFIX:
        add("FAIL" if strict else "WARN", "header",
            "legacy schema (| # | Task | Model/Effort |); migrate to the 13-column Tasks table contract")
        return findings
    if header_norm[:2] != ["#", "wave"]:
        add("FAIL", "header", "unrecognised table header (expected '| # | Wave | Task | ...')")
        return findings

    above = "\n".join([section.header] + section.lines[:start])
    for field in MANIFEST_FIELDS:
        if not re.search(r"\b" + re.escape(field) + r"\b", above):
            add("FAIL", "-", f"assets manifest above the table does not mention '{field}'")

    header_ok = check_header(header, add)

    body = run[1:]
    if body and is_separator(split_cells(body[0])):
        body = body[1:]
    else:
        add("FAIL", "header", "header is not followed by a separator row")

    facts = []
    footer_seen = []
    footer_cells = {}
    task_count = 0
    rows_ok = header_ok
    for raw in body:
        cells = split_cells(raw)
        if all(c == "" for c in cells):
            continue
        first = bare(cells[0])
        key = norm(cells[0])
        if key in FOOTER_KEYS:
            name = FOOTERS[FOOTER_KEYS.index(key)]
            if name in footer_seen:
                add("FAIL", "footer", f"duplicate footer row '{name}'")
            footer_seen.append(name)
            if len(cells) != len(COLUMNS):
                add("FAIL", "footer", f"'{name}' has {len(cells)} cells, expected {len(COLUMNS)}")
            elif header_ok:
                footer_cells.setdefault(name, cells)
            continue
        if key.startswith("total") or key.startswith("remaining sla to complete"):
            add("FAIL", "footer", f"unrecognised footer row '{short(first)}'")
            continue
        label = first or "?"
        task_count += 1
        if footer_seen:
            add("FAIL", label, "task row appears after the footer rows")
        if len(cells) != len(COLUMNS):
            add("FAIL", label, f"has {len(cells)} cells, expected {len(COLUMNS)}")
            rows_ok = False
            continue
        if not header_ok:
            continue
        facts.append(check_task_row(cells, label, above, add))

    for name in FOOTERS:
        if name not in footer_seen:
            add("FAIL", "footer", f"missing footer row '{name}'")
    in_order = [n for n in footer_seen if n in FOOTERS]
    if len(set(in_order)) == len(FOOTERS) and in_order[:3] != list(FOOTERS):
        add("FAIL", "footer", "footer rows are out of order (expected: " + " -> ".join(FOOTERS) + ")")

    if header_ok:
        check_footers(footer_cells, facts, task_count, rows_ok, add)
    return findings


# --------------------------------------------------------------------------- CLI


def run_check(text: str, default_label: str, session: str, strict: bool):
    sections = split_sections(text, default_label)
    if session:
        wanted = session.casefold()
        sections = [s for s in sections if wanted in s.header.casefold()]
    findings = []
    if session and not sections:
        findings.append(Finding("FAIL", f"--session '{session}'", "-", "no section header contains the given text"))
    for section in sections:
        findings.extend(check_section(section, strict))
    return len(sections), findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="check_tasks_table.py",
        description="Validate a TASKS_TABLE.md ledger against the Tasks table contract "
                    "(tool-subagents/agent-orchestrator.md).",
        epilog="Exit codes: 0 no FAIL, 1 at least one FAIL, 2 file unreadable.",
    )
    parser.add_argument("path", help="ledger file (TASKS_TABLE.md) or a file holding one tasks table")
    parser.add_argument("--session", default="",
                        help="check only sections whose '## Session:' header line contains this text (case-insensitive)")
    parser.add_argument("--strict", action="store_true",
                        help="treat a legacy '| # | Task | Model/Effort |' table as FAIL instead of WARN")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    path = Path(args.path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, ValueError) as exc:
        print(f"error: cannot read {args.path}: {exc}", file=sys.stderr)
        return 2
    count, findings = run_check(text, path.name, args.session, args.strict)
    for finding in findings:
        print(finding.render())
    fails = sum(1 for f in findings if f.level == "FAIL")
    warns = sum(1 for f in findings if f.level == "WARN")
    print(f"checked {count} section(s): {fails} fail, {warns} warn")
    return 1 if fails else 0


if __name__ == "__main__":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass
    sys.exit(main())
