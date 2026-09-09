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
- For ticket work, create or change code only inside the ticket's scope. Do the minimum necessary to satisfy the acceptance criteria and verified root cause.
- Do not add adjacent refactors, cleanup, abstractions, feature expansion, or unrelated behavior changes unless the ticket or user explicitly requires them.
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
- Whenever source code is created or updated, run the mandatory changed-code quality gate in `rules/changed-code-quality-gate-required.md` against the trusted Git base before validation can pass.
- Prefer actually executing checks over telling the user what to run when the environment allows it.
- Match validation to the changed surface. Run compile, unit, and integration tests when application/runtime code or its executable behavior changes. For scripts, Terraform, dashboard JSON, documentation, configuration, or other non-code-only changes, run the focused syntax, formatting, plan, dry-run, schema, or artifact checks that prove that change instead; do not run Maven or other application test suites solely because a non-code file changed.
- If a change crosses surfaces, run the union of the relevant focused checks. Do not treat a non-code-only scope as permission to skip the checks that directly validate that non-code artifact.
- Before final push, compilation/build validation must **never skip any tests or checks**. Do not use flags such as `-DskipTests`, `-DskipITs`, `-Dmaven.test.skip=true`, `-Dmaven.clover.skip=true`, `-Ddependency-check.skip=true`, or similar for final validation unless the user explicitly approves and the risk is documented.

## Evidence Must Be Fresh, Not Recalled

When a task's justification depends on evidence produced by running a command (a grep proving something is unreachable, a search proving a pattern doesn't occur, a count of matches), re-run that command fresh for the current, specific case — never recall or infer the result from a prior, similar-looking case. Two superficially similar problems (e.g. two CVEs in the same class, two files with the same naming pattern) can have different, narrower, or broader preconditions; a template that worked once is not proof it applies again.

If a check does find something, don't claim "no matches" — name what matched and explain specifically why that match still doesn't satisfy the concern (e.g. "this usage exists, but lacks the specific property the finding requires"). A confidently-worded but factually wrong negative result is worse than an honest positive-with-explanation: durable evidence (audit trails, suppression justifications, security sign-offs) is trusted by other engineers without independent re-verification, and one caught-wrong instance erodes trust in the whole document even when the underlying conclusion holds.

## Search Existing Knowledge Before Declaring a Capability Gap

Before declaring any tool, API, or CLI incapable of something ("permanent gap," "not supported," "impossible without a browser/human"), search whatever durable knowledge store exists for this project or tool family first — a learnings inbox, a memory directory, project docs, or prior session notes — for the tool name, the specific capability, or related identifiers. If an existing record already answers it, use that answer directly; only declare a genuine gap after that search comes up empty. Not remembering a solution offhand is a signal to search, not equivalent to "no solution exists." Re-deriving a solution that was already solved and recorded doesn't just waste effort — it can leave a system in a degraded state for the entire re-investigation window.

## Cross-Platform Script Artifacts

- Any script an agent creates or modifies must follow `rules/cross-platform-scripts.md` (portable primary implementation, wrappers never the only entrypoint, documented Windows + POSIX examples, syntax + dry-run verification).

## Change Discipline

- Match existing code style (formatting, naming, indentation).
- Every changed line should trace directly to the user's request.
- No features beyond what was asked.
- No abstractions for single-use code.
- The test: Would a senior engineer say this is overcomplicated? If yes, simplify.

## PR Review Discipline

- Evaluate every PR review comment on its merits; do not automatically agree with reviewers, bots, or prior agent findings.
- Accept and implement feedback only when it is correct, relevant to the requested scope, and improves correctness, security, maintainability, operability, or required behavior.
- If a comment is wrong, stale, out of scope, or riskier than the proposed change, explain why with source evidence and propose the smallest safe alternative.

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

- If a repo lacks `.gitattributes`, add one in the **Configuration** commit category.
- Binary files (images, JARs, ZIPs) are unaffected — `.gitattributes` handles them automatically with `text=auto`.

## Files That Should Never Be Committed

Adjust per project, but common patterns:

- Build output directories (e.g., `target/`, `dist/`, `build/`, `out/`)
- IDE files (e.g., `.idea/`, `*.iml`, `.vscode/` settings)
- OS metadata (e.g., `desktop.ini`, `.DS_Store`, `Thumbs.db`)
- Test coverage output (e.g., `coverage/`)
- Secrets or credentials files (e.g., `.env.local`, `*.key`)
- **Cloud-sync duplicate files** (e.g., `file (1).md`, `script (2).sh`) — created by synced-folder conflict resolution (Google Drive, OneDrive, Dropbox). These contain stale or contradictory content and are a **blocking** issue. See `rules/git-conventions.md § Duplicate-File Gate`.

If these appear in `git status`, do not include them in the commit.
