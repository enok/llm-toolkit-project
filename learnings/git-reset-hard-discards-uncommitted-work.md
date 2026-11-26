---
title: git reset --hard to "sync" a shared clone silently discards uncommitted work
category: environment
created: 2026-10-14
tags: [git, reset-hard, shared-clone, uncommitted-work, data-loss, multi-lane, orchestration, dry-run]
---

# Problem

An orchestrator "synced" a shared working clone to a ref with `git reset --hard <ref>`.
The clone held uncommitted work from earlier lanes or earlier runs: tracked edits, staged
files and new files. Each reset discarded that work without an error, a prompt or a
warning, and left a clean tree behind. It happened three times (twice in one day, once two
days later) before a guard existed. Signature: `coordination/reset-hard-discards-uncommitted-work`.

# Failed Approaches

- Treating `git reset --hard` as a harmless "make it match" step: it exits 0 and prints one
  line, so nothing signals that anything was lost.
- Assuming untracked files survive: a reset leaves an untracked file alone only when the
  ref does not track the same path. When it does, the local copy is overwritten, and the
  same happens to an ignored file at a tracked path (both checked in a throwaway repo).
- Running `git status` after the reset: the tree is clean by construction, so it proves
  nothing about what was there before.
- Assuming the clone belonged to the current run: other lanes had left edits in it.

# Solution

Look before moving the branch and never reset, checkout or clean a dirty tree. Use the
guard script, which does the check and picks the safe action:

```bash
git -C <clone> status --porcelain=v1 --untracked-files=all   # any output = dirty
python3 scripts/git_safe_sync.py --repo <clone> --to origin/main --dry-run
python3 scripts/git_safe_sync.py --repo <clone> --to origin/main               # dirty: exit 3
python3 scripts/git_safe_sync.py --repo <clone> --to origin/main --wip-commit  # or --stash
```

Clean tree: it fetches (for a remote-tracking ref) and moves the branch. Dirty tree: it
refuses with exit 3 and lists the paths, or, with `--wip-commit`, commits everything on a
`safe-sync/wip-*` branch and prints the SHA (restore with `git cherry-pick -n <sha>`), or,
with `--stash`, stashes including untracked files and prints the stash SHA (restore with
`git stash apply <sha>`). It also refuses during a merge, rebase, cherry-pick, revert or
bisect, refuses when the ref would overwrite an ignored file, and keeps local commits the
ref lacks on a `safe-sync/previous-*` branch. Exit codes: 0 ok, 2 usage or git error,
3 refused.

`tests/test_git_safe_sync.py` replays the original mistake in throwaway repos, including a
control test that shows a plain `git reset --hard` destroying the work, and the suite fails
when the script is swapped for a plain reset. Untested suggestion: give each lane its own
clone or `git worktree` so lanes never share uncommitted state.

Durable guidance: rules/git-conventions.md and scripts/git_safe_sync.py.

# Why

`git reset --hard` makes the index and working tree match a commit. Unlike `checkout` and
`merge`, it does not refuse when local changes or colliding untracked files are in the way.
Uncommitted edits are not recorded in the reflog, so the reset cannot be undone that way.
In a shared clone the lane running the reset did not make the edits, so nobody notices.
