---
title: A plan synced with a progress tracker must refuse to guess (design rules)
category: architecture
created: 2026-11-26
tags: [tracker, sync, progress, study-plan, design-rules, idempotency, unicode, spreadsheet]
---

# Solution
- Write to a separate output path by default, never over the tracker.
- Refuse (exit 2) when ANY output path already holds ticks, unless an explicit carry-ticks
  option is given. Why: checking only output == tracker lets a re-run wipe ticks in an earlier output.

# Why
Ticks are user data that cannot be rebuilt.
