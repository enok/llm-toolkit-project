---
title: Parallel "save learnings then archive" requests leave orphaned drafts and stuck ledger rows
category: toolchain
created: 2026-11-26
tags: [worktree, unsaved-work, ledger, learnings, sweep, branch-hygiene, orphan]
---

# Problem
Several chats each asked to save their learnings and then archive. Each ran in its own
worktree. The drafts stayed uncommitted in those worktrees, and the matching ledger rows stayed
"in progress" for weeks. Nothing was lost on disk, but nothing reached the shared repository,
and the next harvest had to rediscover it.

# Failed Approaches
- Trusting that "archive" meant "saved": archiving a chat does not commit or push the draft.
- Letting the main checkout sit on a long-lived feature branch: new work then mixed with old
  and the state of "what is on main" became unclear.

# Solution
- Run a periodic unsaved-work sweep. It lists: worktrees with dirty files, local branches
  without a remote, unpushed commits, untracked learning files, ledger rows stuck at "in
  progress", and stale bundles in output folders. The script `scripts/unsaved_work_sweep.py`
  and the "Unsaved-work sweep" section of `workflows/automation-maintenance.md` describe it.
- Review the report with the owner; commit or discard each item explicitly. Do not delete
  anything the sweep merely lists.
- Keep the main checkout on the default branch and put long-lived work in a worktree.
- Before archiving a chat, confirm the draft is on a pushed branch or in a PR.

# Why
Parallel requests multiply worktrees faster than anyone tidies them, and a ledger row only
changes when the agent that owns it finishes. A scheduled sweep turns the hidden state into a
list that a person can act on. The script and workflow section arrive in the same change set
as this learning; if they are missing from a checkout, apply the manual list above.
