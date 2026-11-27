---
description: Run validation, review, and docs pass before opening or updating a PR
---

# Pre-PR check workflow

Use when the user is ready for a PR, wants a full branch check, or wants a review-ready summary before pushing. This file holds the procedure the **pre-pr-check** skill runs.

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
5. Run the repo's lint and tests (infer from `package.json`, `Makefile`, `pom.xml`, or ask); on failure report and stop. Run the smallest safe set, then broaden only when needed.
6. If source code was created or updated, run the blocking
   **changed-code-quality-gate** workflow with the trusted PR base. A
   worktree-only scope run cannot validate committed branch changes.
7. Build or validate the mandatory per-file **File changes** table from
   `git diff --name-status --find-renames origin/<base>...HEAD`. Require exact
   path coverage and file-specific purposes as defined by
   `rules/git-conventions.md § PR File Change Table`.
8. If the branch adds a skill, workflow, rule, or agent, run the value gate
   (blocking; see `workflows/resource-value-check.md`):
   ```bash
   python3 scripts/check_value_checks.py --base origin/<base>
   ```
9. Optional Snyk: if the user wants security scanning and `snyk` is available, run `snyk test`; report critical findings, block on non-critical only when the user asks.
10. UI verification, when the diff touches front-end UI and the user has not waived browser verification: read `docs/jira/<TICKET>/ui-verify-report.md`. `pass` continues; `fail` or `blocked` is a pre-PR blocker unless waived. UI changed with no report: Yellow finding recommending **ui-verify** before merge.
11. In-agent review of the branch diff per `skills/ticket-review/SKILL.md` (rubrics, Red/Yellow/Green findings, `review.md` and `review-report.json` under `docs/jira/<TICKET>/`). Result: fail on any Red finding or blocking gate failure, neutral on Yellow/Green only, pass with no findings.
12. Produce one summary with blockers, warnings, follow-up fixes, and readiness status.

See `rules/multi-agent-orchestration.md`.

---

## Final Step — Self-improvement

Run the per-run retrospective (`workflows/run-retrospective.md`) before closing this workflow.
