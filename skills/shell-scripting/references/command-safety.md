---
trigger: always_on
description: Review shell commands for destructive, exfiltration, or injection risk before execution
---

# Command safety

Before running a local command that has side effects, review it for safety first.

## Always review

- Commands with network access, downloads, or uploads
- Commands with pipes, shell substitution, or inline interpreter execution
- Commands whose literal search patterns or regexes contain shell-active characters such as backticks, `$()`, `;`, `&`, `|`, `<`, or `>`
- Installers and dependency-management commands
- Destructive file operations or Git history rewrites
- Commands touching secrets, auth files, or system-managed paths
- Privileged commands such as `sudo` or `su`

## Review flow

1. Split chained commands into independent segments.
2. If the repository provides a command-assessment script or policy, follow it.
3. Block critical-risk commands by default until the user explicitly reconfirms.
4. Ask for confirmation on high-risk commands and propose a safer alternative.
5. Quote literal patterns so the shell does not execute them. Prefer single-quoted literals for `rg`, `sed`, and similar; escape backticks or `$` when single quotes are not possible.
6. Keep the final command as narrow as possible.

This is guidance for the agent, not kernel-level enforcement.
