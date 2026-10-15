#!/usr/bin/env python3
"""Move a shared working clone to a ref without ever discarding uncommitted work.

``git reset --hard <ref>`` is a tempting way to "sync" a clone that several
agents or runs share, but it silently throws away every uncommitted edit and
overwrites untracked files the ref also tracks. This script is the safe
replacement: it checks the tree first and only moves the branch when nothing
can be lost.

Exit codes: 0 ok, 2 usage or git error, 3 refused (tree is dirty or an
operation is in progress).
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime, timezone

EXIT_OK = 0
EXIT_ERROR = 2
EXIT_REFUSED = 3

MAX_LISTED = 50
FALLBACK_IDENT = ("git-safe-sync", "git-safe-sync@localhost")
IN_PROGRESS = (
    "MERGE_HEAD",
    "CHERRY_PICK_HEAD",
    "REVERT_HEAD",
    "BISECT_LOG",
    "rebase-merge",
    "rebase-apply",
)
# Variables that would redirect git away from the repository passed in --repo.
STRIPPED_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX")

EPILOG = """\
behavior:
  clean tree   fetch (only when --to is a remote-tracking ref such as
               origin/main), then move the current branch to --to with a hard
               reset. A hard reset is acceptable only because nothing is lost.
  dirty tree   refuse with exit 3 and list the dirty paths. Dirty means any
               line of `git status --porcelain=v1 --untracked-files=all`.
  --wip-commit commit everything (tracked edits and untracked files) as a local
               WIP commit kept on a safe-sync/wip-* branch, print its SHA, then
               move the branch. Restore with `git cherry-pick -n <sha>`.
  --stash      `git stash push --include-untracked`, print the stash SHA, then
               move the branch. Restore with `git stash apply <sha>`.

It also refuses (exit 3) when a merge, rebase, cherry-pick, revert or bisect is
in progress, or when --to would overwrite an ignored file. Local commits that
--to does not contain are kept on a safe-sync/previous-* branch.

exit codes: 0 ok, 2 usage or git error, 3 refused (dirty tree).

examples:
  git_safe_sync.py --repo . --to origin/main --dry-run
  git_safe_sync.py --repo /work/shared-clone --to origin/main --wip-commit
  git_safe_sync.py --repo /work/shared-clone --to v1.2.0 --stash
