---
title: git -C worktree add with a relative path resolves against the repo, not your cwd
category: toolchain
created: 2026-08-21
tags: [git, worktree, relative-path, scratchpad, cleanup]
---

# Problem

`cd <scratchpad> && git -C <main-repo> worktree add ./stage-docs <ref>` was
meant to create a throwaway worktree inside the scratchpad. It silently created
`<main-repo>/stage-docs` instead — a full checkout inside the user's project
root.

# Failed Approaches

- Assuming the relative path resolves against the shell's current directory:
  `git -C` changes git's working directory first, so every relative path
  argument resolves against the repository directory.
- Cleaning up afterwards with `git worktree remove` while a shell still had its
  current directory inside the worktree (on Windows: "Permission denied"
  deleting the directory), leaving a stray directory that later needed manual
  deletion from the project root.

# Solution

Always pass an ABSOLUTE path when creating worktrees with `git -C`, or run plain
`git worktree add` from the intended parent directory:

```bash
git -C "$REPO" worktree add "$SCRATCH/stage-docs" "$REF"
```

Before `git worktree remove`, `cd` out of the worktree. If the metadata is
already gone but the directory remains, `git worktree prune` plus manual
directory removal is the only path — so getting the location right up front is
the real fix.

# Why

`-C <path>` is defined as "run as if git was started in `<path>`". It applies
before argument parsing, so every subsequent relative path — worktree targets,
pathspecs, output files — is interpreted relative to that directory rather than
the shell's. Nothing errors, because the path it produced is perfectly valid;
the mistake is only visible as a surprise directory in the repository.
