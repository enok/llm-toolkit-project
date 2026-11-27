#!/usr/bin/env python3
"""Check that every newly added toolkit resource has a passing value-check row.

Before a new skill, workflow, tool-subagent or rule is added it must have passed
a "resource versus plain model" comparison, recorded as one row in the CSV ledger
docs/llm/value-checks.csv. This script lists the resources added between a base
git ref and HEAD and verifies each has such a row.

Usage:
    python scripts/check_value_checks.py --base <git ref> [--ledger <path>]
                                         [--repo <path>] [--json]

Exit code: 0 all pass, 1 any failure or ledger error, 2 usage or git error.

Pure standard library; runs unchanged on Windows, Linux, and macOS.
"""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

HEADER = [
    "resource", "kind", "date", "model", "winner", "margin", "with_passed",
    "plain_passed", "of", "decision", "evidence", "note",
]
DECISIONS = frozenset({"keep", "keep-slim", "on-demand", "slim", "remove", "retest", "exempt"})
PASSING = frozenset({"keep", "keep-slim", "exempt"})
WINNERS = frozenset({"with", "plain", "tie", "exempt"})
DEFAULT_LEDGER = "docs/llm/value-checks.csv"


class GitError(Exception):
    pass


def added_files(repo: Path, base: str) -> List[str]:
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "diff", "--name-status", "--diff-filter=A",
             "-z", f"{base}...HEAD"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
    except OSError as exc:
        raise GitError(f"cannot run git: {exc}")
    if proc.returncode != 0:
        raise GitError(proc.stderr.decode("utf-8", "replace").strip() or "git diff failed")
    parts = proc.stdout.decode("utf-8", "replace").split("\0")
    out: List[str] = []
    i = 0
    while i + 1 < len(parts):
        if parts[i].startswith("A"):
            out.append(parts[i + 1])
        i += 2
    return out


def resource_id(path: str) -> Optional[str]:
    """Return the resource id for an added path, or None when it does not count."""
    p = path.replace("\\", "/")
    segs = p.split("/")
    if len(segs) == 3 and segs[0] == "skills" and segs[2] == "SKILL.md":
        return f"skills/{segs[1]}"
    if len(segs) == 2 and segs[0] in ("workflows", "tool-subagents", "rules"):
        if segs[1].endswith(".md") and segs[1] != "README.md":
            return p
    return None


def new_resources(paths: List[str]) -> List[str]:
    seen: List[str] = []
    for path in paths:
        rid = resource_id(path)
        if rid and rid not in seen:
            seen.append(rid)
    return sorted(seen)


def load_ledger(path: Path) -> Tuple[Dict[str, Dict[str, str]], List[str]]:
    """Return (rows by resource, ledger errors). First row wins on duplicates."""
    rows: Dict[str, Dict[str, str]] = {}
    errors: List[str] = []
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return rows, [f"cannot read ledger {path}: {exc}"]
    records = list(csv.reader(text.splitlines()))
    if not records or records[0] != HEADER:
        got = ",".join(records[0]) if records else "(empty)"
        errors.append(f"header must be exactly {','.join(HEADER)} (got {got})")
        return rows, errors
    for lineno, rec in enumerate(records[1:], start=2):
        if not rec:
            continue
        if len(rec) != len(HEADER):
            errors.append(f"line {lineno}: expected {len(HEADER)} columns, got {len(rec)}")
            continue
        row = dict(zip(HEADER, rec))
        res = row["resource"].strip()
        if not res:
            errors.append(f"line {lineno}: empty resource")
            continue
        if row["decision"] not in DECISIONS:
            errors.append(f"line {lineno}: {res}: unknown decision '{row['decision']}'")
        if row["winner"] not in WINNERS:
            errors.append(f"line {lineno}: {res}: unknown winner '{row['winner']}'")
        if res in rows:
            errors.append(f"line {lineno}: duplicate row for {res}")
            continue
        rows[res] = row
    return rows, errors


def loads_on_demand(repo: Optional[Path], resource: str) -> bool:
    """True when the resource's own frontmatter says it is loaded on demand."""
    if repo is None:
        return False
    path = repo / (resource + "/SKILL.md" if resource.startswith("skills/") and not resource.endswith(".md") else resource)
    try:
        head = path.read_text(encoding="utf-8", errors="replace").split("\n", 40)[:40]
    except OSError:
        return False
    if not head or head[0].strip() != "---":
        return False
    for line in head[1:]:
        if line.strip() == "---":
            break
        if line.strip().replace(" ", "") == "trigger:model_decision":
            return True
    return False


def judge(resource: str, rows: Dict[str, Dict[str, str]], repo: Optional[Path] = None) -> Optional[str]:
    row = rows.get(resource)
    if row is None and resource.startswith("skills/"):
        row = rows.get(resource + "/SKILL.md")
    if row is None:
        return "no row in the value-check ledger"
    decision = row["decision"]
    if decision not in DECISIONS:
        return f"unknown decision '{decision}'"
    if decision == "on-demand":
        if loads_on_demand(repo, resource):
            return None
        return "decision is 'on-demand' but the file does not say trigger: model_decision"
    if decision not in PASSING:
        return f"decision is '{decision}', not keep, keep-slim or exempt"
    if decision == "exempt" and not row["note"].strip():
        return "exempt row has an empty note"
    return None


def default_repo() -> Path:
    here = Path(__file__).resolve().parent
    try:
        proc = subprocess.run(
            ["git", "-C", str(here), "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        if proc.returncode == 0:
            return Path(proc.stdout.decode().strip())
    except OSError:
        pass
    return here.parent


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", required=True, help="git ref to diff against")
    ap.add_argument("--ledger", default=DEFAULT_LEDGER, help="CSV ledger path")
    ap.add_argument("--repo", default=None, help="repository root")
    ap.add_argument("--json", action="store_true", help="emit JSON")
    args = ap.parse_args(argv)

    repo = Path(args.repo).resolve() if args.repo else default_repo()
    ledger = Path(args.ledger)
    if not ledger.is_absolute():
        ledger = repo / ledger
    try:
        resources = new_resources(added_files(repo, args.base))
    except GitError as exc:
        print(f"git error: {exc}", file=sys.stderr)
        return 2

    rows, ledger_errors = load_ledger(ledger) if (resources or ledger.exists()) else ({}, [])
    failed: List[Dict[str, str]] = []
    passed: List[str] = []
    for res in resources:
        reason = judge(res, rows, repo)
        if reason:
            failed.append({"resource": res, "reason": reason})
        else:
            passed.append(res)

    if args.json:
        print(json.dumps({
            "checked": len(resources), "passed": passed,
            "failed": failed, "ledger_errors": ledger_errors,
        }, indent=2))
    else:
        print(f"value checks: {len(resources)} new resource(s), {len(passed)} passed, "
              f"{len(failed)} failed, {len(ledger_errors)} ledger error(s)")
        for f in failed:
            print(f"FAIL {f['resource']}: {f['reason']}")
        for e in ledger_errors:
            print(f"LEDGER {e}")
    return 1 if failed or ledger_errors else 0


if __name__ == "__main__":
    sys.exit(main())
