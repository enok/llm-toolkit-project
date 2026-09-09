---
name: e2e-release-verification
description: >
    Pick and run the smallest relevant E2E or regression verification for a change or release.
    Trigger when a user asks what E2E tests to run, how to verify a release, how to compare
    failures against prior runs, or how to scope regression coverage by environment, tenant,
    or change surface.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# E2E Release Verification

Use this skill for targeted release validation instead of blanket "run everything".

## When to Apply

- Verifying a release candidate before deployment
- Choosing which E2E tests to run for a specific change
- Comparing test failures against prior known failures
- Scoping regression coverage by environment or change surface

## Workflow

1. **Map the change to affected surfaces:**
   - endpoint or API
   - UI workflow
   - tenant or product line
   - integrations or third-party behavior
2. **Select the smallest defensible suite:**
   - smoke tests for quick confidence
   - workflow-specific regression for targeted coverage
   - environment-specific checks when applicable
   - nightly-only coverage when appropriate
3. **Compare failures to prior known failures** when historical data exists.
4. **Separate net-new regressions from chronic flakes** or already-known breakage.
5. **Summarize what is covered, what is intentionally not covered, and residual release risk.**

## Output

Return:
- selected suites or tags with rationale
- results summary
- net-new failures vs known flakes
- remaining gaps and residual risk

## Non-Goals

- Do not run the entire test suite when a targeted slice is sufficient.
- Do not ignore flaky test history — distinguish real regressions from noise.

## Related Skills

- **release-manager** — E2E verification is one step in the release workflow
- **testing** — Test patterns and coverage strategy
- **run-tests** workflow — General test execution
