---
trigger: always_on
description: Approval gate for human-facing review and comment replies
---

# Human Comment Reply Gate

Use this rule before posting, submitting, resolving, deleting, or sending any
reply that will be visible to a human reviewer or stakeholder in GitHub, Jira,
Confluence, Slack, email, chat threads, or similar systems.

## Approval Gate

- Do not post, submit, resolve, delete, or send a human-facing reply without
  first showing the user the exact draft and receiving explicit approval.
- Treat "approve", "post it", "send it", "resolve it", or equivalent wording
  as approval only for the exact target and exact text shown in the latest
  draft. Material edits require a new approval.
- Human-authored threads remain unresolved unless the user explicitly approves
  resolution for that exact thread.

## Pre-Authorized Progress Notifications (narrow exception)

Recurring orchestration progress notifications may be sent without per-message
draft approval only when all of the following hold:

- the user explicitly pre-authorized progress posting for this run or session;
- the user named the exact destination (channel or thread) and approved the
  status-line format up front;
- each message contains only the pre-approved format: agent, one-line result,
  and complexity tier — no evidence, file contents, findings, or free text.

Anything outside that exact format or destination returns to the standard
draft-and-approve flow above. The root agent sends; subagents only draft.

## Thread Audit

Before acting on a human-authored comment, read the full thread and current
state:

- original comment, prior replies, reviewer follow-ups, and linked docs,
  tickets, designs, or decisions;
- relevant code, tests, docs, PR body, and latest diff/current head;
- surrounding file or artifact context needed to understand the comment;
- any prior automated replies from the agent or tooling.

Treat reviewer pushback such as "re-read my comment" as evidence that the
previous interpretation may be wrong. Re-audit the thread before changing code
or drafting another reply.

## Response Preference

- Prefer fixing code, tests, docs, or PR body over adding explanatory replies.
- If a comment is wrong, stale, duplicate, or out of scope, support that
  conclusion with current source evidence and propose the smallest safe
  alternative.
- If prior automated replies are wrong, noisy, duplicate, or superseded,
  identify them and ask before deleting, hiding, or replacing them unless the
  user already explicitly requested that cleanup.

## Draft Discipline

- Produce one consolidated draft per thread after code/docs/tests are settled.
  Do not create incremental reply chains while work is still in progress.
- Every draft must include:
  - `Posting status: NOT POSTED`
  - exact target comment, thread, or link
  - exact reply text
  - what code, docs, tests, PR body, or other artifacts changed, if anything
- Start comment-processing work by auditing relevant human comments and showing
  the processing plan before any post, submit, resolve, delete, or send action.

## Closeout Table

After processing, report:

| Comment/thread | Reviewer | Issue | Action taken | Draft needed | Status/blocker |
| --- | --- | --- | --- | --- | --- |
