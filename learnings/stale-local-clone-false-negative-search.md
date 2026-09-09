---
title: Grep a fresh origin ref, not a possibly stale local clone
category: toolchain
created: 2026-08-19
tags: [git, grep, stale-clone, cross-repo, evidence, false-negative]
---

# Problem

Needed to confirm how a caller repo invokes a shared service, via a
specific config key. Grepping the local clone's working tree for that key
returned zero matches - flatly contradicting earlier verified findings
that the key exists. The clone's `main` was over a thousand commits behind
`origin/main`; the integration had landed after the last local pull.

# Failed Approaches

- Ripgrep/`git grep` over the working tree (all file types,
  case-insensitive): clean zero matches, indistinguishable from "the
  integration was removed".
- Broadening search terms (service name, class-name guesses): still
  nothing - the code genuinely wasn't in the checked-out tree.

# Solution

Before trusting a cross-repo negative search result: `git fetch origin`,
then compare `git rev-list --count main..origin/main`. If behind, search
the remote ref directly without touching the working tree or branch:
`git grep -in "PATTERN" origin/main` (optionally path-scoped, e.g.
`origin/main -- "config/**/*.properties"`), and read files with
`git show origin/main:path/to/file`.

# Why

A stale clone makes "absent" and "outdated" look identical, and a
zero-match grep feels authoritative. `git grep <ref>` searches the object
database, so it needs no checkout, no stash, and no mutation of the
working repo - the freshness check plus ref-scoped search turns a false
negative into reliable evidence.
