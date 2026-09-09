---
name: changed-code-quality-gate
description: Run a mandatory static-analysis gate for Java, Python, JavaScript, TypeScript, Bash, and PowerShell limited to code created or updated in Git. Use during validation, pre-PR checks, reviews, and before push; treat a blocked or failed gate as a code-validation blocker.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Changed-code quality gate

Use this skill whenever source code was added or modified. Load
`workflows/changed-code-quality-gate.md` and treat a blocked or failed gate as
a code-validation blocker. The always-on rule
`rules/changed-code-quality-gate-required.md` makes this gate mandatory before
commit, push, PR readiness, or completion.

## Contract

1. Establish the trusted Git base and head. For a branch or PR, pass the base
   explicitly; default local mode covers only index, worktree, and untracked
   changes relative to `HEAD`.
2. Run `scripts/changed_code_quality_gate.py`. The reference implementation
   invokes only fixed adapters: Semgrep with the reviewed local `.semgrep.yml`
   for Java, Python, JavaScript, and TypeScript, plus trusted syntax and policy
   checks for Bash and PowerShell. Findings are filtered to changed files and
   added/modified lines. The Semgrep path disables candidate-controlled ignore
   and inline suppression mechanisms and verifies every scoped file was scanned.
3. The shipped Semgrep adapter covers Java, Python, JavaScript, and TypeScript,
   including common module extensions. The script adapter covers `.sh` and
   `.ps1` and fails closed when the corresponding syntax parser is unavailable.
   Changed code in another recognized language, an unrecognized file type, an
   oversized source file, or a source-like symlink blocks the reference
   command. Prefer a project's already-configured analyzer for that language.
   Sonar PR/new-code gates and SpotBugs build reports are acceptable only when
   their findings are normalized back to the same changed-file/line scope. A
   whole-project result without that filtering is supporting evidence, not
   this gate.
4. Do not download tools or rules, add credentials, or enable an MCP server as
   a side effect. If a mandatory analyzer is unavailable, report `BLOCKED`.
5. Keep ordinary tests, builds, dependency checks, and the repository security
   gate (`scripts/security-check-toolkit.sh` / `.ps1`) separate and mandatory.

## Quick start

```bash
python scripts/changed_code_quality_gate.py                    # local: index, worktree, untracked vs HEAD
python scripts/changed_code_quality_gate.py --base origin/main # branch / pre-PR (or the repo's default branch)
python scripts/changed_code_quality_gate.py --scope-only       # print scope only; not analyzer coverage
```

The same commands work in PowerShell; use the platform's usable Python launcher
(`python`, `python3`, or `py -3`).

## Exit codes

| Code | Meaning |
| --- | --- |
| 0 | Passed, or no applicable changed code |
| 1 | Changed-code findings |
| 2 | Git scope or configuration error |
| 3 | Required analyzer or coverage unavailable |
| 4 | Analyzer execution or report failure |

## Configuration

`.changed-code-quality-gate.json` is strict JSON. Version 1 accepts only the
`version` key, so a change cannot disable coverage or replace the analyzer.
The trusted rules live in `.semgrep.yml`. CI
(`.github/workflows/changed-code-quality-gate.yml`) runs the gate
implementation, configuration, and rules from the protected PR base, the
immutable pre-push revision, or the protected default branch (`main`) for a new
branch, never from the candidate revision that is being evaluated.

## Provenance

Official Sonar, SpotBugs, and Semgrep sources were reviewed for concepts only.
No external skill content or implementation was imported: the candidate URLs
did not pass the external-source URL check required by
`skills/external-skill-intake/SKILL.md`. This skill is an independent
implementation. See `references/analyzer-selection.md` for the analyzer
comparison and the reviewed sources.
