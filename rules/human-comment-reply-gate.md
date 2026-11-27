---
trigger: always_on
description: Approval gate for human-facing review and comment replies
---

# Human Comment Reply Gate

- Never post, submit, resolve, delete or send a reply a human will see (GitHub, Jira, Confluence, Slack, email, chat) without showing the exact draft and getting explicit approval for that target and text; a material edit needs new approval. Human threads stay unresolved unless the user approves resolving that thread.
- Every draft states `Posting status: NOT POSTED`, the exact target, the exact text, and what changed. One consolidated draft per thread, after the work settles.
- Every question needing an answer gets a draft, even when the answer is the user's call. A decision that commits the user (dates, prices, acceptance, availability, personal or financial data) is drafted as options with trade-offs, never decided.
- Read the full history on every involved channel (scroll to the first message) before drafting, and re-read it just before sending: if the premise changed, the draft is stale and needs new approval.
- Exception: progress notifications the user pre-authorized for this run, to a destination they named, in their pre-approved format (agent, one-line result, tier) only. The root sends; subagents only draft.
