---
title: A shared checkout holding another session's uncommitted edits needs a separate worktree
category: toolchain
created: 2026-10-22
tags: [git, worktree, shared-checkout, uncommitted-changes, concurrent-sessions, stash, origin-main]
---

# Problem
Toolkit edits had to be made, but the main checkout was on another branch and held another
session's uncommitted edits. Any change made there would mix with, or disturb, that work.

# Failed Approaches
- `git checkout main` / switching branches in that checkout: blocked or carried the dirty
  files along.
- `git stash` to clear the way: it hides the other session's in-progress files while that
  session may still be editing them, and a later pop can conflict or restore the wrong state.
- Committing on the checked-out branch: the commit would include or sit on unrelated work.

# Solution
- Look first: `git status --short` and `git branch --show-current` in the shared checkout.
- Create a separate worktree from the remote main branch at an ABSOLUTE path (a sibling
  directory of the repo, not inside it):
  `git fetch origin` then `git worktree add <absolute-path> -b <new-branch> origin/main`.
  A relative path resolves against the repo when `git -C` is used
  (`learnings/git-c-worktree-relative-path-lands-in-repo-root.md`).
- Do all edits, tests and commits in that worktree. Do not stash, reset, clean or otherwise
  touch the other session's files or branch.
- When the work is merged, `git worktree remove <path>` from outside it. In a device-bridge
  session run these git commands in the computer's native shell
  (`learnings/cloud-session-device-bridge-file-io.md`).

# Why
The working tree and index belong to a checkout, and every session that uses that checkout
shares them. A worktree gives the new branch its own tree and index while sharing the object
store, so parallel sessions cannot see or clobber each other's uncommitted state.
