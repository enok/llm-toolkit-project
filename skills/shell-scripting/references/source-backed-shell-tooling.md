---
title: Source-backed shell tooling guidance
tags: [shell, bash, powershell, shellcheck, bats, ci, portability]
---

# Source-backed shell tooling guidance

Use this reference for ShellCheck, Bats, portability, and CI shell validation.
Primary sources:

- [ShellCheck](https://www.shellcheck.net/)
- [ShellCheck wiki](https://www.shellcheck.net/wiki/)
- [Bats documentation](https://bats-core.readthedocs.io/)

- Run ShellCheck for changed shell scripts when available; fix warnings instead
  of suppressing them by default.
- Keep necessary suppressions narrow, local, and justified.
- Use behavioral tests for scripts with branching, argument parsing, file
  operations, or CI/deployment consequences.
- Put destructive behavior behind dry-run or explicit confirmation unless it
  runs only in a tightly controlled CI context.
- Quote variables, construct commands with arrays, and avoid `eval`.
- For shared toolkit automation, provide appropriate Windows, Linux, and macOS
  entry paths when the behavior is intended to be cross-platform.

First establish whether the target is POSIX sh, Bash, PowerShell, CI Linux,
macOS, or Windows; do not apply shell-specific advice without that boundary.
