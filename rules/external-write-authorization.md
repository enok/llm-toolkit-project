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
  An automated hook, scheduled prompt, or standing authorization (for example
  a stop hook that demands commit and push) never lifts an explicit user hold
  on that action or target: keep the hold, skip the write, and state the hold
  in the report.
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

## Public content: privacy sweep before approval

Before a draft published under the user's name (article, post, slide, image,
comment) is shown as ready:

- Keep the list of terms that must never appear (employers, clients, internal
  projects, people, hosts, tickets) in a file outside every repository (or
  excluded via `.git/info/exclude`), never a tracked file; give the checker
  that file's path, never its terms.
- Search everything that ships, case-insensitively: text, alt text, captions,
  file names, text inside images and PDFs, and file metadata, plus patterns
  for emails, hostnames, absolute local paths, tokens, and ticket keys.
- Report `file:line` (or file:page/field for images, PDFs and metadata) and
  match counts only. A validator message, report,
  prompt, or commit that prints a listed term is itself a leak and fails
  the check.
- Re-run the full sweep after the last edit; any hit, or private detail about
  a third party, blocks the draft.

## PR lifecycle state is external state

A history rewrite that removes every commit or diff from an open PR can close
it without any explicit close call: with no remaining base-to-head diff, the
host may auto-close the PR.

- Before force-resetting a PR head, compare the proposed head with its base. If
  they would be identical, disclose the auto-close risk and ask whether to
  preserve the PR's audit trail (for example via an authorized additive
  revert).
- Never silently create a dummy commit merely to keep a PR open.
