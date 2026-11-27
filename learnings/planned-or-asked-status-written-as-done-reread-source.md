---
title: Plans and unanswered questions in team messages were written up as completed status; re-read each row at its source
category: architecture
created: 2026-11-24
tags: [status-report, documentation, wrong-assumption, source-check, planned-vs-done]
---

# Problem
Plans and unanswered questions in team messages were first written up as completed status in a
document. The session classed this as a medium-severity wrong assumption.

# Failed Approaches
- Writing status rows from the messages as read, treating a plan or a question as a finished item.

# Solution
Re-read each status row at its source and mark it planned, reported or unconfirmed. Mark it done
only when the source says it is done.

# Why
A message that states an intention or asks a question does not say the work is complete.
Inference, not observed: a first pass that summarizes by topic loses the difference between what
was planned, what was reported and what was asked.
