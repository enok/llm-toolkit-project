---
description: Address actionable GitHub PR review comments with a human-facing reply approval gate
---

# GitHub PR comments workflow

Use when the user asks to address PR comments, resolve review feedback, draft reviewer replies, or clean up open review threads. Apply `rules/human-comment-reply-gate.md` before any human-facing post, submit, resolution, deletion, or send action.

## Steps

1. Establish exact scope: record `owner/repo#PR`, people/comments to process, open review threads, top-level PR comments, latest review bodies, changed files, and any linked CI failures. Keep all API/CLI calls pinned to that same repo and PR number; do not rely on branch name or ticket ID alone when multiple repos share a ticket branch.
2. Verify GitHub CLI/API access before relying on comments: run the local `gh auth status` equivalent for the repo host, and if auth, scopes, or rate limits block comment reads, stop with the exact command and failure instead of guessing.
3. Audit every relevant human-authored thread before acting: original comment, code context, prior replies, reviewer follow-ups, linked docs/tickets/designs, prior automated replies, and the latest diff/current head. Treat pushback such as "re-read my comment" as evidence that the previous interpretation may be wrong.
4. Show the user the processing plan before posting anything: thread/comment target, reviewer, issue, likely action, needed code/docs/tests/PR body change, whether a reply draft is expected, and blockers.
5. Once independent threads are known, split analysis by file, subsystem, or comment cluster. Do not pause before internal fanout unless there is a user-visible tradeoff or overlapping write ownership.
6. Map each actionable thread to code, tests, docs, PR body, or explanation changes. Prefer fixing the underlying artifact over adding explanatory replies.
7. Apply minimal fixes and rerun relevant checks. If prior automated replies from us are wrong, noisy, duplicate, or superseded, identify them and ask before deletion unless the user explicitly told you to remove them.
8. Prepare one consolidated draft per thread only after the work is settled. Every draft must include `Posting status: NOT POSTED`, the exact target comment/thread/link, the exact reply text, and what code/docs/tests changed.
9. **User Approval Gate** — present all changes and exact human-facing drafts to the user. Do not commit, push, post, submit, resolve, delete, or send until explicitly approved. Skip only if the user explicitly asked to skip approval for that exact action.
10. After approved push/reply, resolve only threads the user explicitly approved for resolution. Verify the same `owner/repo#PR` current head and comment targets before reporting done. Keep both the GraphQL review-thread ID and the numeric review-comment ID so replies and resolution target the same visible thread.

Report the final comment table:

| Comment/thread | Reviewer | Issue | Action taken | Draft needed | Status/blocker |
| --- | --- | --- | --- | --- | --- |

For large PR description updates, use `gh pr edit --body-file <file>` and then
read the PR body back through `gh pr view --json body`. Verify expected
Markdown headings and tables are still line-oriented before reporting the PR
description updated. Preserve and refresh the mandatory per-file **File
changes** table from `rules/git-conventions.md`; reconcile its rows against the
current base-to-head diff before and after the edit.

See `rules/multi-agent-orchestration.md`.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
