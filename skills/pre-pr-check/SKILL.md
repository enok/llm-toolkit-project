---
name: pre-pr-check
description: "Run full pre-PR check — repo validations (lint/tests), the changed-code quality gate, optional Snyk, UI-verify report check, and in-agent AI review. Use when ready for PR, 'check my changes,' 'about to push,' or 'pre-PR check this branch' (branch checked out, no staging)."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Pre-PR Check (in-agent)

Run a full pre-submit flow: (1) run the repo's lint and tests, (2) run the changed-code quality gate, (3) optionally run Snyk if available, (4) perform an in-agent AI diff review. No external CLI; you orchestrate and perform the review using the IDE's LLM. The diff may come from staged changes or from the current branch vs a base branch.

## When to Apply

- User says they are "ready for PR," "about to push," or "check my changes"
- User wants a full pre-submit check (lint + tests + security + AI review)
- User asks for a full check without specifying a single command
- User says "pre-PR check this branch" or "check this PR" (they have the branch checked out, no staging)

## Steps

1. **Run validations.** Infer the repo's lint and test commands (e.g. from `package.json`, `Makefile`, `pom.xml`, or ask the user). Run them in the terminal from the repository root (or the project root that contains the config). If they fail, report failures and stop; suggest fixing before re-running.
2. **Changed-code quality gate.** If source code was created or updated, run the blocking **changed-code-quality-gate** skill (`workflows/changed-code-quality-gate.md`, reference command `python scripts/changed_code_quality_gate.py --base <trusted-base>`) with the trusted PR base so committed branch changes are covered; a worktree-only run is insufficient. Treat a missing or unusable mandatory analyzer as a blocker, not a pass (see `rules/changed-code-quality-gate-required.md`).
3. **Optional: Snyk.** If the user wants security scanning and `snyk` is available, run `snyk test` (or the project's usual Snyk usage). Report critical findings; do not block on non-critical unless the user asks.
4. **Get the diff to review.** Same logic as the **ticket-review** (or **review**) skill: use **staged** (`git diff --cached`) when the user is reviewing their own work and there are staged changes (or they did not ask for branch review); use **branch diff** (`git diff <base>...HEAD`) when they said "this branch" / "this PR" or there are no staged changes and they asked for a pre-PR check. Default base: `origin/main` else `main`; if the user names a base (e.g. "against develop"), use it. If the base ref is not found, ask the user to specify it.
5. **UI verification (when applicable).** If the diff touches front-end UI (components, pages, styles, client behavior) and the user has not explicitly waived browser verification:
   - Read `docs/jira/<TICKET>/ui-verify-report.md` if it exists. **Status `pass`** — continue. **`fail` or `blocked`** — report as a pre-PR blocker unless the user explicitly waived verification; suggest re-running **ui-verify** or fixing blockers.
   - If no report exists and UI changed, note in the review that **ui-verify** was not run and recommend running it before merge (Yellow finding unless the user waived).
   - When a Figma link was in scope, optionally check `docs/jira/<TICKET>/figma-compare-report.md` for `fail`/`blocked` the same way.
6. **Perform in-agent review.** Using the IDE's LLM and this repo's rubrics (`rubrics/architecture.md`, `rubrics/security.md`, `rubrics/code-review-checklist.md`), produce an AI review of the diff. Follow the code-review checklist: evaluate against correctness, security, architecture, maintainability, performance, testing, operability; for Java DTO or shared library PRs, also apply `skills/ticket-review/references/java-dto-library-pr-review.md`; group findings as Red (must fix), Yellow (should fix), Green (nice-to-have); include What/Where, why it matters, and remediation. Summarize blockers and suggestions.
7. **Write report.** Write local outputs to `docs/jira/<TICKET>/` (create the directory if needed; infer `<TICKET>` from the branch name or use `docs/jira/review/` when no ticket is clear). Write `review-report.json` and `review.md` so the user (and the **fix** skill) can act on findings. Report any lint/test/quality-gate/Snyk failures, UI verify/figma-compare gaps, and AI findings in the review. Set check result: fail if any Red findings or a blocking gate failure, neutral if only Yellow/Green, pass if no findings.

There are no exit codes; report blockers and next steps in the review output.

## Related

- `workflows/pre-pr-check.md` — the workflow form (duplicate-file gate, PR file-change table, lane fan-out)
- `skills/ticket-review/SKILL.md` / `skills/review/SKILL.md` — AI diff review without lint/tests
- `skills/fix/SKILL.md` — act on `review-report.json`
- `rules/git-conventions.md` — PR file-change table and duplicate-file gate
