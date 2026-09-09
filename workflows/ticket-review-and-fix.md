---
description: Review + fix + test + push loop for current branch changes
---

# Review and Fix Workflow

Review code changes, fix all issues, ensure tests pass, and push — in a single loop. Combines inspection, remediation, testing, and CI monitoring.

Scope: current branch changes only (diff against base branch).

---

## Phases 1–3 — Scope, Inspect, Present (delegated)

**1–8. Run `workflows/ticket-review.md` Phases 1–3 in full** — scope and ticket
context, the three-signal inspection (S1 AC coverage, S2 unresolved PR
comments, S3 rules/skills checklist), and the categorized findings report.
That workflow owns the canonical S3 checklist and report format; do not
maintain a diverging copy here.

**9. Confirm with user before proceeding to fix** — if there are Blockers that require design decisions or clarifications, pause and ask.

---

## Phase 4 — Fix All Issues

**10. Fix every Blocker and actionable finding.** Process in order: S1 (AC gaps) -> S2 (PR comments) -> S3 (rules violations). For each fix:
- Read the actual source file (never fix from memory).
- Apply minimal, targeted fix — one issue at a time.
- Verify syntax with the stack's cheapest check (e.g. `python -m py_compile`, `node --check`, `mvn -q compile`); detect the stack per `workflows/run-tests.md`.
- Never batch unrelated fixes into one change.

**11. For S2 (PR comment) fixes** — note what changed and why, to reply to each comment after push.

---

## Phase 5 — Update PR and Documentation

**12. Update PR description** if scope or behavior changed during fixes. Always
reconcile the mandatory per-file **File changes** table against the current
base-to-head diff, even when the prose summary did not otherwise need an update.
Require one accurate row per added, modified, deleted, or renamed path and read
the body back after editing; follow
`rules/git-conventions.md § PR File Change Table`.

**13. Update related documentation:**
- README, API docs, Swagger/OpenAPI specs if endpoints changed.
- Architecture docs if design changed.
- Configuration docs if new properties were added.
- Confluence pages if referenced in the ticket.

---

## Phase 6 — Unit Tests (100% Pass Required)

**14. Every changed/new method needs full unit test coverage.** Create test file if missing (mirror source path). Cover: happy path, edge cases, error conditions, all branches.

**15. Run unit tests and verify 100% pass** — detect the stack and use its
unit-test command per `workflows/run-tests.md` (e.g. `pytest`, `mvn test`,
`npm test`).

**16. Fix any failures immediately** — do NOT proceed until all unit tests are green.

---

## Phase 7 — Integration Tests (100% Pass Required)

**17. For API, cross-service, or DB changes** — ensure integration/system tests exist and cover the changed behavior.

**18. Run integration tests and verify 100% pass** — use the stack's
integration-test command per `workflows/run-tests.md` (e.g. `pytest -m integration`,
`mvn verify`, `npm run test:integration`).

**19. Fix any failures immediately** — do NOT proceed until all integration tests are green.

---

## Phase 8 — Final Test Gate

// turbo
**20. Run the full related test suite — zero failures allowed.** Use the
stack's full-suite command per `workflows/run-tests.md` (e.g. `pytest`,
`mvn clean verify`, `npm test`).

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

## Phase 10 — Commit and Push (Semantic Organization — MANDATORY)

Run the **commit-and-push** workflow (`workflows/commit-and-push.md`) in full. This is a mandatory gate — every execution MUST produce a branch whose commits follow the canonical semantic categories and regrouping safeguards.

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
- See **`rules/multi-agent-orchestration.md`** for parallel agent splits and safe fanout.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
