---
description: Review + fix + test + push loop for current branch changes
---

# Review and Fix Workflow

Review code changes, fix all issues, ensure tests pass, and push — in a single loop. Combines inspection, remediation, testing, and CI monitoring.

Scope: current branch changes only (diff against base branch).

---

## Phase 1 — Scope and Context

**1. Determine scope** — identify the current branch and its base (e.g., `main`). Only review changes in `git diff --merge-base <base>`.

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
- Generic rules: `rules/code-rules.md`, `rules/security.md`, `rules/testing.md`, `rules/best-practices.md`
- Language-specific rules: detect primary language from changed files and load the matching rule (e.g., `rules/java-best-practices.md`, `rules/python-best-practices.md`, `rules/js-ts-best-practices.md`)
- Rubrics: `rubrics/code-review-checklist.md`, `rubrics/security.md`, `rubrics/architecture.md`
- Project-specific rules: any rules in the project's `.windsurf/rules/`, `.cursor/rules/`, or similar

**7. Evaluate the diff against the full checklist:**
- **Correctness & Logic** — NPEs, off-by-ones, edge cases (nulls, empty collections, missing records)
- **Security** — authorization, injection, PII in logs, secrets, parameterized queries
- **Performance** — N+1 queries, blocking calls, log levels, payload sizes
- **Error Handling** — swallowed exceptions, meaningful messages, no sensitive data in logs
- **Backward Compatibility** — API contracts, message formats, shared databases
- **Operability** — logging quality, metrics impact, migration safety
- **Code Standards** — framework patterns, DI patterns, naming, duplication, dead code

Each confirmed issue = **Blocker or Suggestion (S3)** per `rubrics/code-review-checklist.md` severity rules.

---

## Phase 3 — Present Findings

**8. Categorize and present all findings before fixing:**

```
## Inspection Summary
**Branch**: X  **Ticket**: TICKET-ID  **Files reviewed**: N

### S1 — AC Coverage
| AC | Description | Implemented? | Tested? | Code/Test |
|----|-------------|-------------|---------|-----------|
| AC-1 | ... | Yes/No | Yes/No | path:line |

### S2 — Unresolved PR Comments
| # | Author | Comment | Status | Action |
|---|--------|---------|--------|--------|

### S3 — Rules/Skills Findings
| Severity | Signal | File:Line | Issue | Remediation |
|----------|--------|-----------|-------|-------------|
| Blocker  | S3     | ...       | ...   | ...         |

### Ticket Quality Issues
```

**9. Confirm with user before proceeding to fix** — if there are Blockers that require design decisions or clarifications, pause and ask.

---

## Phase 4 — Fix All Issues

**10. Fix every Blocker and actionable finding.** Process in order: S1 (AC gaps) -> S2 (PR comments) -> S3 (rules violations). For each fix:
- Read the actual source file (never fix from memory).
- Apply minimal, targeted fix — one issue at a time.
- Verify syntax with `python -m py_compile src/<file>.py`.
- Never batch unrelated fixes into one change.

**11. For S2 (PR comment) fixes** — note what changed and why, to reply to each comment after push.

---

## Phase 5 — Update PR and Documentation

**12. Update PR description** if scope or behavior changed during fixes.

**13. Update related documentation:**
- README, API docs, Swagger/OpenAPI specs if endpoints changed.
- Architecture docs if design changed.
- Configuration docs if new properties were added.
- Confluence pages if referenced in the ticket.

---

## Phase 6 — Unit Tests (100% Pass Required)

**14. Every changed/new method needs full unit test coverage.** Create test file if missing (mirror source path). Cover: happy path, edge cases, error conditions, all branches.

**15. Run unit tests and verify 100% pass:**
```bash
pytest
```

**16. Fix any failures immediately** — do NOT proceed until all unit tests are green.

---

## Phase 7 — Integration Tests (100% Pass Required)

**17. For API, cross-service, or DB changes** — ensure integration/system tests exist and cover the changed behavior.

**18. Run integration tests and verify 100% pass:**
```bash
pytest
```

**19. Fix any failures immediately** — do NOT proceed until all integration tests are green.

---

## Phase 8 — Final Test Gate

// turbo
**20. Run the full related test suite — zero failures allowed.**
```bash
pytest
```

If anything fails, go back to Phase 4.

---

## Phase 9 — User Approval Gate (MANDATORY)

**All fixes are complete and tests are green. STOP here and present a summary to the user.**

Present:
```
## Ready for Review
**Branch**: X  **Ticket**: TICKET-ID

### Changes Made
| # | File | Change Summary |
|---|------|---------------|

### Test Results
All tests passing: Yes/No

Awaiting your approval to commit and push.
```

**Do NOT proceed until the user explicitly approves.** If the user requests changes, go back to Phase 4 and re-run through Phase 8.

---

## Phase 10 — Commit and Push (5-Category Rule — MANDATORY)

Run the **commit-and-push** workflow (`workflows/commit-and-push.md`) in full. This is a mandatory gate — every execution of this workflow MUST produce a branch where ALL commits follow the 5-category rule.

---

## Phase 11 — Monitor CI Until Green

**21. Poll CI** using `gh pr checks <PR_NUMBER>` or GitHub MCP until all checks complete.

**22. CI green** — notify user. PR is ready for human review.

**23. CI fails** — diagnose and fix immediately:
1. Read the failure output.
2. Diagnose root cause.
3. Fix locally.
4. Re-run tests (Phase 8).
5. Commit and push (Phase 10).
6. Poll CI again.
7. **Loop until green. Do not stop on CI failure.**

**23a. If an automation PR review check fails** (e.g. IDE-integrated review bot; check name varies by org) — the bot often posts a review comment with Red/Yellow/Green findings. Run the **pr-automation-review** workflow (`workflows/pr-automation-review.md`) to triage, fix, and re-push. Then poll CI again.

**24. After every CI failure, update rules/workflows** to prevent recurrence (see `rules/ci-feedback-loop.md`).

---

## Notes

- Always read actual code — never review or fix from memory.
- Only changes in the branch diff are in scope — do not fix pre-existing issues outside the diff unless they are blocking.
- API changes -> regenerate types if applicable.
- Infrastructure/environment changes -> verify all environment configs are updated.
- DI configuration changes -> run full test suite.
- Check test files too — tests can have bugs.
- **Only stop when CI is fully green.**

### Multi-agent runs

- After **each phase** (1–11), print a concise **Phase N — result** summary before starting the next phase.
- See **`rules/ticket-review-and-fix-multi-agent.md`** for agent splits (S1/S2/S3), Windows shell pitfalls, exception-handling gotchas, datetime mocking limits, and Phase 9 safety.
