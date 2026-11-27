---
title: A stop hook complaining about unsigned or unpushed commits is not a request to rewrite history
category: toolchain
created: 2026-11-26
tags: [git, stop-hook, signed-commits, force-with-lease, history-rewrite, approval, protected-branch]
---

# Problem
A stop hook reported that commits on an already pushed branch were unverified or unsigned. Taken
literally, the feedback invites a rebase and force-push of a protected personal main branch.

# Failed Approaches
- Rewriting history immediately to satisfy the hook.
- Force-pushing without approval.

# Solution
- Inspect the history first. If every earlier commit has the same authorship and none is signed,
  record that fact and leave history alone.
- Rewriting and force-pushing a protected personal main needs explicit user approval
  (`rules/external-write-authorization.md`).
- Offer the option: `git rebase` plus `git push --force-with-lease`, and say that the commits
  stay unverified unless a signing key is configured.
- Repeated hook feedback gets the same answer; do not escalate.

# Why
Signing is a property of how earlier commits were made. A rewrite changes every hash for every
collaborator to satisfy an advisory message, which is a larger and less reversible change than the
warning justifies. See `rules/git-conventions.md`.
