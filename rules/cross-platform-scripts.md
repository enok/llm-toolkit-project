---
trigger: always_on
description: Scripts created or changed by agents must be portable across Windows, Linux, and macOS unless a platform-specific wrapper is intentional
---

# Cross-platform scripts

Scripts created or modified by agents should run on Windows, Linux, and macOS.

## Requirements

- Prefer portable logic and avoid OS-specific assumptions in paths, quoting, line endings, filesystem operations, and shell features.
- Put shared behavior in a portable implementation such as Python, Node, or a small compiled CLI when practical. This applies to toolkit scripts, consumer-repo scripts, shared skills, CLI helpers, automation, setup, validation scripts, and executable examples.
- When shell-specific wrappers are needed, provide equivalent Windows PowerShell and POSIX shell entrypoints that call the same underlying logic; wrappers must not be the only way to run a shared capability unless the task is explicitly OS-specific.
- Avoid hardcoded absolute user paths, drive letters, `/tmp`-only assumptions, GNU-only flags, or shell features that break on another supported OS. Use `pathlib`, environment variables, `mktemp`, or documented OS-specific fallbacks.
- Document prerequisites and example commands for Windows, Linux, and macOS when quoting or path syntax differs.
- Validate on the current platform and structure the script so the other platforms are easy to validate. Verify at least syntax and a dry-run path for the portable entrypoint; when possible, test from a different working directory so scripts do not depend on the repo root.

## Content hashes and byte pins

Checksums used as contract pins (SHA256 of a shipped file, fixture, or template) must be computed against the canonical LF form, not the working-tree copy. Git normalizes line endings in its object database, but a raw byte read returns whatever the checkout produced — so a pin computed on Windows with CRLF fails on every Linux and macOS checkout of the identical file, and vice versa.

- Normalize CRLF to LF before hashing, and write the normalized bytes back when the file is being added.
- Back this with `.gitattributes` (`text=auto eol=lf`) so the stored form matches the pinned form.
- Treat a hash mismatch that appears only in CI as a line-ending problem first; the file content is usually identical.

## Windows notes

- Use PowerShell-safe quoting for Maven, Git, AWS CLI, and path arguments.
- Avoid destructive filesystem operations composed across shells.
- Do not assume symlink privileges; Windows may require Developer Mode, elevation, or NTFS junction fallbacks.

## POSIX notes

- Use `#!/usr/bin/env bash` only when Bash features are required.
- Keep scripts executable when committed from POSIX environments.
- Quote paths and variables because workspace paths may contain spaces.
