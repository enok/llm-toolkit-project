---
description: Run validation, review, and docs pass before opening or updating a PR
---

# Pre-PR check workflow

Use when the user is ready for a PR, wants a full branch check, or wants a review-ready summary before pushing. Prefer the **pre-pr-check** skill when it matches the IDE.

## Steps

1. Establish scope: diff, base branch, ticket, and intended PR surface.
2. **Check for cloud-sync duplicates** (blocking — see `rules/git-conventions.md § Duplicate-File Gate`):
   ```bash
   git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files before pushing" && exit 1
   ```
   If any are found, `git rm` them and verify originals before proceeding.
3. Once scope is known, split independent lanes **immediately by default**:
   - validation command selection and execution
   - diff review and risk clustering
   - docs or config drift
   - security or release-impact checks when relevant
4. Do not pause before internal fanout unless there is a user-visible tradeoff, risky external side effect, or overlapping write ownership.
5. Run the smallest safe validation set, then broaden only when needed.
6. If source code was created or updated, run the blocking
   **changed-code-quality-gate** workflow with the trusted PR base. A
   worktree-only scope run cannot validate committed branch changes.
7. Build or validate the mandatory per-file **File changes** table from
   `git diff --name-status --find-renames origin/<base>...HEAD`. Require exact
   path coverage and file-specific purposes as defined by
   `rules/git-conventions.md § PR File Change Table`.
8. Produce one summary with blockers, warnings, follow-up fixes, and readiness status.

See `rules/multi-agent-orchestration.md`.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
