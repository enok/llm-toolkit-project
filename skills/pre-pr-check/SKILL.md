---
name: pre-pr-check
description: "Run full pre-PR check — repo validations (lint/tests), the changed-code quality gate, optional Snyk, UI-verify report check, and in-agent AI review. Use when ready for PR, 'check my changes,' 'about to push,' or 'pre-PR check this branch' (branch checked out, no staging)."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Pre-PR Check

Full pre-PR validation of the checked-out branch: lint and tests, duplicate-file gate, the changed-code quality gate, PR file-change table, value gate, optional Snyk, UI-verify report gate and in-agent review. Follow `workflows/pre-pr-check.md`, which holds the procedure.
