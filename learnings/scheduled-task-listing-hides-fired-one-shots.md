---
title: Scheduled-task listing hides fired one-shots; polling loops leave one per poll
category: toolchain
created: 2026-10-22
tags: [scheduled-task, list_triggers, include_completed, one-shot, send_later, polling, cleanup, cowork]
---

# Problem
An inventory of scheduled tasks looked short, yet the project page's "Scheduled" summary
counted dozens more ("+N more"). The default listing omits fired one-shot tasks (they
disable themselves after running but remain as records) and tasks that were moved into a
project. A polling loop built from chained one-shot reminders (each poll schedules the next
one, every few minutes) leaves one fired, disabled task per poll: 25 in a single afternoon.

# Failed Approaches
- Trusting the default listing as the full set and reporting "nothing to clean".
- Reading the full listing in the main session: each entry carries its whole prompt, so the
  pages are very large and flood the context.
- Deleting by title: fired one-shots from a loop share the same name.

# Solution
- List with `include_completed=true` and compare the count with the project page's summary.
- Delegate the scan to a light lane that writes compact JSON only: id, name, enabled, cron,
  run_once_at, ended_reason, model, last_run status and failure_reason.
- Delete fired one-shots (ended_reason shows they ran) by explicit ID allow-list, after the
  user approves the group; they are history, not configuration, so this group is low risk.
- When designing a polling loop, prefer one recurring task with an end condition over
  chained one-shots. If one-shots are unavoidable, make "delete this loop's fired one-shots"
  the last step of the loop's own plan.

# Why
The listing defaults to live, active tasks. A fired one-shot is finished but still stored,
and a chained loop creates a new stored record on every iteration, so the clutter grows
silently until something lists with the completed filter on.
