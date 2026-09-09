---
title: Reconcile applied-but-uncommitted drift before committing in multi-copy IaC stacks
category: deployment
created: 2026-08-19
tags: [terraform, git, worktree, drift, multi-copy, sync, commit-hygiene]
---

# Problem

A Terraform stack existed in several synchronized copies (an app-repo
branch worktree, a canonical infra-repo branch, and a short-path working
copy initialized against the real backend). When staging a new fix for
commit, `git status` showed extra modified files the current session
never touched - a prior session had authored and *applied* a change (a
variable validation guard) in the working copy and mirrored it to the
branch worktree, but never committed it. Blindly committing everything
would silently smuggle unrelated changes into the fix's commit; discarding
them would desync git from the live-applied configuration.

# Failed Approaches

- Assuming a clean prior state and running `git add -A` for "my" change -
  the staged set contained files the session had no memory of editing.
- Considering a revert of the unknown diff - diffing against the
  real-backend working copy showed the change was already applied live, so
  reverting would create git-vs-live drift and a surprise diff on the next
  plan.

# Solution

Before committing in a multi-copy stack: run `git status`/`git diff` and
explain every changed file; `diff -rq` (excluding `.terraform`, logs,
plans) between the branch copy and the real-backend working copy to learn
which side is ahead. Classify each unexpected diff: if it is already
applied/live, commit it **separately** with an honest message stating it
was previously uncommitted applied config; if it is stale, sync it from
the ahead side rather than reverting. Only then commit the new fix, and
re-verify all copies are byte-identical for the touched files (docs
included) after pushing.

# Why

Working copies that apply against real backends can legitimately run
ahead of git history when a session ends after apply but before commit.
In a multi-copy layout every copy is a potential source of truth for some
file, so commit hygiene requires provenance-checking each diff - one
commit per intent - instead of assuming the working tree equals the
session's own work.
