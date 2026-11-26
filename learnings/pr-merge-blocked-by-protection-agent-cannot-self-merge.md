---
title: Green checks but merge refused - the agent cannot self-merge past branch protection
category: toolchain
created: 2026-11-26
tags: [github, branch-protection, code-scanning, required-review, merge, handoff, draft-pr, rebase]
---

# Problem
Pull requests with all checks green still could not be merged: the base branch required
code-scanning results (the scanner was not enabled on the repository) or a review. The agent was
asked to "open the PR, wait for validations, merge" and met the same blocker in several runs.

# Failed Approaches
- Enabling the scanner or changing branch protection to get past the block.
- Retrying the merge command.
- Reporting "merged" from a note written earlier instead of a live read.

# Solution
- Do not enable scanners or bypass protection; that is the owner's decision.
- Record in the PR handoff the exact user action: enable the scanner, or click squash-merge.
- Verify the merge state with a live read; when it cannot be read, write "cannot confirm
  merged".
- A draft PR that fell behind the base is brought current by rebase:
  `gh pr update-branch <pr> --rebase` (see
  `strict-required-checks-behind-main-use-update-branch.md`).
- A required check that no longer exists blocks too: `required-checks-must-follow-removed-ci-jobs.md`.
- Merge only with explicit approval (`rules/git-conventions.md`).

# Why
Branch protection is a control the agent must respect, and a stale note is not evidence of the
current repository state.
