---
title: Git includeIf hasconfig for SSH remotes never matches unless the glob is `host:*/**`
category: toolchain
created: 2026-11-26
tags: [git, includeif, hasconfig, ssh, multiple-accounts, identity, gitconfig, glob]
---

# Problem
Commits on a machine with several Git accounts kept the wrong author and email. The global
config used a conditional include keyed on the remote URL:
`includeIf "hasconfig:remote.*.url:git@github.example:**"`. It never matched, no error was
printed, and the default identity was used everywhere.

# Failed Approaches
- Assuming the include file was wrong: its content was fine.
- Adding more `**` or reordering the sections: `**` directly after the colon does not match the
  `owner/repo` part of an SSH URL, so the condition stays false.
- Checking only the working tree: the effective identity depends on which includes matched.

# Solution
Diagnose in this order, stopping at the first fault:
1. Git version: `hasconfig:` needs Git 2.36 or newer (`git --version`).
2. Included file bytes: `cat -vet <included-file>` shows stray whitespace, a BOM or CRLF that
   makes the `[user]` section unreadable.
3. Effective config inside the repository:
   `git config --show-origin --get-regexp 'user\.|includeif'` lists which file supplied each
   value and whether the include was loaded.
4. Fix the glob so it covers the path after the colon: `git@github.example:*/**`.

Keep one include per account (one key per account, or one host alias per account in the SSH
config) so each repository resolves to exactly one identity.

# Why
For SSH remotes the URL is `git@host:owner/repo.git`. In Git's glob syntax `**` needs a path
separator context, so `host:**` does not span `owner/repo`, while `host:*/**` does. Because a
non-matching include is silent, the only evidence is the `--show-origin` listing.
Related: `rules/git-conventions.md`.
