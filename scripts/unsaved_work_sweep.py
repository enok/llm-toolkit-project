#!/usr/bin/env python3
"""Read-only sweep for work that exists only on this computer.

Before a cleanup (deleting worktrees or branches, wiping a sandbox, closing sessions)
list everything that would be lost. The sweep reports, for each repository root given:

* worktrees with uncommitted changes to tracked files (`dirty-worktree`);
* untracked files under learnings/, skills/, rules/, workflows/, tool-subagents/
  (`untracked-asset`; ignored files are not reported);
* local branches with no upstream and no same-named remote branch (`branch-no-remote`),
  branches with commits their upstream lacks (`branch-unpushed`), and branches whose
  upstream was deleted (`branch-upstream-gone`);
* worktrees on a detached HEAD whose commits no branch or remote holds (`detached-head`);
* stash entries (`stash`);
* ledger sections (`## Session:` in TASKS_TABLE.md at each worktree root) whose
  `Total (remaining/not completed)` count is above 0 and whose header date is older than
  `--stale-days` (`ledger-open-section`; a section with no date in its header counts as
  unknown age and is reported);
* with `--output-dir`, leftover *.bundle / *.patch / *.diff files (`loose-artifact`).

It never writes, fetches, pushes, or deletes: only read-only git commands run, with no
network access and optional locks disabled. Worktrees are discovered from
`git worktree list`, so passing the main checkout covers its linked worktrees.

Usage (Python 3, standard library only):

    python scripts/unsaved_work_sweep.py [--root <repo>]... [--output-dir <dir>]...
        [--stale-days N] [--json] [--fail-on-findings]

Default root is the current directory. Exit codes: 0 always (findings are information),
1 only with --fail-on-findings when there are findings or a root could not be read, 2 on a usage error.
"""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

WATCHED_DIRS = ("learnings", "skills", "rules", "workflows", "tool-subagents")
ARTIFACT_SUFFIXES = (".bundle", ".patch", ".diff")
LEDGER_FILE = "TASKS_TABLE.md"
SECTION_SPLIT_RE = re.compile(r"(?m)^(?=## Session: )")
DATE_RE = re.compile(r"\b(\d{4}-\d{2}-\d{2})\b")


