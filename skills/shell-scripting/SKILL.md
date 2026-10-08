---
name: shell-scripting
description: Bash, POSIX sh, and PowerShell scripting best practices for writing robust, portable, and secure scripts. This skill should be used when writing, reviewing, or refactoring shell scripts. Triggers on tasks involving Bash scripts, `set -euo pipefail`, ShellCheck, automation, CLI tools, cron jobs, deployment scripts, CI/CD shell steps, jq JSON validation, cross-platform Windows/macOS/Linux script parity, or PowerShell interop issues (native command exit codes, UTF-8 BOM, `-File` vs `-Command` argument binding).
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Shell Scripting Best Practices

Comprehensive best practices guide for Bash and shell scripting. Contains 30+ rules across 8 categories, prioritized by impact to guide script authoring, review, and refactoring.

## When to Apply

Reference these guidelines when:
- Writing new Bash scripts for automation, deployment, or CI/CD
- Reviewing shell scripts for correctness and safety
- Debugging script failures or unexpected behavior
- Porting scripts between Linux, macOS, and CI environments
- Writing CLI tools or wrapper scripts
- Hardening scripts against injection or misuse

## Shared Toolkit Portability

For any script created by an agent, Windows, Linux, and macOS support is required by default unless the user explicitly asks for an OS-specific script or the target platform is inherently OS-specific.

- Prefer a portable primary runner such as Python 3, Node.js, or a compiled CLI for shared automation.
- Use Bash, PowerShell, or CMD files as thin convenience wrappers when needed, not as the only implementation.
- If a shell script remains Linux/macOS-only, document why the task is OS-specific and provide the Windows path or state that none is safe.
- Include examples for PowerShell and POSIX shells when quoting, paths, or environment variables differ.
- Test syntax and a dry-run path for the portable entrypoint before closing the change.
- Keep flags, defaults, exit codes, dry-run behavior, and examples aligned across the primary script and thin wrappers.
- Avoid GNU-only shell options, machine-specific absolute paths, and shell-specific quoting unless the limitation is explicit and justified.

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Safety & Strict Mode | CRITICAL | `safety-` |
| 2 | Error Handling | CRITICAL | `error-` |
| 3 | Security | HIGH | `sec-` |
| 4 | Script Structure | HIGH | `structure-` |
| 5 | Quoting & Variables | MEDIUM | `var-` |
| 6 | Text Processing & I/O | MEDIUM | `text-` |
| 7 | Portability & Performance | LOW-MEDIUM | `perf-` |
| 8 | PowerShell / Windows interop | HIGH | `ps-` |

## Quick Reference

### 1. Safety & Strict Mode (CRITICAL)

- `safety-strict-mode` - Always use `set -euo pipefail` at the top of every script
- `safety-shebang` - Use `#!/usr/bin/env bash` for portability
- `safety-ifs` - Set `IFS=$'\n\t'` to prevent word splitting on spaces

### 2. Error Handling (CRITICAL)

- `error-trap-cleanup` - Use `trap cleanup EXIT` for guaranteed cleanup of temp files
- `error-trap-err` - Use `trap 'handler' ERR` for error reporting with line numbers
- `error-check-commands` - Check return codes of critical commands, use `|| die "message"`
- `error-pipefail` - `set -o pipefail` catches failures in any pipe segment, not just the last

### 3. Security (HIGH)

- `sec-no-eval` - Never `eval` untrusted input — use arrays and direct execution instead
- `sec-mktemp` - Use `mktemp` for temporary files, never predictable names in /tmp
- `sec-validate-input` - Validate and sanitize all user input and environment variables
- `sec-no-secrets-in-scripts` - Never hardcode credentials — use env vars or secret managers

### 4. Script Structure (HIGH)

- `structure-template` - Use the standard template: shebang, strict mode, constants, functions, main
- `structure-functions` - Organize logic into small named functions with `local` variables
- `structure-arg-parsing` - Use `case` + `shift` or `getopts` for argument parsing
- `structure-usage` - Include `usage()` function with description, options, and examples

### 5. Quoting & Variables (MEDIUM)

- `var-always-quote` - Always double-quote variables: `"$var"` not `$var`
- `var-curly-braces` - Use `"${var}"` for clarity and to prevent ambiguity
- `var-readonly` - Use `readonly` for constants, `local` for function-scoped variables
- `var-default-values` - Use `"${var:-default}"` for defaults, `"${var:?error}"` for required

### 6. Text Processing & I/O (MEDIUM)