"""


class GitError(Exception):
    """A git command failed or the arguments were unusable (exit 2)."""


def emit(text: str = "", stream=None) -> None:
    print(text, file=stream or sys.stdout)


def warn(text: str) -> None:
    emit(text, sys.stderr)


def git_run(repo: str, *args: str) -> subprocess.CompletedProcess[bytes]:
    env = {k: v for k, v in os.environ.items() if k not in STRIPPED_ENV}
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        return subprocess.run(
            ["git", "-C", repo, *args],
            capture_output=True,
            env=env,
            check=False,
        )
    except OSError as exc:
        raise GitError(f"cannot run git: {exc}")


def subcommand(args: tuple[str, ...]) -> str:
    skip = False
    for arg in args:
        if skip:
            skip = False
        elif arg == "-c":
            skip = True
        elif not arg.startswith("-"):
            return arg
    return "?"


def git(repo: str, *args: str) -> bytes:
    proc = git_run(repo, *args)
    if proc.returncode != 0:
        detail = proc.stderr.decode("utf-8", "replace").strip()
        raise GitError(f"git {subcommand(args)} failed: {detail}")
    return proc.stdout


def git_text(repo: str, *args: str) -> str:
    return git(repo, *args).decode("utf-8", "replace").strip()


def git_ok(repo: str, *args: str) -> bool:
    return git_run(repo, *args).returncode == 0


def parse_status(raw: bytes) -> list[str]:
    """Turn `status --porcelain=v1 -z` output into one display line per path."""
    parts = raw.split(b"\0")
    lines: list[str] = []
    i = 0
    while i < len(parts):
        entry = parts[i]
        i += 1
        if not entry:
            continue
        code = entry[:2].decode("ascii", "replace")
        path = os.fsdecode(entry[3:])
        if ("R" in code or "C" in code) and i < len(parts):
            path = f"{os.fsdecode(parts[i])} -> {path}"
            i += 1
        lines.append(f"{code} {path}")
    return lines


def dirty_entries(repo: str) -> list[str]:
    raw = git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    return parse_status(raw)


def in_progress_operations(repo: str) -> list[str]:
    found = []
    for name in IN_PROGRESS:
        path = git_text(repo, "rev-parse", "--git-path", name)
        if not os.path.isabs(path):
            path = os.path.join(repo, path)
        if os.path.exists(path):
            found.append(name)
    return found


def current_branch(repo: str) -> str:
    proc = git_run(repo, "symbolic-ref", "--short", "-q", "HEAD")
    name = proc.stdout.decode("utf-8", "replace").strip()
    return name if proc.returncode == 0 and name else "(detached HEAD)"


def head_sha(repo: str) -> str | None:
    proc = git_run(repo, "rev-parse", "--verify", "--quiet", "HEAD^{commit}")
    sha = proc.stdout.decode("ascii", "replace").strip()
    return sha if proc.returncode == 0 and sha else None


def resolve(repo: str, ref: str) -> str | None:
    proc = git_run(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    sha = proc.stdout.decode("ascii", "replace").strip()
    return sha if proc.returncode == 0 and sha else None


def remote_of(repo: str, ref: str) -> str | None:
    """Return the remote name when `ref` is a remote-tracking ref, else None."""
    name = ref.removeprefix("refs/remotes/")
    if git_ok(repo, "show-ref", "--verify", "--quiet", "refs/heads/" + name):
        return None
    remotes = git_text(repo, "remote").splitlines()
    matches = [r for r in remotes if name.startswith(r + "/")]
    return max(matches, key=len) if matches else None


def ignored_overwrites(repo: str, target: str) -> list[str]:
    """Ignored, untracked files that a reset to `target` would overwrite."""
    listed = git(repo, "ls-files", "-z", "--others", "--ignored", "--exclude-standard")
    ignored = {os.fsdecode(p) for p in listed.split(b"\0") if p}
    if not ignored:
        return []
    tree = git(repo, "ls-tree", "-r", "-z", "--name-only", target)
    tracked = {os.fsdecode(p) for p in tree.split(b"\0") if p}
    return sorted(ignored & tracked)


def stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def commit_identity_args(repo: str) -> list[str]:
    if git_ok(repo, "var", "GIT_COMMITTER_IDENT") and git_ok(
        repo, "var", "GIT_AUTHOR_IDENT"
    ):
        return []
    name, email = FALLBACK_IDENT
    return ["-c", "user.name=" + name, "-c", "user.email=" + email]


def preserve_wip_commit(
    repo: str, ref: str, branch: str, count: int
) -> tuple[str, str]:
    """Commit everything and pin the commit on a branch. Returns (sha, branch)."""
    git(repo, "add", "-A")
    message = (
        f"WIP: uncommitted work preserved by git_safe_sync before syncing to {ref}\n\n"
        f"Branch: {branch}\nPaths: {count}\n"
        "Created by scripts/git_safe_sync.py. Restore with\n"
        "`git cherry-pick -n <this commit>`; delete the safe-sync/wip-* branch\n"
        "once the work is restored."
    )
    git(
        repo,
        *commit_identity_args(repo),
        "commit",
        "--no-verify",
        "--no-gpg-sign",
        "-m",
        message,
    )
    sha = git_text(repo, "rev-parse", "HEAD")
    name = f"safe-sync/wip-{stamp()}-{sha[:7]}"
    git(repo, "branch", name, sha)
    return sha, name


def preserve_stash(repo: str) -> str:
    before = git_run(repo, "rev-parse", "--verify", "--quiet", "refs/stash")
    git(
        repo,
        *commit_identity_args(repo),
        "stash",
        "push",
        "--include-untracked",
        "-m",
        f"git_safe_sync {stamp()}",
    )
    after = git_text(repo, "rev-parse", "--verify", "refs/stash")
    if before.returncode == 0 and before.stdout.decode().strip() == after:
        raise GitError("git stash created nothing; refusing to continue")
    return after


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="git_safe_sync.py",
        description=(
            "Move a working clone's branch to a ref without discarding "
            "uncommitted work. Use this instead of `git reset --hard`."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--repo", required=True, help="path to the working clone")
    parser.add_argument(
        "--to", required=True, metavar="REF", help="branch, tag, SHA or remote ref"
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--wip-commit",
        action="store_true",
        help="when dirty, commit everything as a local WIP commit, then sync",
    )
    mode.add_argument(
        "--stash",
        action="store_true",
        help="when dirty, stash including untracked files, then sync",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="report what would happen; change nothing (no fetch either)",
    )
    return parser


def refuse(lines: list[str], reason: str) -> int:
    warn(f"REFUSED: {reason}")
    for line in lines[:MAX_LISTED]:
        warn(f"  {line}")
    if len(lines) > MAX_LISTED:
        warn(f"  ... and {len(lines) - MAX_LISTED} more")
    return EXIT_REFUSED


def locate_repo(path: str) -> str:
    if not os.path.isdir(path):
        raise GitError(f"--repo is not a directory: {path}")
    top = git_run(path, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        raise GitError(f"--repo is not inside a git work tree: {path}")
    return os.fsdecode(top.stdout.strip())


def fetch_and_resolve(repo: str, ref: str, dry: bool) -> str | None:
    """Resolve `ref`, fetching its remote first when it is remote-tracking.

    Returns None only in a dry run where the ref needs a fetch that was skipped.
    """
    remote = remote_of(repo, ref)
    target = resolve(repo, ref)
    if remote and dry:
        if target is None:
            emit(f"[dry-run] would fetch {remote} to resolve {ref} (skipped)")
            return None
    elif remote:
        emit(f"fetching {remote}")
        git(repo, "fetch", remote)
        target = resolve(repo, ref)
    if target is None:
        raise GitError(f"cannot resolve --to {ref!r} to a commit")
    return target


def print_paths(entries: list[str], indent: str = "  ") -> None:
    for line in entries[:MAX_LISTED]:
        emit(f"{indent}{line}")
    if len(entries) > MAX_LISTED:
        emit(f"{indent}... and {len(entries) - MAX_LISTED} more")


def run(args: argparse.Namespace) -> int:
    if args.to.startswith("-"):
        raise GitError(f"--to must be a ref, not an option: {args.to!r}")
    repo = locate_repo(args.repo)
    dry = args.dry_run
    preserve = args.wip_commit or args.stash

    busy = in_progress_operations(repo)
    if busy:
        return refuse(busy, "an operation is in progress; finish or abort it first")

    entries = dirty_entries(repo)
    if entries and not preserve:
        refuse(
            entries,
            f"working tree has {len(entries)} uncommitted path(s); nothing was changed",
        )
        warn("Re-run with --wip-commit or --stash to keep that work, or commit it.")
        return EXIT_REFUSED

    target = fetch_and_resolve(repo, args.to, dry)
    if target is not None:
        collisions = ignored_overwrites(repo, target)
        if collisions:
            return refuse(
                collisions, "--to would overwrite ignored file(s); move them first"
            )

    branch = current_branch(repo)
    old_head = head_sha(repo)
    if dry:
        return report_dry_run(args, branch, old_head, target, entries)

    assert target is not None
    emit(f"sync {branch}: {(old_head or 'none')[:7]} -> {target[:7]} ({args.to})")
    saved, wip_branch = "", None
    if entries:
        emit(f"{len(entries)} uncommitted path(s) found:")
        print_paths(entries)
    if entries and args.wip_commit:
        saved, wip_branch = preserve_wip_commit(repo, args.to, branch, len(entries))
        emit(f"preserved uncommitted work as WIP commit {saved} on {wip_branch}")
    elif entries:
        saved = preserve_stash(repo)
        emit(f"preserved uncommitted work as stash {saved} (stash@{{0}})")
    if entries:
        leftover = dirty_entries(repo)
        if leftover:
            return refuse(
                leftover,
                "tree is still dirty after preserving; the branch was not moved",
            )

    if (
        old_head
        and wip_branch is None
        and not git_ok(repo, "merge-base", "--is-ancestor", old_head, target)
    ):
        previous = f"safe-sync/previous-{stamp()}-{old_head[:7]}"
        git(repo, "branch", previous, old_head)
        emit(f"kept local commits not in {args.to} on branch {previous}")

    # Safe here: the tree is clean and any local work is pinned by a ref above.
    git(repo, "reset", "--hard", target)
    if head_sha(repo) != target or dirty_entries(repo):
        raise GitError(f"tree did not end clean at {target[:7]} after the reset")
    emit(f"synced {branch} to {target[:7]} ({args.to})")
    if wip_branch:
        emit(
            f"restore: git cherry-pick -n {saved}   (then: git branch -D {wip_branch})"
        )
    elif entries:
        emit(f"restore: git stash apply {saved}   (then: git stash drop)")
    return EXIT_OK


def report_dry_run(
    args: argparse.Namespace,
    branch: str,
    old_head: str | None,
    target: str | None,
    entries: list[str],
) -> int:
    new = target[:7] if target else "<known after fetch>"
    emit(f"[dry-run] sync {branch}: {(old_head or 'none')[:7]} -> {new} ({args.to})")
    if entries:
        how = "WIP commit" if args.wip_commit else "stash"
        emit(f"[dry-run] {len(entries)} uncommitted path(s) would go into a {how}:")
        print_paths(entries)
    else:
        emit("[dry-run] tree is clean; the branch would simply move")
    emit("[dry-run] nothing was changed")
    return EXIT_OK


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="backslashreplace")  # type: ignore[attr-defined]
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)  # argparse exits 2 on usage errors
    try:
        return run(args)
    except GitError as exc:
        warn(f"error: {exc}")
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
