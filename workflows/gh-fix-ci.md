---
description: Diagnose and repair failing GitHub Actions checks on the current PR or branch
---

# GitHub CI fix workflow

Use when the user asks to fix CI, debug failing GitHub checks, or understand why a PR is red.

## Steps

1. Establish scope: PR number, failing checks, recent runs, and changed subsystems.
2. Verify GitHub CLI/API access before trusting check state: confirm auth for the repo host and workflow-readable scopes, and report the exact command if auth, API field drift, or rate limits block inspection.
3. Inspect GitHub Actions logs for actionable failures. Treat non-GitHub providers as external checks: report the check name and details URL, but do not invent provider-specific log scraping inside this generic workflow.
4. Once failing jobs are known, split **read-only** log inspection immediately by default (per job or failure family).
5. Do not pause before internal fanout unless there is a user-visible tradeoff or risky external side effect.
6. Map root cause to code, config, docs, environment, or workflow changes.
7. Apply minimal fixes and rerun relevant local checks.
8. **User Approval Gate** — present all changes to the user and **do NOT commit or push until explicitly approved.** Skip only if the user explicitly asked to skip approval.
9. Push, re-check CI, and loop until green.
10. If the failure reveals a reusable blind spot, capture it via `rules/ci-feedback-loop.md`.

See `rules/multi-agent-orchestration.md`.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