- `text-no-parse-ls` - Never parse `ls` output — use globs or `find -print0`
- `text-read-files` - Use `while IFS= read -r line` for safe line-by-line reading
- `text-find-print0` - Use `find -print0 | xargs -0` for filenames with spaces/special chars; it is also the fix for a validator that hangs on a huge expanded argument list (`learnings/hanging-validator-trains-agents-to-skip-validation.md`)
- `text-heredoc` - Use heredocs for multi-line strings, `<<-` for indented heredocs
- `text-jq-validation` - Use `jq empty FILE` to parse-validate JSON; `jq -e 'type == "object"'` to assert shape; never `jq -e empty` (exit 4 on valid JSON)

### 7. Portability & Performance (LOW-MEDIUM)

- `perf-builtins-over-externals` - Prefer Bash builtins over external commands (parameter expansion vs sed)
- `perf-avoid-subshells` - Avoid unnecessary subshells — use `{ }` grouping instead of `( )`
- `perf-parallel` - Use `xargs -P` or `GNU parallel` for parallel processing
- `perf-shellcheck` - Run ShellCheck on every script — integrate into CI

### 8. PowerShell / Windows interop (HIGH)

- `ps-native-command-exit-codes` - Scope `$ErrorActionPreference` per native call and decide success by `$LASTEXITCODE`; PS 5.1 + `2>&1` promotes the first stderr line to a terminating error
- `ps-utf8-no-bom` - Write tool-consumed files with a BOM-less `UTF8Encoding($false)` encoder; PS 5.1 `-Encoding UTF8` emits a BOM that strict parsers (e.g. `aws ... file://`) reject
- `ps-file-vs-command-args` - `powershell -File` binds `a,b` as one literal string for `[string[]]` params; invoke via `-Command` with `@()` or split a delimited string inside the script

## How to Use

Read the standalone rule files for detailed explanations and code examples. These are the only rule files that exist on disk — every other quick-reference slug is expanded in `AGENTS.md`:

```
rules/safety-strict-mode.md
rules/error-trap-cleanup.md
rules/var-always-quote.md
rules/text-jq-validation.md
rules/ps-native-command-exit-codes.md
rules/ps-utf8-no-bom.md
rules/ps-file-vs-command-args.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect script example with explanation
- Correct script example with explanation
- Additional context and key rules

References:

- [references/source-backed-shell-tooling.md](references/source-backed-shell-tooling.md) — ShellCheck, Bats, portability, and CI validation choices.
- [references/command-safety.md](references/command-safety.md) — a compact always-on summary of the destructive-command and confirmation gates (mirrors the toolkit's `rules/command-safety.md`) for consumer repos.

## Known pitfalls

- In Windows PowerShell, do not pass a `--jq '<filter>'` argument to `gh` (the recorded failure was `gh api`, "accepts 1 arg(s), received 5"); pipe the JSON to `ConvertFrom-Json` and select the fields in PowerShell. See `learnings/powershell-gh-jq-quoting-breaks.md`. (sig: tool-misuse/powershell-gh-jq-quoting)
- Before `Remove-Item -Recurse -Force` on a path that may be an NTFS junction, test the `ReparsePoint` attribute and delete a link non-recursively with `[System.IO.Directory]::Delete($Path, $false)`: on PowerShell 5.1 the recursive delete removes the target directory's contents. See `learnings/powershell-remove-item-recurse-deletes-junction-targets.md`.
- When a PowerShell 5.1 step writes a file that another tool will read, do not rely on the PowerShell redirect (the recorded redirect wrote a script as UTF-16 and Python could not read it); redirect through `cmd /c` or use `Out-File` with an explicit encoding, and use the BOM-less writer in `skills/shell-scripting/rules/ps-utf8-no-bom.md` when the consumer rejects a BOM. See `learnings/powershell-redirect-writes-utf16.md`. (sig: tool-misuse/powershell-redirect-writes-utf16)
- Name PowerShell variables so that no two differ only by case: variable names are case-insensitive, and two variables that differed only by case overwrote each other. (sig: tool-misuse/powershell-case-insensitive-variables)
- Under `$ErrorActionPreference = 'Stop'`, do not let a native command's stderr abort the script: wrap the native command with `cmd /c` or relax the preference for that call, and decide success from `$LASTEXITCODE` (`skills/shell-scripting/rules/ps-native-command-exit-codes.md`). (sig: tool-misuse/powershell-stop-aborts-on-native-stderr)

## Related Skills

- **security** — Input validation, injection prevention, secrets management (applies to all scripts handling user input or credentials)
- **js-ts-best-practices** — CI/CD shell steps and Docker deployment scripts often accompany Node.js builds
- **terraform** / **terraform-change-safety** — Change-safety patterns for the Terraform/OpenTofu stacks that deployment scripts wrap
- **best-practices** — Defensive programming and fail-fast patterns that apply to script design

## Related Rules

- `rules/command-safety.md` — destructive commands need an explicit human gate
- `rules/cross-platform-scripts.md` — Windows/macOS/Linux parity for shared automation

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`
