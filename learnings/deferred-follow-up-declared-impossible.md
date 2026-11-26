---
title: A "send it to me when it is ready" request was declared impossible while a scheduler existed
category: toolchain
created: 2026-10-22
tags: [scheduled-task, follow-up, reminder, deferred-tools, capability-check, limitation, chat]
---

# Problem

During a chat about a live public event, the user asked for a full analysis
to be done later and sent to them once fact-checks and analyses were
published, then added "and any new polls too". The assistant answered that it
could not work after the conversation ended or send anything on its own, and
offered a reminder on the user's phone instead. The session's tool surface
included scheduling (scheduled tasks and a one-shot "message later" tool,
partly listed as deferred tools), so the answer stated a limitation that was
not real and handed the work back to the user.

# Failed Approaches

- Answering from a general belief about what chat assistants can do instead
  of checking the session's tools, including the deferred ones.
- A device reminder as the first offer: it only nudges the user to come back
  and ask, so the research still waits for them, and later scope (the polls)
  survives only if it is copied into the reminder text.

# Solution

Before stating any limitation, check declared and deferred tools, connectors,
and skills (`rules/capability-check-before-limitation.md`). For a deferred
follow-up, prefer a scheduled task that runs the research and notifies the
user, timed after the sources' publication window, with a standalone prompt
that carries every scope the user asked for; fall back to a reminder only
when no scheduler exists, and say so. Procedure: "Deferred follow-ups" in
`workflows/automation-maintenance.md`.

# Related

- `rules/capability-check-before-limitation.md`: the rule this learning motivates.
- `workflows/automation-maintenance.md` ("Deferred follow-ups"): how to create the task.

# Why

Tool availability varies by session and deferred tools are invisible until
searched, so "I can't" is a claim that needs the same evidence as any other.
