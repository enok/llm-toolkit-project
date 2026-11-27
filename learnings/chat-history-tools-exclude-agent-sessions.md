---
title: Chat-history tools list only regular chats, not agent (Cowork) sessions
category: toolchain
created: 2026-10-22
tags: [chat-history, recent_chats, conversation_search, cowork, agent-sessions, inventory, cleanup, claude-ai, browser]
---

# Problem
A workspace inventory ("what chats and tasks does this account hold?") was built from the
chat-history tools (recent chats, conversation search). It returned only a fraction of the
items (17 of 26 in one run). The rest were agent sessions (Cowork tasks), which are usually
the bulk of the clutter, and none of them appeared.

# Failed Approaches
- Treating the recent-chats result as the full list and paging with `before`/`after`:
  the tool never returns agent sessions, so more pages do not help.
- Searching by keyword for task titles with conversation search: same index, same gap.
- Deriving sessions from the scheduled-task listing: it shows tasks, not the sessions they
  or the user started.

# Solution
Inventory each surface with its own source and merge the results into one table keyed by a
stable ID (the URL uuid), with a `source` column:
- Regular chats: the chat-history tools.
- Agent sessions: the claude.ai web app, Recents (Active and Archived filters; entries are
  labelled "Task" and live under a `/cowork/` URL) and the project pages. This needs a
  signed-in browser. The built-in browser may redirect to login: never sign in for the
  user, ask which browser is already signed in or ask them to sign in.
- Scheduled tasks: the scheduling tool with `include_completed=true`
  (see `learnings/scheduled-task-listing-hides-fired-one-shots.md`).
- Artifacts: the Artifact list (scope mine/all).
Where the page UI cannot list everything, ask the user before using any non-UI route, and
cross-check against what the page shows.

# Why
The chat-history tools index regular conversations only. Agent sessions are a different
object type with separate storage and UI, and the tools do not error on the gap: they just
return a shorter list that looks complete.
