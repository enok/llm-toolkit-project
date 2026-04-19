---
name: run-tests
description: Identify the right validation commands for a change set, split independent test planning and verification work in parallel, and run the smallest sufficient set of checks first before escalating to broader suites. Use when the user asks what to test or to verify a branch.
---

# Run Tests

Use this skill to choose and execute the right verification strategy for a change set.

## When to use
- The user asks to run or choose the right tests.
- A change spans backend, frontend, infra, or shared code.
- You need a minimal but safe validation plan before a PR or deployment.

## Parallel fanout
- Once the change surface is known, spawn the independent mapping lanes immediately by default.
- One subagent maps changed files to backend test scope.
- One subagent maps changed files to frontend, E2E, or visual scope.
- One subagent checks docs or config drift when behavior changes imply broader validation.
- Keep the actual command execution and final pass or fail judgment local.

## Validation order
1. Fast targeted checks.
2. Module or package-level checks.
3. Broader integration or E2E checks when the surface area demands it.
4. Full-suite escalation only when risk or failures require it.

## Outputs
- Ordered test plan with rationale.
- Commands run and outcomes.
- Remaining unverified areas, if any.

## Failure Classification
- Separate product verdict from environment or harness verdict in the final report.
- If scenario assertions pass and cleanup or teardown fails later, report the behavioral proof and the cleanup blocker separately.
- If a shared setup step such as a global `before all` fails before scenarios execute, report the run as environment-blocked rather than feature-failed.

## Evidence Hand-off
- When the repo family provides a specialized evidence-capture skill for user-visible proof, hand the artifact work to that specialist skill instead of treating it as generic test execution only.
