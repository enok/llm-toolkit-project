---
trigger: always_on
description: CI failure to rule update continuous improvement cycle
---

# CI Pipeline Feedback Loop — Continuous Improvement

## Principle

Every CI pipeline failure is an opportunity to improve the review process. When a PR pipeline fails, the root cause must be analyzed and the corresponding rule or workflow must be updated so that **future reviews catch the same class of error before the PR is even opened**.

## Mandatory Process

When validating a PR pipeline execution and encountering a failure:

1. **Diagnose the root cause** — identify exactly what caused the CI check to fail (e.g., missing config, lint violation, missing import, stale types, etc.).

2. **Fix the immediate issue** — apply the minimal fix to make CI green.

3. **Identify the prevention rule** — ask: *"What rule or checklist item, if it existed during the code review phase, would have caught this error before the PR was opened?"*

4. **Update the appropriate rule or workflow file:**
   - SQL/migration errors → update the review workflow or create a dedicated rule.
   - Lint/style errors → update the review workflow's code standards checklist.
   - Missing permissions → update security rules or review workflow.
   - Test failures → update testing rules or review workflow.
   - Build/compile errors → update code rules or backend/frontend rules.
   - New category → create a new rule file if no existing file covers the error class.

5. **Propagate the change** — if the rule applies to multiple repositories, update the rule in ALL relevant repos.

6. **Document** — add the CI failure and the rule update to the review or PR documentation.

## Key Rule

**Never let the same class of CI error happen twice.** If CI catches it once, the review workflow must catch it forever after.