def _load_remaining_values():
    """Reuse the footer parser from ledger_compact.py so both scripts agree on the format."""
    path = Path(__file__).resolve().with_name("ledger_compact.py")
    spec = importlib.util.spec_from_file_location("_ledger_compact_for_sweep", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.remaining_values


remaining_values = _load_remaining_values()


class GitError(Exception):
    pass


def porcelain_entries(raw: str) -> list[str]:
    """Split `git status --porcelain -z` output into "XY path" entries.

    -z keeps paths with spaces or non-ASCII characters unquoted; a rename or copy
    entry is followed by its source path, which is dropped here.
    """
    parts = raw.split("\0")
    out: list[str] = []
    i = 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if len(entry) < 4:
            continue
        out.append(entry)
        if entry[0] in "RC":
            i += 1
    return out


def git(cwd: Path, *args: str, check: bool = True) -> str:
    """Run a read-only git command (no optional locks, no prompts, no network)."""
    result = subprocess.run(
        ["git", "--no-optional-locks", "-C", str(cwd), *args],
        text=True, encoding="utf-8", errors="replace",
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        env=_git_env(),
    )
    if check and result.returncode != 0:
        raise GitError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout


def _git_env() -> dict[str, str]:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def finding(kind: str, repo: str, where: str, detail: str, **extra) -> dict:
    item = {"kind": kind, "repo": repo, "where": where, "detail": detail}
    item.update(extra)
    return item


def list_worktrees(root: Path) -> list[dict]:
    """Worktrees of the repo at root: [{path, head, branch|None, bare, prunable}]."""
    text = git(root, "worktree", "list", "--porcelain")
    worktrees: list[dict] = []
    current: dict = {}
    for line in text.splitlines() + [""]:
        if not line.strip():
            if current:
                worktrees.append(current)
            current = {}
            continue
        key, _, value = line.partition(" ")
        if key == "worktree":
            current = {"path": value, "head": "", "branch": None, "bare": False, "prunable": False}
        elif key == "HEAD":
            current["head"] = value
        elif key == "branch":
            current["branch"] = value.removeprefix("refs/heads/")
        elif key == "bare":
            current["bare"] = True
        elif key == "prunable":
            current["prunable"] = True
    return worktrees


def sweep_worktree(repo: str, wt: dict, today: dt.date, stale_days: int) -> list[dict]:
    out: list[dict] = []
    path = Path(wt["path"])
    if wt["bare"]:
        return out
    if wt["prunable"] or not path.is_dir():
        out.append(finding("dirty-worktree", repo, str(path), "worktree directory is missing (prunable); its branch state is reported separately"))
        return out
    status = porcelain_entries(git(path, "status", "--porcelain", "-z", "--untracked-files=all"))
    tracked = [line for line in status if not line.startswith("??")]
    if tracked:
        out.append(finding("dirty-worktree", repo, str(path), f"{len(tracked)} changed tracked file(s)", files=[line[3:] for line in tracked][:50]))
    watched = [line[3:] for line in status if line.startswith("??") and line[3:].split("/", 1)[0] in WATCHED_DIRS]
    for name in watched[:200]:
        out.append(finding("untracked-asset", repo, str(path), name))
    if wt["branch"] is None and wt["head"]:
        unref = git(path, "rev-list", "--count", "HEAD", "--not", "--branches", "--remotes", check=False).strip()
        if unref.isdigit() and int(unref) > 0:
            out.append(finding("detached-head", repo, str(path), f"detached HEAD with {unref} commit(s) no branch or remote holds"))
    out.extend(sweep_ledger(repo, path, today, stale_days))
    return out


def sweep_branches(repo: str, root: Path) -> list[dict]:
    out: list[dict] = []
    fmt = "%(refname:short)%09%(upstream:short)%09%(upstream:track)"
    for line in git(root, "for-each-ref", "refs/heads", f"--format={fmt}").splitlines():
        name, _, rest = line.partition("\t")
        upstream, _, track = rest.partition("\t")
        if not name:
            continue
        if upstream:
            if "gone" in track:
                out.append(finding("branch-upstream-gone", repo, name, f"upstream {upstream} no longer exists; local commits may be the only copy"))
                continue
            ahead = git(root, "rev-list", "--count", f"{upstream}..{name}", check=False).strip()
            if ahead.isdigit() and int(ahead) > 0:
                out.append(finding("branch-unpushed", repo, name, f"{ahead} commit(s) ahead of {upstream}", ahead=int(ahead)))
            continue
        same_name = git(root, "for-each-ref", "refs/remotes", "--format=%(refname:short)", check=False).split()
        on_remote = any(ref.split("/", 1)[-1] == name for ref in same_name)
        if on_remote:
            continue
        only_local = git(root, "rev-list", "--count", name, "--not", "--remotes", check=False).strip()
        count = int(only_local) if only_local.isdigit() else 0
        out.append(finding("branch-no-remote", repo, name, f"no remote branch; {count} commit(s) not on any remote", commits=count))
    return out


def sweep_stashes(repo: str, root: Path) -> list[dict]:
    lines = [ln for ln in git(root, "stash", "list", check=False).splitlines() if ln.strip()]
    return [finding("stash", repo, f"stash@{{{i}}}", line.split(": ", 1)[-1]) for i, line in enumerate(lines)]


def section_date(section: str) -> dt.date | None:
    header = section.splitlines()[0] if section.strip() else ""
    match = DATE_RE.search(header)
    if not match:
        return None
    try:
        return dt.date.fromisoformat(match.group(1))
    except ValueError:
        return None


def sweep_ledger(repo: str, worktree: Path, today: dt.date, stale_days: int) -> list[dict]:
    out: list[dict] = []
    ledger = worktree / LEDGER_FILE
    if not ledger.is_file():
        return out
    try:
        text = ledger.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [finding("ledger-open-section", repo, str(ledger), f"cannot read ledger: {exc}")]
    for section in SECTION_SPLIT_RE.split(text)[1:]:
        values = remaining_values(section)
        if not values or all(value == "0" for value in values):
            continue
        header = section.splitlines()[0].removeprefix("## Session: ").strip()
        opened = section_date(section)
        age = (today - opened).days if opened else None
        if age is not None and age < stale_days:
            continue
        note = f"remaining {', '.join(values)}; " + (f"{age} day(s) old" if age is not None else "age unknown (no date in header)")
        out.append(finding("ledger-open-section", repo, f"{ledger} :: {header}", note, age_days=age))
    return out


def sweep_output_dir(directory: Path) -> list[dict]:
    out: list[dict] = []
    if not directory.is_dir():
        return [finding("loose-artifact", str(directory), str(directory), "output directory not found")]
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in ARTIFACT_SUFFIXES:
            age = (dt.date.today() - dt.date.fromtimestamp(path.stat().st_mtime)).days
            out.append(finding("loose-artifact", str(directory), str(path), f"{path.stat().st_size} bytes, {age} day(s) old", age_days=age))
    return out


def run_sweep(roots: list[Path], output_dirs: list[Path], stale_days: int, today: dt.date | None = None) -> dict:
    today = today or dt.date.today()
    findings: list[dict] = []
    errors: list[str] = []
    seen_worktrees: set[str] = set()
    seen_repos: set[str] = set()
    for root in roots:
        try:
            common = Path(git(root, "rev-parse", "--path-format=absolute", "--git-common-dir").strip()).resolve()
            worktrees = list_worktrees(root)
        except (GitError, OSError) as exc:
            errors.append(f"{root}: not a readable git repository ({exc})")
            continue
        repo = str(common.parent if common.name == ".git" else common)
        if repo not in seen_repos:
            seen_repos.add(repo)
            try:
                findings.extend(sweep_branches(repo, root))
                findings.extend(sweep_stashes(repo, root))
            except GitError as exc:
                errors.append(f"{root}: {exc}")
        for wt in worktrees:
            key = str(Path(wt["path"]).resolve())
            if key in seen_worktrees:
                continue
            seen_worktrees.add(key)
            try:
                findings.extend(sweep_worktree(repo, wt, today, stale_days))
            except GitError as exc:
                errors.append(f"{wt['path']}: {exc}")
    for directory in output_dirs:
        findings.extend(sweep_output_dir(directory))
    counts: dict[str, int] = {}
    for item in findings:
        counts[item["kind"]] = counts.get(item["kind"], 0) + 1
    return {
        "roots": [str(r) for r in roots],
        "stale_days": stale_days,
        "findings": findings,
        "counts": counts,
        "total": len(findings),
        "errors": errors,
    }


def render_human(report: dict) -> str:
    lines = [f"Unsaved-work sweep: {report['total']} finding(s) across {len(report['roots'])} root(s) (read-only)"]
    by_kind: dict[str, list[dict]] = {}
    for item in report["findings"]:
        by_kind.setdefault(item["kind"], []).append(item)
    for kind in sorted(by_kind):
        lines.append(f"\n[{kind}] {len(by_kind[kind])}")
        for item in by_kind[kind]:
            lines.append(f"  - {item['where']}: {item['detail']}")
    for error in report["errors"]:
        lines.append(f"\nerror: {error}")
    if not report["findings"] and not report["errors"]:
        lines.append("Nothing found: no dirty worktrees, unpushed branches, stashes, untracked assets, or open stale ledger sections.")
    return "\n".join(lines)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Read-only report of work that exists only locally.")
    parser.add_argument("--root", action="append", type=Path, default=[], help="Repository root (repeatable; default: current directory)")
    parser.add_argument("--output-dir", action="append", type=Path, default=[], help="Folder to scan for leftover *.bundle/*.patch/*.diff files (repeatable)")
    parser.add_argument("--stale-days", type=int, default=7, help="Report open ledger sections at least this many days old (default 7)")
    parser.add_argument("--json", action="store_true", help="Print the report as JSON")
    parser.add_argument("--fail-on-findings", action="store_true", help="Exit 1 when there is any finding or a root could not be read (default: always exit 0)")
    args = parser.parse_args(argv)
    if args.stale_days < 0:
        parser.error("--stale-days must be >= 0")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    roots = args.root or [Path.cwd()]
    report = run_sweep(roots, args.output_dir, args.stale_days)
    print(json.dumps(report, indent=2) if args.json else render_human(report))
    if args.fail_on_findings and (report["total"] or report["errors"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
