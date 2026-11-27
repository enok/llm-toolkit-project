---
title: Many back-to-back daily automations can exhaust usage limits before priority work
category: toolchain
created: 2026-10-22
tags: [scheduled-task, usage-limit, digest, consolidation, cost, scheduling, cowork]
---

# Problem
Six independent daily digest tasks (news, inbox, agenda and similar) each ran 2 to 29
minutes, back to back, every morning. The same morning a higher-priority task failed with
"usage limit reached". The digests were the likely cause, though the platform does not
attribute the limit to specific runs.

# Failed Approaches
- Retrying the failed priority task: it hit the same limit.
- Nudging each digest's start time individually: the total work in the window stayed the same.
- Deleting the old digests the moment a combined task existed: no fallback if the new task
  misbehaves, and no baseline to compare against.

# Solution
- Audit by time: list tasks (with the completed filter), group them by cron window, and
  sum the last-run durations in each window.
- Consolidate overlapping digests into one task with one output, one section per source and a
  per-section cap (top N items, a maximum number of lookups).
- Pause (not delete) the old tasks and write a recovery record (id, enabled before, next run).
  Delete them only after the new task has several runs that pass the duration and output
  check.
- Keep priority tasks outside the digest burst (schedule the critical job away from bulk
  jobs, not just a few minutes after them), and choose the new task's model deliberately.

# Why
Usage limits are shared by every automation and session in the same window. Each small task
pays its own start-up and context-loading cost, so N tasks cost more than one task with N
capped sections, and an unattended burst can starve work that matters more.
