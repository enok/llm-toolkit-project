# Code Review Checklist Rubric

Use this checklist when performing a holistic, evidence-based AI diff review
(the **code-review**, **review**, **ticket-review**, or **pre-pr-check**
skill). Evaluate the staged diff (or branch diff) against the categories
below; apply only where the changed code is relevant. Base every finding on
concrete evidence in the diff or the source it touches.

**Rubrics:** for **architecture** and **security**, use the detailed
criteria in `rubrics/architecture.md` and `rubrics/security.md`; this file
defines the overall categories, severity levels, evidence rules, and
response format.

---

## Severity Levels

| Level | Definition | Action |
|-------|------------|--------|
| **Red** (Blocker) | Security vulnerability, correctness bug, data-loss risk, broken contract, missing or bypassable authorization check, a broken acceptance criterion, a silent failure, or an open PR review comment not yet addressed or explicitly deferred | Must fix - or be explicitly deferred with justification - before merge |
| **Yellow** (Suggestion) | Important maintainability, design, performance, or testing gap that is not merge-blocking | Should address; may defer with a note |
| **Green** (Nice-to-have) | Polish, clarity, or a minor improvement; may also call out a notably good pattern worth praising | No action needed |

Elsewhere in this toolkit these levels are also labeled `S1` (Red/Blocker)
and `S3` (Yellow or Green/Suggestion). A PR may only be approved once every
Red finding is fixed or explicitly deferred with justification by whoever
owns the merge decision.

---

## Review Categories

Evaluate correctness, security, architecture/design, maintainability,
performance, testing, and operability. Provide high-signal, actionable
feedback that improves overall code quality and reduces production risk.

### 1. AC Coverage

- Every acceptance criterion maps to at least one code path **and** at least one test.
- A vague or untestable AC is a Ticket Quality Issue, not itself Red - flag it and ask for clarification rather than guessing.
- Missing implementation for a stated AC - **Red**.
- Missing test for an implemented AC - **Red**.

### 2. Correctness & Robustness

| Check | Severity |
|-------|----------|
| Null/undefined dereference on untrusted input | Red |
| Off-by-one in a loop or range | Red |
| Wrong operator (`<` vs `<=`, `=` vs `==`) | Red |
| Collection mutated while iterating | Red |
| Edge case (empty list, zero, negative, max value) unhandled | Red |
| Incorrect aggregation or join key | Red |
| Race condition or unclear ordering guarantee on shared/concurrent state | Red |
| Unreachable branch or dead code | Yellow |

Also see the dedicated **Backward Compatibility** category below, and
`rubrics/architecture.md`, for contract, schema, and wire-format changes -
including separate wire-contract and source/binary compatibility for shared
libraries.

### 3. Security

See the detailed criteria in **`rubrics/security.md`** (injection,
authentication/authorization, secrets, cryptography, PII, web security,
dependencies).

| Check | Severity |
|-------|----------|
| Missing authorization check on a new endpoint or action | Red |
| User-controlled input used in a query/command/path without sanitization | Red |
| PII or a secret logged | Red |
| Hardcoded secret or credential | Red |
| Exception message leaking a stack trace or infrastructure detail to a client | Red |
| SSRF or open redirect with a user-controlled URL | Red |

### 4. Architecture & Design

See the detailed criteria in **`rubrics/architecture.md`** (layering and
boundaries, separation of concerns, dependency injection, transaction
safety, coupling and cohesion, API and contract design, data design,
resilience).

### 5. Performance

| Check | Severity |
|-------|----------|
| N+1 query (DB/HTTP call inside a loop) | Red |
| Synchronous external call blocking a request thread | Red |
| Unbounded query without pagination or a limit | Red |
| Excessive debug logging in a hot path | Yellow |
| Missing index on a foreign key that is queried | Yellow |

### 6. Error Handling & Operability

| Check | Severity |
|-------|----------|
| Swallowed exception (empty catch) | Red |
| Catch too broad (`Exception`/`Throwable`) without re-throw | Red |
| Migration or rollout step without a documented rollback path | Red |
| No context in an exception message (what failed, for what input) | Yellow |
| Missing the caught exception (`exc_info=True` or equivalent) on an error log | Yellow |
| Log without a correlation/request ID in a service context | Yellow |

Logging must stay useful without being noisy, and must never carry sensitive
data - redact or omit PII and high-risk identifiers before they reach logs.
Note metrics/tracing impact where relevant.

