---
title: OWASP security report template
tags: [owasp, security-report, template, findings]
---

# OWASP Security Report Template

Copy the block below into the report file (default `docs/security/<repo-or-dir-name>-security-report.md`) and fill every field; delete nothing, write `n/a` instead.

```markdown
# Security Review: <repo-or-scope>

## Executive Summary

- Scope:
- Overall risk:
- Highest priority action:

## Coverage

- Inspected:
- Not inspected:
- Local checks run:
- Checks unavailable:

## Findings

### <ID>: <short title>

- Severity:
- OWASP mapping:
- Status: Open
- Evidence: `<file>:<line>`
- Impact:
- Recommended fix:
- Validation:
- Confidence:

## Observations

Use this section for non-blocking hardening notes that are not confirmed vulnerabilities.

## Prioritized Next Steps

1. Fix confirmed high-risk findings.
2. Run missing dependency or runtime checks.
3. Re-test fixed paths and update this report.
```
