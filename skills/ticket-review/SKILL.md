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
2. **Load rubrics.** Read `rubrics/architecture.md` from this repo (if in the workspace or linked) for architecture severity calls. Evaluate the categories correctness, security, architecture, maintainability, performance, testing, and operability, and report each finding as Red/Yellow/Green with What/Where/Why/Remediation.
3. **Review.** Using the IDE's LLM, evaluate the diff against the checklist categories that apply. Base findings on concrete evidence in the diff. For Java DTO or shared library PRs, also apply `references/java-dto-library-pr-review.md`. Produce a concise review: summary plus findings grouped by Red (must fix), Yellow (should fix), Green (nice-to-have), with file/line references, why it matters, and remediation where useful.
4. **Write outputs.** Write local outputs to `docs/jira/<TICKET>/` (create the directory if needed; infer `<TICKET>` from the branch name or use `docs/jira/review/` when no ticket is clear). When in doubt, write both files so the user and a later fix step can use them:
   - `docs/jira/<TICKET>/review.md` — human-readable review text
   - `docs/jira/<TICKET>/review-report.json` — structured report with findings (each with type/severity: blocker, suggestion, nice-to-have; file, line, message, suggestion) and summary, so a later fix step can consume it.

## Ticket-scoped signals (S1, S2, S3)

When the review is tied to a ticket or PR, tag every finding with its signal:

- **S1 — acceptance criteria.** Label each AC `AC-1`, `AC-2`, ... and map it to the code that implements it and the test that verifies it. Missing implementation or missing test = **Blocker (S1)**; vague or untestable AC = Ticket Quality Issue.
- **S2 — unresolved PR comments.** Read all review comments (`gh pr view <N> --json reviews,comments`), keep the unresolved ones, and verify for each whether the current code addresses it. Unaddressed actionable comment = **Blocker (S2)**.
- **S3 — rules and skills.** Findings from steps 2-3 above.

The report then carries an S1 table (AC, implemented?, tested?, code/test path:line), an S2 table (comment, status, action needed) and the S3 findings.

## Rubrics

The review is guided by `rubrics/architecture.md` and the categories and Red/Yellow/Green format in step 2. For full pre-PR (lint + tests + optional Snyk + review), use the **pre-pr-check** skill instead.

## Related

- `workflows/ticket-review.md` — report-only entry point; the S1/S2/S3 procedure lives in this file
- `skills/pre-pr-check/SKILL.md` — lint + tests + quality gate + review
- `references/java-dto-library-pr-review.md` — contract-surface and hygiene checks for Java DTO/library PRs
