---
description: Review code changes for bugs, correctness, security, and test coverage
---

# Code Review Workflow

Review code changes for bugs, correctness, security issues, and test coverage. Works with PRs, branches, or uncommitted diffs.

Scope: PR number → use PR tools; branch name → use `git log`; current changes → `git diff --stat && git diff`.

---

## Phase 1 — Identify What to Review

**1. Determine scope** — PR / branch / uncommitted diff.

**2. Read the ticket** — extract ticket ID from PR title/branch/commits. Fetch from Jira (via CLI or MCP). Label every AC as `AC-1`, `AC-2`, … Flag vague/untestable ACs immediately.

---

## Phase 2 — Code Review Checklist

**3. Correctness & Logic** — code matches ticket intent; no NPEs, off-by-ones, or bad conditionals; edge cases (nulls, empty collections, missing records) handled.

**4. Backend Standards** — follow project-specific backend rules (see `rules/` and project rules). Check code style, framework patterns, dependency injection patterns.

**5. Frontend Standards** — follow project-specific frontend rules. No `any` without justification. Generated API types preferred. Strings externalized. No unsafe HTML insertion.

**6. Security (CRITICAL)** — see `skills/security/SKILL.md` and `rubrics/security.md`. Authorization on every new endpoint. No PII in logs. No secrets in code. Parameterized queries only.

**7. Performance** — no N+1 queries; long ops offloaded to async workers; no blocking in request threads; appropriate log levels.

**8. Error Handling & Logging** — meaningful exception messages; no swallowed exceptions; no sensitive data in logs.

**8a. Backward Compatibility** — persisted payloads, event schemas, and public APIs may have **downstream consumers** (other services, jobs, mobile or web clients). Renaming or removing fields, enum-like string constants, or topic/message shapes without coordination is a **Blocker** unless versioned or feature-flagged per project policy. Adding optional fields is usually safe; verify migrations and consumers.

**9. Database Migrations** — correct naming convention; never modify committed migrations; backward compatible; indexes for FKs.

**10. Test Coverage** — every changed method has a unit test. Happy path, edge cases, error conditions. E2E updated if user-facing behavior changed. Named constants, no magic strings. Run tests to verify.

**11. Files That Must Not Be Committed** — build output, IDE files, OS metadata, credentials.

**12. AC Coverage** — for each AC, locate the code/test that satisfies it. No code → Blocker. No test → Blocker. Vague AC → Ticket Quality Issue.

---

## Phase 3 — Validate AC Coverage (100% Required)

**13. Verify every ticket AC is implemented** — map each AC to the code that satisfies it. Missing implementation = Blocker. Vague/untestable AC = flag and request clarification.

**14. Categorize findings** — Blockers (bugs, security, missing permissions, data loss, missing AC), Suggestions (style, refactors), Praise.

**15. Present the review:**

```
## Review Summary
**PR/Branch**: X  **Ticket**: TICKET-ID  **Files reviewed**: N  **Verdict**: Approve / Request Changes

### Blockers        ### Suggestions        ### What looks good

### AC Coverage
| AC | Description | Satisfied? | Code/Test |
|----|-------------|-----------|-----------|
| AC-1 | ... | ✅/❌ | path:line |

### Ticket Quality Issues    ### Test Assessment
```

---

## Phase 4 — Fix All Issues

**16. Fix every Blocker and inconsistency** — read the actual source file → apply minimal targeted fix → verify the fix compiles. One issue at a time, never batch unrelated fixes.

**17. Read and triage ALL PR comments (if PR exists):**
- Prioritize: Blockers → Required changes → Questions → Suggestions.
- Fix each actionable comment: read source → apply minimal fix → verify compile → run tests.
- Reply to every comment with what changed and why.

---

## Phase 5 — Add / Update Unit Tests

**18. Every changed/new method needs full unit test coverage.** Create test file if missing (mirror source path). Cover: happy path, edge cases, error conditions, all branches.

**19. Run and verify 100% pass.** Fix failures immediately — do NOT proceed until green.

---

## Phase 6 — Add / Update Integration Tests

**20. For API, cross-service, or DB changes** — ensure integration/system tests exist.

**21. Run and verify 100% pass.** Fix failures before proceeding.

---

## Phase 7 — Final Test Gate (100% Pass Required)

**22. Full related test suite — zero failures allowed.** If anything fails, go back to Phase 4.

// turbo
**22a. Run full test suite:**
```bash
pytest
```

---

## Phase 8 — Commit & Push

**23. Commit only after 100% green.** Verify `git status` excludes build output, IDE files, etc. Split unrelated changes into separate commits.

**23a. Check for cloud-sync duplicates** (blocking — see `rules/git-conventions.md § Duplicate-File Gate`):
```bash
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files before pushing" && exit 1
```

**24. Rebase before every push** (see `rules/git-conventions.md`). Re-check for duplicates after rebase.

**25. Push and create/update draft PR** with appropriate labels.

---

## Phase 9 — Monitor CI Until Green

**26. Poll CI** until all checks complete.

**27. CI green** → notify user, PR ready for human review.

**28. CI fails** → diagnose and fix immediately. Loop: read failure → diagnose root cause → fix locally → re-run tests → commit → push → poll again.

**29. After every CI failure, update rules/workflows** to prevent recurrence (see `rules/ci-feedback-loop.md`).

---

## Notes

- Always read actual code — never review from memory.
- API changes → regenerate types if applicable.
- Infrastructure/environment changes → verify all environment configs are updated.
- DI configuration changes (XML, modules, etc.) → run full test suite.
- Check test files too — tests can have bugs.
- **Only stop when CI is fully green.**
