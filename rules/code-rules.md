---
trigger: always_on
description: Coding discipline, source verification, and change management
---

# Code Rules

General coding discipline and change management. These rules apply to every task regardless of tech stack.

## Development Guidelines

- Follow the user's requirements carefully & to the letter.
- Always write correct, best-practice, DRY (Don't Repeat Yourself), bug-free, fully functional code.
- Fully implement all requested functionality — no TODOs, no placeholders, no missing pieces.
- **Solve the root cause, not the symptom.**
- Minimal and precise changes — only touch what's necessary.
- No unnecessary comments; document in the same style as the file you are modifying.

## Source Code Verification

- **Always read the actual source before modifying.** Never guess method signatures, return types, or field names.
- If a class/module is not in the local workspace (e.g., from a shared library, monorepo package, or external dependency), check **local caches first** (`.m2/repository`, `node_modules`, `vendor/`, `site-packages/`, etc.) before searching remotely or asking the user.
- **Never assume method signatures** — overloaded methods, inherited members, and final methods are common sources of failures when guessed.

## Dependency Injection Configuration

- When adding or modifying beans/services, **always verify the DI configuration** (Spring XML, Guice modules, Angular modules, etc.).
- Config-based wiring (XML, YAML, property files) is common in legacy and enterprise projects — do not assume annotation-based scanning.
- If the project uses config-based DI, check the config files before adding or changing any bean.

## Verify After Changes

- After any non-trivial edit, **verify** before claiming done: run affected tests or scripts, confirm exit codes, or inspect artifacts (e.g. reparse points, generated files).
- Prefer actually executing checks over telling the user what to run when the environment allows it.
- Before final push, compilation/build validation must **never skip any tests or checks**. Do not use flags such as `-DskipTests`, `-DskipITs`, `-Dmaven.test.skip=true`, `-Dmaven.clover.skip=true`, `-Ddependency-check.skip=true`, or similar for final validation unless the user explicitly approves and the risk is documented.

## Cross-Platform Script Artifacts

- Any new or modified script created by an agent must be designed to run from Windows, Linux, and macOS unless the user explicitly asks for an OS-specific script or the target platform is inherently OS-specific.
- This applies to toolkit scripts, consumer-repo scripts, shared skills, CLI helpers, automation scripts, setup scripts, validation scripts, and executable examples.
- Prefer a portable primary implementation such as Python 3, Node.js, or a compiled CLI when the script must work across operating systems.
- OS-specific shell scripts (`.sh`, `.ps1`, `.cmd`) are acceptable as convenience wrappers, but they must not be the only way to run a shared capability unless the task is explicitly OS-specific.
- Document cross-platform commands in skill references or README examples. Include Windows PowerShell and Linux/macOS shell examples when quoting or path syntax differs.
- Avoid hardcoded absolute user paths, drive letters, `/tmp`-only assumptions, GNU-only flags, or shell features that break on another supported OS. Use `pathlib`, environment variables, `mktemp`, or documented OS-specific fallbacks.
- Verify at least syntax and a dry-run path for the portable entrypoint. When possible, test from a different working directory so scripts do not depend on the repo root.

## Change Discipline

- Match existing code style (formatting, naming, indentation).
- Every changed line should trace directly to the user's request.
- No features beyond what was asked.
- No abstractions for single-use code.
- The test: Would a senior engineer say this is overcomplicated? If yes, simplify.

## Line Endings — LF Only

- **All files MUST use LF (`\n`) line endings.** Never commit CRLF (`\r\n`).
- On Windows, Git's `core.autocrlf` can silently introduce CRLF. Always verify before committing.
- Every repo SHOULD have a `.gitattributes` file at the root enforcing LF:

```gitattributes
# Enforce LF line endings for all text files
* text=auto eol=lf
```

- **Before committing**, check for CRLF in changed files:

```bash
# Find CRLF in staged files
git diff --cached --name-only | xargs grep -Prl '\r$' 2>/dev/null
# Fix: convert CRLF → LF
git diff --cached --name-only | xargs sed -i 's/\r$//'
```

- If a repo lacks `.gitattributes`, add one as part of **Category 4 (Application configs/structure)** in the commit structure.
- Binary files (images, JARs, ZIPs) are unaffected — `.gitattributes` handles them automatically with `text=auto`.

## Files That Should Never Be Committed

Adjust per project, but common patterns:

- Build output directories (e.g., `target/`, `dist/`, `build/`, `out/`)
- IDE files (e.g., `.idea/`, `*.iml`, `.vscode/` settings)
- OS metadata (e.g., `desktop.ini`, `.DS_Store`, `Thumbs.db`)
- Test coverage output (e.g., `coverage/`)
- Secrets or credentials files (e.g., `.env.local`, `*.key`)
- **Cloud-sync duplicate files** (e.g., `file (1).md`, `script (2).sh`) — created by Google Drive, OneDrive, or Dropbox conflict resolution. These contain stale or contradictory content and are a **blocking** issue. See `rules/git-conventions.md § Duplicate-File Gate`.

If these appear in `git status`, do not include them in the commit.
