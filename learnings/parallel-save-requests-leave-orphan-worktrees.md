---
title: Parallel "save learnings then archive" requests leave orphaned drafts and stuck ledger rows
category: toolchain
created: 2026-11-26
tags: [worktree, unsaved-work, ledger, learnings, sweep, branch-hygiene, orphan]
---

# Solution
Move the main checkout back to the default branch. First secure the feature branch's
uncommitted work (modified and untracked files): commit it on that branch or move it into a
worktree, then push. Keep long-lived work in that worktree or pushed branch. Discard nothing.

# Why
A main checkout parked on a feature branch mixes new work with old and hides what is on main.
