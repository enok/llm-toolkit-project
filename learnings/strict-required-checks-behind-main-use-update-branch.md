---
title: Strict required checks make a PR that is behind main unmergeable - use gh pr update-branch --rebase
category: toolchain
created: 2026-11-26
tags: [github, branch-protection, strict-checks, update-branch, rebase, gh, classifier, merge, squash]
---

# Problem
With "require branches to be up to date" (strict required checks) on, a pull request that fell
behind `main` could not be merged even though its checks had passed. Separately, `gh` commands
that read back or merged the PR were refused by the session's safety classifier, so the state
could not be confirmed.

# Failed Approaches
- Merging `main` into the PR branch (the default `gh pr update-branch` variant, or a local
  `git merge`): it violates `rules/git-conventions.md` ("never use `git merge` to integrate
  upstream changes - rebase only").
- Rebasing locally and force-pushing without approval: it rewrites history on a branch that
  protected repositories should not allow force-pushes to.
- Retrying a refused `gh` read-back or merge: the classifier refuses the same call again.
- Reporting "merged" without a read-back: the refusal means the state is unknown.

# Solution
- Catch the branch up server-side with the rebase variant: `gh pr update-branch <pr> --rebase`.
  GitHub rebases the PR head onto the base. Use it only for the user's own PR branch, never a
  shared or environment branch. Wait for the required checks to rerun, then merge.
- If the rebase method is unavailable (conflicts), rebase locally under the "Ticket/Feature
  Branch Rebase Before Push" section of `rules/git-conventions.md` and push with
  `--force-with-lease` after the owner approves.
- If a `gh` read-back or merge is refused by the classifier, report the item as
  "unconfirmed - needs a human" with the exact command, and stop. Do not retry or look for a
  way around it; merging needs explicit approval anyway. For a merge that checks cannot unblock
  see `pr-merge-blocked-by-protection-agent-cannot-self-merge.md`.
- Branch-protection recipe for a personal toolkit repo: pull request required, 0 approvals,
  dismiss stale reviews, enforce for admins, no force-push, no deletion, conversation
  resolution required, strict checks `validate` and `changed-code-quality-gate`, squash merge
  only, delete branch on merge. Keep required job names stable; see
  `learnings/branch-protection-required-checks-need-stable-job-names.md`.

# Why
Strict mode requires the tested commit to contain the latest base, and the rebase variant of
`update-branch` produces such a commit on the server while keeping history linear. A refused command gives no
evidence either way, so the honest status is "unconfirmed". The recipe fits a single-owner
repository; teams that need reviews should raise the approval count.
