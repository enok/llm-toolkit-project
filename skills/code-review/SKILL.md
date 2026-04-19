---
name: code-review
description: |
  Perform code review for bugs, correctness, security, and test coverage. Use for
  PR reviews, branch reviews, staged changes, or architecture/security review.
license: MIT
---

# Code Review

Review code changes for bugs, correctness, security issues, and test coverage.

> **Reference**: For the complete workflow, see `workflows/review.md`

## Quick Reference

### Phase 1 — Identify What to Review
1. Determine scope: PR / branch / uncommitted diff
2. Read the ticket — extract ACs, label as AC-1, AC-2, etc.
3. Flag vague/untestable ACs immediately

### Phase 2 — Review Checklist

| Category | What to Check |
|----------|---------------|
| **Correctness** | Code matches intent; no NPEs, off-by-ones, bad conditionals |
| **Standards** | Follow project-specific rules (see `rules/`) |
| **Security** | Auth on every endpoint, no PII in logs, no secrets in code |
| **Performance** | No N+1 queries, long ops async, appropriate log levels |
| **Error Handling** | Meaningful exceptions, no swallowed errors, no sensitive data |
| **Backward Compat** | API/migration changes don't break downstream consumers |
| **Test Coverage** | Every changed method tested; happy path, edge cases, errors |
| **AC Coverage** | Map each AC to code that satisfies it |

### Phase 3 — Report Format

**Red (Blocker)** — Must fix before merge
**Yellow (Should fix)** — Recommend addressing
**Green (Nice-to-have)** — Consider if time permits

Each finding needs:
- File and line reference
- What the issue is
- Why it matters
- Suggested remediation

## When to Apply

- User asks to "review my changes" or "review my code"
- Reviewing a PR or branch
- Architecture or security review needed
- Full pre-PR check (pair with `pre-pr-check` workflow)

## Related

- `workflows/review.md` — Step-by-step review workflow
- `rubrics/code-review-checklist.md` — Evaluation categories
- `rubrics/security.md` — Security-specific checks
- `rubrics/architecture.md` — Architecture review criteria
