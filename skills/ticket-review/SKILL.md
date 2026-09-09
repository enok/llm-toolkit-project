---
name: ticket-review
description: "Perform an in-agent AI diff review of staged changes or current branch vs base (no lint/tests). Use for 'review my code,' or when reviewing someone else's branch/PR (branch checked out, no staging)."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# In-Agent AI Diff Review

Perform an AI-generated review of a diff using the IDE's LLM. No lint, unit tests, or Snyk. You do the review yourself; do not invoke any external CLI. The diff may come from staged changes or from the current branch compared to a base branch.

## When to Apply

- User asks to "review my changes" or "review my code" and does not need full check
- User wants feedback on architecture, security, or test coverage without running the full pipeline
- User already ran tests/lint and only wants AI review
- User is reviewing someone else's branch or PR (they have the branch checked out, no staging)

## Steps

1. **Get the diff to review.**
   - **Staged (default when reviewing own work):** If the user intent is "review my changes" / "review my code," or there are staged changes and the user did not explicitly ask for branch/PR review, use `git diff --cached` (or the IDE's staged-file context).
   - **Branch diff (when reviewing current branch):** If the user intent is "review this branch," "review this PR," "review the branch," or "review without staging," or there are no staged changes and the user asked for a review, use the diff of the current branch against a base. Use `git diff <base>...HEAD` (three-dot: changes since the branch point). Default base: `origin/main` if it exists, else `main`. If the user specifies a base in chat (e.g. "review against develop"), use that ref.
   - **Tie-breaker:** Staged changes present and no explicit "branch" or "PR" wording → use staged. No staged changes and user said "review" → use branch diff so the skill still produces a useful result.
   - **Base branch not found:** If both `origin/main` and `main` fail (e.g. no remote or different default), ask the user to name the base (e.g. "review against develop") or try common names (`master`, `develop`); if still ambiguous, suggest they specify the base ref.
2. **Load rubrics.** Read from this repo (if in the workspace or linked): `rubrics/architecture.md`, `rubrics/security.md`, and `rubrics/code-review-checklist.md`. The code-review checklist defines the full evaluation categories (correctness, security, architecture, maintainability, performance, testing, operability) and evidence/response rules (Red/Yellow/Green, What/Where/Why/Remediation).
3. **Review.** Using the IDE's LLM, evaluate the diff against the checklist categories that apply. Base findings on concrete evidence in the diff. For Java DTO or shared library PRs, also apply `references/java-dto-library-pr-review.md`. Produce a concise review: summary plus findings grouped by Red (must fix), Yellow (should fix), Green (nice-to-have), with file/line references, why it matters, and remediation where useful.
4. **Write outputs.** Write local outputs to `docs/jira/<TICKET>/` (create the directory if needed; infer `<TICKET>` from the branch name or use `docs/jira/review/` when no ticket is clear). When in doubt, write both files so the user and the **fix** skill can use them:
   - `docs/jira/<TICKET>/review.md` — human-readable review text
   - `docs/jira/<TICKET>/review-report.json` — structured report with findings (each with type/severity: blocker, suggestion, nice-to-have; file, line, message, suggestion) and summary, so the **fix** skill can consume it. See `rubrics/code-review-checklist.md` for the report format.

## Rubrics

The review is guided by this repo's `rubrics/`: **architecture**, **security**, and **code-review-checklist** (holistic categories and Red/Yellow/Green response format). For full pre-PR (lint + tests + optional Snyk + review), use the **pre-pr-check** skill instead.

## Related

- `workflows/ticket-review.md` — ticket-scoped, report-only review workflow (AC coverage, unresolved PR comments, rules/skills findings)
- `workflows/ticket-review-and-fix.md` — the same review followed by the fix loop
- `skills/review/SKILL.md` — the same in-agent diff review under its shorter name
- `skills/pre-pr-check/SKILL.md` — lint + tests + quality gate + review
- `skills/fix/SKILL.md` — act on `review-report.json`
- `references/java-dto-library-pr-review.md` — contract-surface and hygiene checks for Java DTO/library PRs
