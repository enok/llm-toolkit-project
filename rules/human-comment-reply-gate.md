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
- when the conversation spans several channels (e.g. email plus chat or social
  messaging or a ticket), the complete history on every involved channel, not
  only the one being replied on; paginate or scroll to the first message,
  because chat UIs often lazy-load only recent messages;
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
- Decisions that commit the user (prices or rates, acceptance, availability,
  personal or financial data) are the user's. Drafts present options and
  trade-offs; they do not decide.

## Pre-Send Freshness Check

- Immediately before sending an approved reply, re-read the latest messages on
  every involved channel.
- If the user already replied, or the counterpart sent something that changes
  the premise, the draft is stale: do not send it. Show the delta and a revised
  draft for new approval. Approval does not carry over to a stale draft.

## Closeout Table

After processing, report:

| Comment/thread | Reviewer | Issue | Action taken | Draft needed | Status/blocker |
| --- | --- | --- | --- | --- | --- |
