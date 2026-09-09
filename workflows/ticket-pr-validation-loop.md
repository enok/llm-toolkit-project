---
description: Validate a solved ticket and drive the related PR through comments, CI/CD, fixes, and final approval readiness
---

# Ticket PR Validation Loop

Use this for a recurring or user-triggered automation bound to one ticket after
implementation appears solved. The goal is a current, evidence-backed
approve-or-block call for the ticket's PR, plus the smallest safe fix loop when
comments or CI/CD show real issues.

Compose existing workflows instead of copying them:

- `workflows/ticket-review-and-fix.md` for code review, acceptance criteria,
  test selection, fixes, commits, and pushes.
- `workflows/gh-address-comments.md` for PR review threads and replies.
- `workflows/gh-fix-ci.md` for failing CI/CD checks.
- `workflows/changed-code-quality-gate.md` when source code changed.
- `skills/ci-watcher/SKILL.md` for read-only background monitoring after push.
- `workflows/self-improvement.md` for durable lessons from repeated failures.

## Required inputs

- Ticket key, for example `ABC-123`.
- Repository path or GitHub repo.
- Branch and PR number, or enough evidence to discover them.
- Base branch.
- Automation cadence, stop condition, and whether the automation may comment,
  commit, push, or only report.

If the ticket, repo, branch, or PR cannot be uniquely identified, stop and
report the ambiguity before editing, pushing, or commenting.

## Phase 1 - Establish live scope

1. Read the ticket with the CLI (`rules/cli-over-mcp.md`). Prefer default or
   allowed fields first, then view details, comments, and subtasks as needed.
2. Capture acceptance criteria, linked issues, subtasks, requested test or stage
   evidence, and any "done" notes.
3. Resolve the PR from ticket links, branch names, commits, or `gh pr list`.
4. Read current PR metadata with `gh pr view --json headRefOid,headRefName,baseRefName,state,isDraft,mergeable,reviewDecision,statusCheckRollup,updatedAt`.
5. Fetch the remote and verify the local checkout matches the live PR head.
6. Compare the PR body's mandatory per-file **File changes** table with
   `git diff --name-status --find-renames origin/<base>...HEAD`. A missing,
   duplicated, stale, or generic row blocks approval readiness; follow
   `rules/git-conventions.md` section **PR File Change Table**.
7. Inspect dirty and staged files. Preserve unrelated user changes. If ownership
   is unclear, stop with a blocker.

Do not trust stale review state or a previous green check. The final decision
must be tied to the current PR head SHA.

## Phase 2 - Map ticket to evidence

Build a compact trace table before judging readiness.

| Ticket requirement | Evidence source | Status |
| --- | --- | --- |
| Acceptance criterion, bug, or reviewer ask | Code path, test, log, docs, PR thread, CI job | pass, fail, blocked, or not applicable |

Use parent tickets and story context so you do not validate only a subtask when
the subtask is part of a larger delivery.

For production or operational tickets, gather evidence first from application
logs, cloud logs/metrics/alarm history, ticket comments and subtasks, GitHub PR
comments, and related service logs. Keep production checks read-only unless the
user explicitly authorizes a write (`rules/external-write-authorization.md`).

## Phase 3 - Validate locally

1. Select the narrowest tests that cover changed code and ticket risk.
2. Re-run previously failing focused tests after each new head.
3. Run broader validation when the ticket touched shared behavior, packaging,
   generated artifacts, security-sensitive code, or CI/CD surfaces.
4. Run the changed-code quality gate when source code changed.
5. Run `git diff --check` for patch hygiene.
6. If this toolkit changed, run the toolkit validators and the mandatory
   security gate required by `rules/security-check-required.md`.

Treat environment failures as blockers only after proving they are not caused by
the branch. Record the exact failing command and the shortest retry path.

## Phase 4 - Triage PR comments

Read unresolved review threads, bot comments, human comments, and requested
changes. Use `workflows/gh-address-comments.md` for thread handling and apply
`rules/human-comment-reply-gate.md` before any human-facing reply, deletion, or
resolution.

- If a comment is correct, in scope, and actionable: apply the smallest fix,
  validate it, and prepare a consolidated draft with the evidence.
- If a comment is wrong, stale, duplicate, or out of ticket scope: do not change
  code just to agree. Draft or report with source evidence and a narrow
  alternative when useful.
- Place new feedback at the exact file and line when possible. Use file-level or
  top-level comments only when inline placement is impossible.
- Do not post, submit, resolve, delete, or send a human-facing reply without
  showing the exact draft first and receiving explicit approval. Human-authored
  threads remain unresolved unless the user explicitly approves resolution for
  that exact thread.

## Phase 5 - Triage CI/CD

1. Run `gh pr checks` and inspect failed check details. If there are no GitHub
   checks, document the decisive local or external CI signal instead.
2. For GitHub Actions failures, follow `workflows/gh-fix-ci.md`.
3. Separate branch-caused failures from flaky or infrastructure failures.
4. Re-run unrelated flaky jobs at most once when allowed.
5. If a fix is needed, change only ticket-scoped code, validate locally, push,
   and monitor the new head.

After each successful push on an open PR, start or request a read-only
`ci-watcher` run when the repo has CI workflows. The root agent remains
responsible for edits, commits, pushes, comments, and final reporting.

## Phase 6 - Approval readiness decision

End every run with one of these calls:

- **Approve-ready:** the current head matches the local checkout, ticket
  requirements are traced, relevant local validation passes, PR comments are
  resolved or correctly answered, and CI/CD is green or non-branch failures are
  documented.
- **Blocked:** name the exact failing ticket requirement, comment, validation,
  CI/CD job, auth issue, environment issue, dirty-tree ownership issue, or
  freshness issue.
- **Monitor:** no action is needed now, but CI/CD or a reviewer response is
  still pending. Include the next poll target and stop condition.

Always report the ticket key, repo, PR, branch, live head SHA, validators run,
PR comment outcome, CI/CD outcome, pushed commits if any, and remaining risk.

## Phase 7 - Improve the loop

When the same failure shape recurs, run `workflows/self-improvement.md` and
promote the reusable lesson into the smallest durable asset: intent mapping,
workflow split, rule, skill reference, subagent prompt, validation gate, or a
note in the consumer repo's `docs/llm/`. Keep ticket-specific facts out of
generic toolkit files.
