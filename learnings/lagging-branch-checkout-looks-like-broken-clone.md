---
title: A checkout of a lagging branch can look like a broken clone
category: environment
created: 2026-08-26
tags: [git, branch, checkout, stale-tree, content-missing, verification]
---

# Problem

Work proceeded from a checkout where an expected directory had only one
file and another was empty. That was read as "the content is missing" and
led to re-implementing things that already existed elsewhere in the repo's
history - work that later had to be reverted once the mismatch was
understood.

# Failed Approaches

- Assuming a broken clone: the clone was fine; the checked-out branch was
  simply many commits behind the branch that actually held the content.
- Searching the working directory: `grep` and `find` over the current tree
  returned zero results for files that existed on the up-to-date branch but
  not on the lagging one.
- Inferring from naming conventions: guessing what "should" exist based on
  similar repos led to recreating files that already existed elsewhere in
  the real history.

# Solution

Before concluding anything is absent, verify you are on the branch that
actually holds the content:

```bash
# Check current branch and divergence
git status
git log --oneline --graph --all -15

# Compare commit counts against the reference branch
git rev-list --count HEAD..origin/main
git rev-list --count origin/main..HEAD
```

A nonzero "behind" count next to a suspiciously empty directory is the
signal: verify lineage before diagnosing a gap, not after.

# Why

Git checkouts are branch-specific. A branch that diverged before a major
restructuring (files added, directories moved) will show an empty or
sparse tree that looks like missing content but is actually the truthful
state of that branch. The content exists on another branch, just not the
checked-out one - `git rev-list --count` turns a guess into a number.