### 7. Backward Compatibility

| Check | Severity |
|-------|----------|
| Renaming/removing a field in a persisted payload or API without a migration | Red |
| Changing an enum/string constant value without consumer coordination | Red |
| Adding a required field to an existing schema | Red |
| Changing a message/event topic or queue name | Red |
| Adding an optional field | - (generally safe) |

### 8. Test Coverage

| Check | Severity |
|-------|----------|
| New/changed method with no unit test | Red |
| Happy path only - no edge cases or exception paths | Red |
| Test relies on hidden shared mutable state | Red |
| An end-to-end test not updated for a user-facing behavior change | Red |
| Magic literals in tests instead of named constants | Yellow |
| Duplicate test setup not extracted to a fixture | Yellow |

Also flag missing negative/regression tests, a mismatch between the test
level chosen (unit/integration/e2e) and what the change needs, and flaky or
non-deterministic test risk.

### 9. Code Standards

| Check | Severity |
|-------|----------|
| Naming that doesn't reveal intent | Yellow |
| Function doing more than one thing, or well over ~30 lines | Yellow |
| Deep nesting (more than ~3 levels) | Yellow |
| Magic number or string not extracted to a constant | Yellow |
| Duplicated business logic (rule of three) | Yellow |
| `TODO`/`FIXME` without a ticket reference | Yellow |

Also check readability, consistency with repo standards, correct use of
framework/language idioms, and missing or outdated documentation where
behavior changes.

### 10. Files That Must Not Be Committed

| Check | Severity |
|-------|----------|
| Build output (`target/`, `dist/`, `build/`) | Red |
| Credentials or a `.env.local`-style secret file | Red |
| Cloud-sync duplicate files (`file (1).md`) | Red |
| Notebook outputs, when not an intentional review artifact | Yellow |
| IDE-local files (`.idea/`, `.vscode/`) | Yellow |

---

## Evidence Rules

- Base every finding on concrete evidence in the diff or the source it
  touches - never assert a finding without reading the actual code (verify
  method signatures, return types, and field names).
- Separate confirmed issues from uncertain concerns; if a finding cannot be
  confirmed, mark it as a question, not a Red.
- If uncertain, clearly state assumptions and the validation still required.
- Avoid speculative or style-only nitpicks unless they meaningfully improve
  clarity or maintainability.
- A Green finding that praises good work must also cite evidence - name the
  specific pattern or file that is well done.

---

## Response Format

Post findings grouped by severity:

```text
## Review Summary
**PR/Branch**: <name>  **Ticket**: <TICKET-ID>  **Files reviewed**: N  **Verdict**: Approve / Request Changes

### Red - Must Fix
| # | File:Line | Category | Issue | Remediation |
|---|-----------|----------|-------|--------------|

### Yellow - Should Fix
| # | File:Line | Category | Issue | Remediation |
|---|-----------|----------|-------|--------------|

### Green - Nice-to-Have
| # | File:Line | Category | Note |
|---|-----------|----------|------|

### AC Coverage
| AC | Description | Implemented? | Tested? | Evidence |
|----|-------------|---------------|---------|----------|

### Ticket Quality Issues
<vague or untestable ACs, missing context>

### Test Assessment
<coverage summary, gaps, flaky/non-deterministic risks>
```

For each finding include **What/Where** (file and function/line), **why it
matters**, and **concrete remediation guidance**. Include test
recommendations when applicable.

If no high-confidence issues are found, post a concise "no high-confidence
issues found" comment (optionally with a few Green suggestions or praise).

Do not push changes or open fix PRs from this workflow - report findings and
let the developer, or the **fix** skill on request, apply them.

### Check Run Status

- **Fail** if any Red findings.
- **Neutral** if only Yellow/Green findings.
- **Pass** if no findings.

---

## Structured Report (`review-report.json`)

When writing `docs/jira/<TICKET>/review-report.json` (or
`docs/jira/review/review-report.json` when no ticket is clear), include a
`findings` array. Each finding should have:

- **type** (severity): `"blocker"` (Red), `"suggestion"` (Yellow), or `"nice-to-have"` (Green)
- **file**: path to the file (or `null`)
- **line**: line number if relevant (or `null`)
- **message**: what the issue is
- **suggestion**: concrete remediation (optional)

Include a **summary** (for example, counts of blockers/suggestions and the
overall pass/fail/neutral verdict). This lets the **fix** skill prioritize
and act on findings.
