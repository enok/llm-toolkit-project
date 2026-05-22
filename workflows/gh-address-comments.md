---
description: Address actionable GitHub PR review comments and drive threads toward resolution
---

# GitHub PR comments workflow

Use when the user asks to address PR comments, resolve review feedback, or clean up open review threads.

## Steps

1. Establish scope: PR, open review threads, changed files, and any linked CI failures.
2. Once independent threads are known, split analysis immediately by file, subsystem, or comment cluster.
3. Do not pause before internal fanout unless there is a user-visible tradeoff or overlapping write ownership.
4. Map each actionable thread to code, tests, docs, or explanation changes.
5. Apply minimal fixes, rerun relevant checks, and prepare concise thread replies with fix references.
6. **User Approval Gate** — present all changes to the user and **do NOT commit or push until explicitly approved.** Skip only if the user explicitly asked to skip approval.

See `rules/multi-agent-orchestration.md`.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
