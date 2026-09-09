---
description: Perform an in-agent AI diff review — report only, no fixes or commits
---

# Code Review Workflow (Report Only)

Review code changes for bugs, correctness, security issues, and test coverage. Produces a structured inspection report. **Does not fix, commit, or push anything.** For the full fix loop, use `workflows/ticket-review-and-fix.md`.

Scope: PR number → use PR tools; branch name → `git diff --merge-base <base>`; uncommitted → `git diff`.

---

## Phase 1 — Scope and Context

**1. Determine scope** — identify the target: PR number, branch name, or uncommitted diff. For branches, identify the base (e.g., `main`). Only review changes in `git diff --merge-base <base>`.

**2. Extract ticket ID** — from branch name, PR title, or commits. Fetch from Jira (prefer CLI `acli`, fallback to MCP, then ask user). Label every Acceptance Criterion as `AC-1`, `AC-2`, … Flag vague or untestable ACs immediately.

**3. Fetch PR metadata (if PR exists)** — use `gh pr view` or GitHub MCP to get:
- PR description and linked ticket
- All review comments (resolved and unresolved)
- CI check status

---

## Phase 2 — Three-Signal Inspection

Run three independent inspections. Tag every finding with its signal source.

### S1: Inspect Against PR Acceptance Criteria

**4. Map each AC to code and tests.** For every AC:
- Locate the code that implements it.
- Locate the test that verifies it.
- Missing implementation = **Blocker (S1)**. Missing test = **Blocker (S1)**. Vague AC = **Ticket Quality Issue**.

### S2: Inspect Unresolved PR Comments

**5. Read ALL PR review comments** (via `gh pr view <N> --json reviews,comments` or GitHub MCP).
- Filter to unresolved / not-addressed comments.
- For each unresolved comment: verify whether the current code addresses it.
- Unaddressed actionable comment = **Blocker (S2)**.

### S3: Inspect Against Rules and Skills

**6. Load applicable rules and skills:**
- Generic rules and skills: `rules/code-rules.md`, `skills/security/SKILL.md`, `skills/testing/SKILL.md`, `skills/best-practices/SKILL.md`
- Language-specific skills: detect primary language from changed files and load the matching skill (e.g., `skills/java-best-practices/SKILL.md`, `skills/python-best-practices/SKILL.md`, `skills/js-ts-best-practices/SKILL.md`)
- Rubrics: `rubrics/code-review-checklist.md`, `rubrics/security.md`, `rubrics/architecture.md`
- Project-specific rules: any rules in the project's `.windsurf/rules/`, `.cursor/rules/`, or similar

**7. Evaluate the diff against the full checklist:**
- **Correctness & Logic** — NPEs, off-by-ones, edge cases (nulls, empty collections, missing records)
- **Security** — authorization on every new endpoint, injection, PII in logs, secrets, parameterized queries
- **Performance** — N+1 queries, blocking calls, log levels, payload sizes
- **Error Handling** — swallowed exceptions, meaningful messages, no sensitive data in logs
- **Backward Compatibility** — API contracts, message formats, shared databases, event schemas, downstream consumers
- **Operability** — logging quality, metrics impact, migration safety
- **Database Migrations** — naming convention, never modify committed migrations, indexes for FKs
- **Code Standards** — framework patterns, DI patterns, naming, duplication, dead code
- **Test Coverage** — every changed method has unit tests (happy path, edge cases, error conditions)
- **Files That Must Not Be Committed** — build output, IDE files, OS metadata, credentials

Each confirmed issue = **Blocker or Suggestion (S3)** per `rubrics/code-review-checklist.md` severity rules.

---

## Phase 3 — Present Findings

**8. Categorize and present all findings. Do NOT fix anything — report only.**

```
## Inspection Report
**PR/Branch**: X  **Ticket**: TICKET-ID  **Files reviewed**: N
**Verdict**: Approve / Request Changes

### S1 — AC Coverage
| AC | Description | Implemented? | Tested? | Code/Test |
|----|-------------|-------------|---------|-----------|
| AC-1 | ... | Yes/No | Yes/No | path:line |

### S2 — Unresolved PR Comments
| # | Author | Comment | Status | Action Needed |
|---|--------|---------|--------|---------------|

### S3 — Rules/Skills Findings
| Severity | Signal | File:Line | Issue | Suggested Remediation |
|----------|--------|-----------|-------|----------------------|
| Blocker  | S3     | ...       | ...   | ...                  |

### Ticket Quality Issues
(Vague ACs, untestable criteria, missing context)

### What Looks Good
(Acknowledge well-done aspects)
```

**9. Suggest next steps** — if Blockers exist, recommend running `ticket-review-and-fix` workflow. If clean, recommend proceeding to merge.

---

## Notes

- **This workflow produces a report only.** It does not fix code, run tests, commit, or push.
- Always read actual code — never review from memory.
- Only changes in the diff are in scope — do not flag pre-existing issues outside the diff unless they are blocking.
- API changes → note whether types need regeneration.
- Check test files too — tests can have bugs.
- To act on findings, run `workflows/ticket-review-and-fix.md`.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
