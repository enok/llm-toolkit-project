---
trigger: always_on
description: Bind every external mutation (Jira, GitHub metadata, Confluence, Slack, email) to an explicit current user instruction
---

# External write authorization

Terminal language expresses persistence toward an outcome, not permission for
side effects in other systems. External records and replies affect other
people, workflows, and audit history, so their authorization boundary must be
checked independently from the technical task.

- Before every external mutation, bind the exact action and target to a current
  user instruction. "Finish", "do the same", or a ticket reference is not
  blanket permission to mutate every system associated with the ticket.
- Deployment authority covers only the named environment, branch, pipeline, and
  validation work. It does not implicitly cover Jira, GitHub metadata (labels,
  state, reviews), Confluence, Slack, email, or other human-facing systems.
- Read-only inspection may continue whenever the authorized task needs it.
- For an unapproved external write, prepare the smallest draft or proposed
  delta, label it `NOT POSTED`, and ask for approval. If the write is required
  for full completion, report it as pending instead of silently expanding
  scope. Human-facing replies additionally follow
  `rules/human-comment-reply-gate.md`.
- Finding a defect (for example stale documentation) authorizes reporting it,
  not publishing the fix.

## PR lifecycle state is external state

A history rewrite that removes every commit or diff from an open PR can close
it without any explicit close call: with no remaining base-to-head diff, the
host may auto-close the PR.

- Before force-resetting a PR head, compare the proposed head with its base. If
  they would be identical, disclose the auto-close risk and ask whether to
  preserve the PR's audit trail (for example via an authorized additive
  revert).
- Never silently create a dummy commit merely to keep a PR open.
