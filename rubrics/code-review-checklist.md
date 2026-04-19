# Code Review Checklist Rubric

Holistic review categories, evidence rules, and response format. Use this as the master checklist when performing structured code reviews.

---

## Severity Levels

| Level | Label | Definition | Action |
|-------|-------|------------|--------|
| **S1** | Blocker | Bug, security hole, data loss, missing permission check, broken AC, silent failure | Must fix before merge |
| **S2** | Unresolved Comment | Open PR comment not addressed or not explicitly deferred | Must resolve or defer with justification |
| **S3** | Suggestion | Style, naming, refactor opportunity, non-critical coupling | Should address; can defer with note |
| **S4** | Praise | Notable quality, good pattern reuse, clear naming | No action needed |

A PR may only be approved when all S1 and S2 items are resolved.

---

## Review Categories

### 1. AC Coverage (S1 if missing)

- Every acceptance criterion maps to at least one code path **and** at least one test.
- Vague or untestable ACs are flagged as Ticket Quality Issues (not S1, but must be clarified).
- Missing implementation for a stated AC = **Blocker**.
- Missing test for an implemented AC = **Blocker**.

### 2. Correctness & Logic

| Check | Severity |
|-------|----------|
| NPE / null dereference on untrusted input | S1 |
| Off-by-one in loop or range | S1 |
| Wrong operator (`<` vs `<=`, `=` vs `==`) | S1 |
| Unreachable branch or dead code | S3 |
| Collection mutated while iterating | S1 |
| Edge case (empty list, zero, negative, max value) unhandled | S1 |
| Incorrect aggregation or join key | S1 |

### 3. Security (see also `rubrics/security.md`)

| Check | Severity |
|-------|----------|
| Missing authorization check on new endpoint/action | S1 |
| User-controlled input used in query/command without sanitization | S1 |
| PII logged | S1 |
| Hardcoded secret or credential | S1 |
| Exception message leaking stack trace or infrastructure detail to client | S1 |
| SSRF or open redirect with user-controlled URL | S1 |

### 4. Performance

| Check | Severity |
|-------|----------|
| N+1 query (DB/HTTP call inside a loop) | S1 |
| Synchronous external call blocking a request thread | S1 |
| Unbounded query without pagination or limit | S1 |
| Excessive debug logging in hot path | S3 |
| Unused index or missing index on FK | S3 |

### 5. Error Handling & Logging

| Check | Severity |
|-------|----------|
| Swallowed exception (empty catch) | S1 |
| Catch too broad (`Exception`, `Throwable`) without re-throw | S1 |
| No context in exception message (what failed, for what input) | S3 |
| Missing `exc_info=True` / `e` on error log | S3 |
| Log without correlation ID in service context | S3 |

### 6. Backward Compatibility

| Check | Severity |
|-------|----------|
| Renaming/removing a field in persisted payload or API without migration | S1 |
| Changing enum/string constant value without consumer coordination | S1 |
| Adding a required field to existing schema | S1 |
| Changing message/event topic name | S1 |
| Adding optional field (generally safe) | — |

### 7. Test Coverage

| Check | Severity |
|-------|----------|
| New/changed method with no unit test | S1 |
| Happy path only — no edge cases or exception paths | S1 |
| Test relies on hidden shared mutable state | S1 |
| Magic literals in tests (not named constants) | S3 |
| Duplicate test setup not extracted to fixture | S3 |
| E2E test not updated for user-facing behaviour change | S1 |

### 8. Code Standards

| Check | Severity |
|-------|----------|
| Naming doesn't reveal intent | S3 |
| Function > 30 lines / doing more than one thing | S3 |
| Deep nesting (> 3 levels) | S3 |
| Magic number or string not extracted to constant | S3 |
| Duplicated business logic (rule of three) | S3 |
| `TODO` / `FIXME` without ticket reference | S3 |

### 9. Files That Must Not Be Committed

| Check | Severity |
|-------|----------|
| Build output (`target/`, `dist/`, `build/`) | S1 |
| Credentials or `.env.local` | S1 |
| Cloud-sync duplicate files (`file (1).md`) | S1 |
| IDE files (`.idea/`, `.vscode/`) | S3 |
| Notebook outputs when not intentional review artifact | S3 |

---

## Review Response Format

```
## Review Summary
**PR/Branch**: X  **Ticket**: TICKET-ID  **Files reviewed**: N  **Verdict**: Approve / Request Changes

### S1 — Blockers
| # | File:Line | Category | Issue | Remediation |
|---|-----------|----------|-------|-------------|

### S2 — Unresolved Comments
| # | Author | Comment | Status |
|---|--------|---------|--------|

### S3 — Suggestions
| # | File:Line | Category | Issue |
|---|-----------|----------|-------|

### S4 — Praise
...

### AC Coverage
| AC | Description | Implemented? | Tested? | Evidence |
|----|-------------|-------------|---------|----------|

### Ticket Quality Issues
...

### Test Assessment
...
```

---

## Evidence Rules

- Every finding must cite a **file path and line number** (or diff hunk).
- Never assert a finding without reading the actual source — verify method signatures, return types, and field names.
- Praise must also cite evidence — name the specific pattern or file that is well-done.
- If a finding cannot be confirmed by reading the diff or source, mark it as a question, not a blocker.
