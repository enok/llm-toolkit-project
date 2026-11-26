---
title: A script variable named like an OS environment variable collides on Windows
category: environment
created: 2026-11-26
tags: [windows, powershell, bash, environment-variable, naming, device-bridge, scripts]
---

# Problem
A script variable called `PUBLIC` collided with the Windows system variable of the same name
(the public folder), producing wrong paths. Through the device bridge, a PowerShell command line
also lost every `$`, so variables vanished.

# Failed Approaches
- Renaming only in the failing line: the same name remained elsewhere.
- Passing a multi-line command with variables through the bridge's PowerShell.

# Solution
- Give script variables a specific prefix (`MYTOOL_PUBLIC_DIR`), never a generic name that an
  operating system defines (`PUBLIC`, `TEMP`, `PATH`, `HOME`).
- Anything that uses variables goes into a script file that is run through bash
  (`desktop-commander-powershell-run-and-scan-patterns.md`).
- Windows names are also case-insensitive, see `skills/shell-scripting/SKILL.md`.

# Why
Windows resolves environment variables case-insensitively and exposes them to child processes,
so a plain name can silently shadow an existing value. The bridge's shell expands `$` before the
script ever sees it.
