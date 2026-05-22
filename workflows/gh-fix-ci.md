---
description: Diagnose and repair failing GitHub Actions checks on the current PR or branch
---

# GitHub CI fix workflow

Use when the user asks to fix CI, debug failing GitHub checks, or understand why a PR is red.

## Steps

1. Establish scope: PR number, failing checks, recent runs, and changed subsystems.
2. Once failing jobs are known, split **read-only** log inspection immediately by default (per job or failure family).
3. Do not pause before internal fanout unless there is a user-visible tradeoff or risky external side effect.
4. Map root cause to code, config, docs, environment, or workflow changes.
5. Apply minimal fixes and rerun relevant local checks.
6. **User Approval Gate** — present all changes to the user and **do NOT commit or push until explicitly approved.** Skip only if the user explicitly asked to skip approval.
7. Push, re-check CI, and loop until green.
8. If the failure reveals a reusable blind spot, capture it via `rules/ci-feedback-loop.md`.

See `rules/multi-agent-orchestration.md`.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
