#!/usr/bin/env python3
"""Compact the TASKS_TABLE.md / CONTEXT_STATE.md session ledgers.

Long-running work leaves one `## Session: <name>` section per session in
`TASKS_TABLE.md` and `CONTEXT_STATE.md`. Finished sections only add noise, so
this script moves them to `<root>/ledger-archive/` and rewrites the originals
with the remaining sections.

Selection rules:

* A TASKS_TABLE section is archived when its `Total (remaining/not completed)`
  footer row says 0 and its session name is not in `--keep`. The count is the
  first non-empty cell after the label, so both the current 15-column footer
  (`| **Total (remaining/not completed)** |  | 0 | ... |`, count in the Task
  column) and the short form (`| Total (remaining/not completed) | 0 |`) work.
  Header wording such as "all waves complete" is never consulted: it can be
  stale while rows are still open. Footer-like lines inside code fences are
  ignored.
* A CONTEXT_STATE section is archived when its session name was archived from
  TASKS_TABLE.
* The text before the first `## Session: ` line (the header) is preserved.
* Archived sections are appended (never overwritten) to
  `ledger-archive/<FILE>.archive-<date>.md`, one header line per append.
* `ledger-archive/` is added to the checkout's `info/exclude` when `<root>/.git`
  is a directory, or a worktree/submodule `.git` file whose git dir resolves.

Usage (identical on Windows, Linux, and macOS; Python 3, standard library only):

    python scripts/ledger_compact.py --root <dir> [--keep <session>]... [--date YYYY-MM-DD] [--dry-run]

Prints a JSON report to stdout. Exit codes: 0 success, 2 usage error or
missing/unreadable input (TASKS_TABLE.md is required; CONTEXT_STATE.md is not).
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

TASKS_FILE = "TASKS_TABLE.md"
CONTEXT_FILE = "CONTEXT_STATE.md"
ARCHIVE_DIR = "ledger-archive"
EXCLUDE_LINE = "ledger-archive/"
EXCLUDE_EQUIVALENTS = {"ledger-archive/", "/ledger-archive/", "ledger-archive", "/ledger-archive"}

SECTION_SPLIT_RE = re.compile(r"(?m)^(?=## Session: )")
NAME_RE = re.compile(r"^## Session: (?:Cowork / )?([\w.\-]+)")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
REMAINING_LABEL = "total (remaining/not completed)"


@dataclass(frozen=True)
class Section:
    name: str
    text: str


@dataclass
class Plan:
    file: str
    header: str
    original: str
    kept: list[tuple[Section, str]]
    archived: list[Section]

    @property
    def new_text(self) -> str:
        return self.header + "".join(section.text for section, _ in self.kept)


def split_ledger(text: str) -> tuple[str, list[Section]]:
    """Split a ledger into its header and `## Session: ` sections (lossless)."""
    parts = SECTION_SPLIT_RE.split(text)
    header, raw_sections = parts[0], parts[1:]
    sections = []
    for raw in raw_sections:
        match = NAME_RE.match(raw)
        if match:
            name = match.group(1)
        else:
            name = raw.splitlines()[0][len("## Session: "):].strip()
        sections.append(Section(name=name, text=raw))
    return header, sections


def remaining_values(section_text: str) -> list[str]:
    """Counts from every `Total (remaining/not completed)` footer row outside code fences."""
    values: list[str] = []
    in_fence = False
    for line in section_text.splitlines():
        if FENCE_RE.match(line):
            in_fence = not in_fence
            continue
        stripped = line.strip()
        if in_fence or not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        for index, cell in enumerate(cells):
            if cell.strip("* ").strip().casefold() == REMAINING_LABEL:
                rest = [c.strip("* ").strip() for c in cells[index + 1:] if c.strip("* ").strip()]
                values.append(rest[0] if rest else "")
                break
    return values


def remaining_is_zero(section_text: str) -> bool:
    """True when every `Total (remaining/not completed)` row says 0 (and one exists)."""
    values = remaining_values(section_text)
    return bool(values) and all(value == "0" for value in values)


def plan_tasks(text: str, keep: set[str]) -> Plan:
    header, sections = split_ledger(text)
    plan = Plan(file=TASKS_FILE, header=header, original=text, kept=[], archived=[])
    for section in sections:
        if section.name in keep:
            plan.kept.append((section, "keep-list"))
        elif remaining_is_zero(section.text):
            plan.archived.append(section)
        elif remaining_values(section.text):
            plan.kept.append((section, "open-rows"))
        else:
            plan.kept.append((section, "no-total-row"))
    return plan


def plan_context(text: str, archived_names: set[str]) -> Plan:
    header, sections = split_ledger(text)
    plan = Plan(file=CONTEXT_FILE, header=header, original=text, kept=[], archived=[])
    for section in sections:
        if section.name in archived_names:
            plan.archived.append(section)
        else:
            plan.kept.append((section, "not-archived-in-tasks-table"))
    return plan


def size(text: str) -> int:
    return len(text.encode("utf-8"))


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def read_ledger(path: Path) -> str:
    # newline="" keeps CRLF/LF exactly as stored so untouched sections round-trip.
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def write_atomic(path: Path, text: str) -> None:
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def append_archive(path: Path, plan: Plan, date: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    prefix = ""
    if path.exists() and path.stat().st_size > 0:
        with path.open("rb") as handle:
            handle.seek(-1, os.SEEK_END)
            if handle.read(1) != b"\n":
                prefix = "\n"
    count = len(plan.archived)
    header_line = f"# Archived {date} from {plan.file} ({count} session{'s' if count != 1 else ''})"
    body = "".join(ensure_trailing_newline(section.text) for section in plan.archived)
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(prefix + header_line + "\n\n" + body)


def resolve_exclude_path(root: Path) -> tuple[Path | None, str | None]:
    """Return (exclude file, reason it is unavailable) for the checkout at `root`."""
    dotgit = root / ".git"
    if dotgit.is_dir():
        return dotgit / "info" / "exclude", None
    if not dotgit.is_file():
        return None, "not a git checkout"
    try:
        first_line = dotgit.read_text(encoding="utf-8").strip().splitlines()[0]
    except (OSError, UnicodeDecodeError, IndexError):
        return None, ".git file is unreadable or empty"
    match = re.match(r"gitdir:\s*(.+)$", first_line)
    if not match:
        return None, ".git file has no 'gitdir:' line"
    gitdir = Path(match.group(1).strip())
    if not gitdir.is_absolute():
        gitdir = root / gitdir
    try:
        gitdir = gitdir.resolve()
        commondir_file = gitdir / "commondir"
        if commondir_file.is_file():
            common = (gitdir / commondir_file.read_text(encoding="utf-8").strip()).resolve()
        else:
            common = gitdir
    except (OSError, UnicodeDecodeError):
        return None, "gitdir could not be resolved"
    if not common.is_dir():
        return None, f"git common dir not found: {common}"
    return common / "info" / "exclude", None


def exclude_status(exclude_path: Path) -> str:
    try:
        existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    except (OSError, UnicodeDecodeError):
        return "unreadable"
    present = any(line.strip() in EXCLUDE_EQUIVALENTS for line in existing.splitlines())
    return "present" if present else "missing"


def add_exclude(exclude_path: Path) -> None:
    existing = exclude_path.read_text(encoding="utf-8") if exclude_path.exists() else ""
    prefix = "" if not existing or existing.endswith("\n") else "\n"
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    with exclude_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write(prefix + EXCLUDE_LINE + "\n")


def iso_date(value: str) -> str:
    try:
        return dt.datetime.strptime(value, "%Y-%m-%d").date().isoformat()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected YYYY-MM-DD, got {value!r}") from exc


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Move finished sessions out of TASKS_TABLE.md / CONTEXT_STATE.md into ledger-archive/.",
    )
    parser.add_argument("--root", required=True, type=Path, help="Directory holding TASKS_TABLE.md and CONTEXT_STATE.md")
    parser.add_argument("--keep", action="append", default=[], metavar="SESSION", help="Session name to keep even when its remaining count is 0 (repeatable)")
    parser.add_argument("--date", type=iso_date, default=None, help="Archive date, YYYY-MM-DD (default: today)")
    parser.add_argument("--dry-run", action="store_true", help="Report what would change without writing anything")
    return parser.parse_args(argv)


def fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root: Path = args.root
    date = args.date or dt.date.today().isoformat()
    keep = set(args.keep)

    if not root.is_dir():
        return fail(f"--root is not a directory: {root}")
    tasks_path = root / TASKS_FILE
    context_path = root / CONTEXT_FILE
    if not tasks_path.is_file():
        return fail(f"{TASKS_FILE} not found in {root}")

    try:
        tasks_plan = plan_tasks(read_ledger(tasks_path), keep)
        known_names = {section.name for section, _ in tasks_plan.kept} | {section.name for section in tasks_plan.archived}
        for missing in sorted(keep - known_names):
            print(f"warning: --keep session not found in {TASKS_FILE}: {missing}", file=sys.stderr)
        # A name that is also kept in TASKS_TABLE (e.g. a duplicate heading) is never archived from CONTEXT_STATE.
        kept_names = {section.name for section, _ in tasks_plan.kept}
        archived_names = {section.name for section in tasks_plan.archived} - kept_names
        context_plan = plan_context(read_ledger(context_path), archived_names) if context_path.is_file() else None
    except (OSError, UnicodeDecodeError) as exc:
        return fail(f"cannot read ledger: {exc}")

    plans = [tasks_plan] + ([context_plan] if context_plan else [])
    any_archived = any(plan.archived for plan in plans)

    exclude = "skipped: nothing archived"
    exclude_path: Path | None = None
    if any_archived:
        exclude_path, reason = resolve_exclude_path(root)
        if exclude_path is None:
            exclude = f"skipped: {reason}"
            if reason != "not a git checkout":
                print(f"warning: ledger-archive/ not added to git exclude ({reason})", file=sys.stderr)
        else:
            status = exclude_status(exclude_path)
            exclude = {"present": "present", "missing": "would-add" if args.dry_run else "added"}.get(status, "skipped: exclude file unreadable")
            if status != "missing":
                exclude_path = None

    report = {
        "archived": [{"file": plan.file, "session": section.name} for plan in plans for section in plan.archived],
        "kept": [{"file": plan.file, "session": section.name, "reason": why} for plan in plans for section, why in plan.kept],
        "bytes_before": {plan.file: size(plan.original) for plan in plans},
        "bytes_after": {plan.file: size(plan.new_text) for plan in plans},
        "dry_run": bool(args.dry_run),
        "exclude": exclude,
    }

    if not args.dry_run and any_archived:
        # Archive first, then rewrite: an interruption can duplicate a section in the archive but never lose one.
        for plan in plans:
            if plan.archived:
                stem = plan.file.rsplit(".", 1)[0]
                append_archive(root / ARCHIVE_DIR / f"{stem}.archive-{date}.md", plan, date)
        if exclude_path is not None:
            add_exclude(exclude_path)
        for plan, path in ((tasks_plan, tasks_path), (context_plan, context_path)):
            if plan and plan.archived:
                write_atomic(path, plan.new_text)

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
