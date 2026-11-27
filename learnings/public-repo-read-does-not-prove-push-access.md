---
title: A successful anonymous read of a public repository does not prove push access
category: toolchain
created: 2026-11-24
tags: [git, push, credentials, ls-remote, dry-run, public-repo, preflight, gh-auth]
---

# Problem

An agent checked push readiness with a remote listing (`git ls-remote`) with prompts
disabled. It succeeded, so the plan assumed the machine could push. The repository was
public, so the read needed no credential and proved nothing about write access.

The later push failed with "could not read Username". No credential was stored, the
pull-request command-line tool was not signed in, and no SSH host key was known. Cost: the
push step failed at the end of a long run. The session recorded this as a wrong-assumption
mistake.

# Failed Approaches

- Treating a successful `ls-remote` with prompts disabled as the push-readiness check. It
  passed only because the repository was public and reads need no credential.

# Solution

Test write access explicitly before planning on it:

```bash
git push --dry-run <remote> <branch>
```

A push dry run against the remote failed the same way the real push did (missing
credential), so it works as the probe. Then:

- Check the pull-request tool's auth status as a second check (for example `gh auth status`;
  the exact command was not recorded in the session).
- Check whether the repository is public before reading anything into a successful fetch.
- When no credential exists, hand the interactive sign-in to the owner at the start of the
  run, not at the end.

# Why

An anonymous read and an authenticated write take different paths: a public repository
serves reads without credentials, while a push needs one. The read succeeding therefore says
nothing about the write. General guidance, not observed in this session: running the probe
in the first steps of a run turns a late failure into an early hand-off.
