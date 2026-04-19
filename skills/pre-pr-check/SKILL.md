---
name: pre-pr-check
description: "Run full pre-PR check — repo validations (lint/tests), optional Snyk, and in-agent AI review. Use when ready for PR, 'check my changes,' or 'pre-PR check this branch' (branch checked out, no staging)."
---

# Pre-PR Check (in-agent)

Run a full pre-submit flow: (1) run the repo's lint and tests, (2) optionally run Snyk if available, (3) perform an in-agent AI diff review. No external CLI; you orchestrate and perform the review using the IDE's LLM. The diff may come from staged changes or from the current branch vs a base branch.

## When to Apply

- User says they are "ready for PR," "about to push," or "check my changes"
- User wants a full pre-submit check (lint + tests + security + AI review)
- User asks for a full check without specifying a single command
- User says "pre-PR check this branch" or "check this PR" (they have the branch checked out, no staging)

## Steps

1. **Run validations.** Infer the repo's lint and test commands (e.g. from `package.json`, `Makefile`, `pom.xml`, or ask the user). Run them in the terminal from the repository root (or the project root that contains the config). If they fail, report failures and stop; suggest fixing before re-running.
2. **Optional: Snyk.** If the user wants security scanning and `snyk` is available, run `snyk test` (or the project's usual Snyk usage). Report critical findings; do not block on non-critical unless the user asks.
3. **Get the diff to review.** Same logic as the **review** skill: use **staged** (`git diff --cached`) when the user is reviewing their own work and there are staged changes (or they did not ask for branch review); use **branch diff** (`git diff <base>...HEAD`) when they said "this branch" / "this PR" or there are no staged changes and they asked for a pre-PR check. Default base: `origin/main` else `main`; if the user names a base (e.g. "against develop"), use it. If the base ref is not found, ask the user to specify it.
4. **Perform in-agent review.** Using the IDE's LLM and this repo's rubrics (`rubrics/architecture.md`, `rubrics/security.md`, `rubrics/code-review-checklist.md`), produce an AI review of the diff. Follow the code-review checklist: evaluate against correctness, security, architecture, maintainability, performance, testing, operability; group findings as Red (must fix), Yellow (should fix), Green (nice-to-have); include What/Where, why it matters, and remediation. Summarize blockers and suggestions.
5. **Write report.** Write outputs to `docs/jira/<TICKET>/` (create the directory if needed; infer `<TICKET>` from the branch name or ask the user). Write `review-report.json` and `review.md` so the user (and the **fix** skill) can act on findings. Report any lint/test/Snyk failures and AI findings in the review. Set check result: fail if any Red findings, neutral if only Yellow/Green, pass if no findings.

There are no exit codes; report blockers and next steps in the review output.
