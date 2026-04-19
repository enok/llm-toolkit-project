---
name: shell-scripting
description: Bash and shell scripting best practices for writing robust, portable, and secure scripts. This skill should be used when writing, reviewing, or refactoring shell scripts. Triggers on tasks involving Bash scripts, automation, CLI tools, cron jobs, deployment scripts, or CI/CD shell steps.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Shell Scripting Best Practices

Comprehensive best practices guide for Bash and shell scripting. Contains 25+ rules across 7 categories, prioritized by impact to guide script authoring, review, and refactoring.

## When to Apply

Reference these guidelines when:
- Writing new Bash scripts for automation, deployment, or CI/CD
- Reviewing shell scripts for correctness and safety
- Debugging script failures or unexpected behavior
- Porting scripts between Linux, macOS, and CI environments
- Writing CLI tools or wrapper scripts
- Hardening scripts against injection or misuse

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
- `text-find-print0` - Use `find -print0 | xargs -0` for filenames with spaces/special chars
- `text-heredoc` - Use heredocs for multi-line strings, `<<-` for indented heredocs

### 7. Portability & Performance (LOW-MEDIUM)

- `perf-builtins-over-externals` - Prefer Bash builtins over external commands (parameter expansion vs sed)
- `perf-avoid-subshells` - Avoid unnecessary subshells — use `{ }` grouping instead of `( )`
- `perf-parallel` - Use `xargs -P` or `GNU parallel` for parallel processing
- `perf-shellcheck` - Run ShellCheck on every script — integrate into CI

## How to Use

Read individual rule files for detailed explanations and code examples:

```
rules/safety-strict-mode.md
rules/error-trap-cleanup.md
```

Each rule file contains:
- Brief explanation of why it matters
- Incorrect script example with explanation
- Correct script example with explanation
- Additional context and key rules

## Related Skills

- **security** — Input validation, injection prevention, secrets management (applies to all scripts handling user input or credentials)
- **nodejs** — CI/CD shell steps and Docker deployment scripts often accompany Node.js builds
- **cloudformation** / **terraform** — Infrastructure deployment scripts that wrap IaC tooling
- **best-practices** — Defensive programming and fail-fast patterns that apply to script design

## Full Compiled Document

For the complete guide with all rules expanded: `AGENTS.md`
