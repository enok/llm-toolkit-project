---
title: A long-lived consolidation PR is the base for further harvests
category: toolchain
created: 2026-11-26
tags: [consolidation, integration-pr, harvest, branch-hygiene, stacking, scheduled-writers]
---

# Problem
A long-lived integration pull request had already merged every open branch of the toolkit.
A later harvest of unsaved work started from the default branch instead, re-merged branches
that the integration PR already contained, and produced conflicts on files that were already
resolved there.

# Failed Approaches
- Branching from the default branch and re-merging old branches: duplicates the integration
  work and re-opens settled conflicts.
- Copying draft files from older bases over current files: reference text edited after the
  draft was written is lost.

# Solution
- Treat the integration PR's head as the base for further work: branch from it, stack new work
  on top, and apply drafts as deltas onto the current files instead of copying them.
- Do not re-merge branches the integration PR already contains; verify with
  `git merge-base --is-ancestor <branch> <integration-head>` before touching one.
- While the PR consolidates, pause scheduled tasks that write to the repository and record
  which ones were paused, then resume exactly those (see "Hygiene" in
  `workflows/automation-maintenance.md` and `workflows/folder-reorganization.md`).
- After the PR merges, new work goes back on the default branch.

# Why
The integration head is the newest agreed state; anything older is stale by construction.
Stacking keeps one history to review. Pausing writers avoids new commits landing on the
branch that is being consolidated.
