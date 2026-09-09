---
name: review-and-fix
description: Review a diff, split independent investigation and fix work across subagents, apply scoped fixes, and converge on a verified result. Use when the user asks to review and fix code, address PR feedback end-to-end, or drive a branch to review-ready.
---

# Review and Fix

Use this skill as a multi-agent orchestrator for high-signal review and remediation work.

## When to use
- The user asks to "review and fix" a branch, PR, or staged changes.
- The task includes both diagnosis and implementation.
- Multiple independent findings or subsystems can be explored in parallel.

## Orchestration pattern
1. Establish scope first: diff, base branch, ticket, comments, CI state, and changed subsystems.
   - For branch-diff scope, use either `git diff origin/<base>...HEAD` or `git diff --merge-base origin/<base> HEAD`. Do not combine `--merge-base` with a `A...B` range.
   - Before planning or editing, read the repo-root `AGENTS.md` and the closest applicable `CLAUDE.md` files, and scan any task-matching repo-local skill playbooks (`SKILL.md` files) when they exist.
2. Treat GitHub pipeline state as a first-class signal. If a PR exists or checks are available, inspect them early and keep monitoring them during the loop.
3. Once scope is clear, spawn the independent lanes immediately by default and report each lane or phase result as soon as it finishes. Do not ask for permission to use multiple agents unless a user-visible tradeoff or unsafe side effect requires a decision.
4. Keep the immediate blocking path local.
5. Fan out only independent work:
   - `$review` for diff findings and risk clustering
   - `$task-starter` or `$ticket-research` for ticket and AC context when needed
   - `$testing` or `$test-plan` for missing coverage analysis
   - `$doc-delta` for docs drift when behavior or config changed
   - `$gh-fix-ci` for failing GitHub Actions checks and log inspection
   - a repo-specific evidence skill when the active profile requires proof artifacts
   - language or domain specialists (`$java-best-practices`, `$js-ts-best-practices`, `$python-best-practices`, `$react-best-practices`, `$security`, `$terraform`, `$cloudformation`) for focused standards review
6. When implementing, split write ownership by disjoint file sets. Never run two fixers on the same files.
7. Treat phase reporting as mandatory. After each completed phase, publish a short update with status, findings or fixes, validation, blockers, and next step.
   - When the repo also provides a review-and-fix workflow or numbered phase script, mirror that workflow's exact phase count and labels in all progress and final reporting. Do not collapse numbered phases into fewer ad hoc buckets.
8. If any phase exposes a mistake, blind spot, or repeatable miss in the agent workflow, run the config-evolution loop from `rules/ci-feedback-loop.md` before closing the task:
   - classify the root cause and decide whether prevention belongs in a rule, workflow, or skill
   - improve an existing shared artifact in `agent-skills` when possible
   - create a new shared skill or workflow when the failure reveals a reusable blind spot
   - use `$skill-creator` when designing or restructuring a reusable skill
   - use `$skill-installer` when a mature external skill is a better shared solution than inventing a new one
   - treat CI failures as a common trigger for this loop, not the only one
9. Whenever a PR exists or will be created, review the PR description (title, summary, affected files, validation evidence, proof state) against `rules/git-conventions.md` and `skills/documentation-reviewer/SKILL.md` on the initial draft and again after every later revision that changes the diff, affected files, validation, or proof state. Review the live or draft PR title/body, and update it if the summary is stale, noisy, vague, or inconsistent with the current branch state.
10. Finish with a single local verification pass: targeted tests, sanity check of the diff, CI status, latest PR description refresh status, and a concise summary of what changed, what config artifacts evolved, and what remains risky. If the branch is ready to share and no PR exists yet, create it instead of reporting PR and CI phases as blocked. Missing PR state is temporary, not a completion condition.
   - In JS/TS repos that enforce dead-export or unused-export checks, do not export helper functions solely for testability. Test through public exports or run the repo’s dead-export signal before pushing.
11. When the active repo family requires proof artifacts, do not stop at green tests. Ensure each UI-visible workflow has appropriate proof, finish with the repo-specific evidence package when one exists, and report whether evidence was attached or not applicable.
12. When the diff touches shared BDD step definitions, shared test harness adapters, or other reused test helpers, explicitly scan committed consuming specs before treating the change as covered. Untracked scratch specs and temporary files do not count as validation or evidence.

## Parallel safety rules
- Do not parallelize edits to overlapping files.
- Do not delegate the next immediate blocking step if local progress depends on it.
- Use subagents for sidecar analysis, file-local fixes, and test or docs verification.
- Aggregate findings before editing so fixes stay minimal and coherent.

## Outputs
- Clear finding clusters with severity and file ownership.
- Phase-by-phase progress notes, published as each phase completes.
- When a repo-local workflow defines numbered phases, progress and final notes must preserve those exact phase numbers and labels.
- Implemented fixes when the user asked for execution, not just a report.
- Verification notes: what was run, what passed, what remains unverified.
- PR description notes when applicable: whether the PR title/body was reviewed on the initial draft and each later revision, what was updated, or why the rule did not apply.
- Evidence notes when applicable: evidence identifier, artifact paths, video-evidence applicability, and attachment status.
- Config evolution notes: which shared rules, workflows, or skills were improved, created, or installed because a reusable gap was exposed.
