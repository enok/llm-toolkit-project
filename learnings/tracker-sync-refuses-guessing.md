---
title: A plan synced with a progress tracker must refuse to guess (design rules)
category: architecture
created: 2026-11-26
tags: [tracker, sync, progress, study-plan, design-rules, idempotency, unicode, spreadsheet]
---

# Problem
A generated plan was synced with a progress tracker sheet. A wrong guess about tick state would
overwrite the user's real progress. These are design rules; the module is not in the toolkit.

# Failed Approaches
- Coercing odd values to true or false.
- Regenerating the tracker over existing ticks.
- Matching titles that differ only by a dash variant.

# Solution
- Refuse non-boolean state values: exit with code 2, no guess.
- Never overwrite a tracker file that already holds ticks unless an explicit carry-ticks option is
  given.
- Never queue a tick for an item missing from the state that was actually read.
- Normalise every dash variant (including U+2010) before matching titles.
- Treat Done stored as formula-false and the literal False as equal.
- Keep core scheduling standard-library only and import renderer libraries lazily.
- Related: `skills/job-search-pipeline/references/tracker-schema.md`.

# Why
Progress is user data that cannot be reconstructed, so every ambiguity must stop the run instead of
being resolved by a guess.
