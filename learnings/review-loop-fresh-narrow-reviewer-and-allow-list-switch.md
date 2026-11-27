---
title: Review loops - a fresh narrow reviewer can cost half as much, and two failed deny-lists call for an allow-list
category: toolchain
created: 2026-11-26
tags: [review-loop, validator, fixer, tokens, allow-list, deny-list, iteration-cap, orchestration]
---

# Problem
In a validator and fixer loop the long-lived reviewer carried a large context, and a security filter
for hidden-text and carrier characters kept failing: each fix added a new finding in the fix itself.

# Failed Approaches
- Resuming the long-lived reviewer for every iteration: about 218K tokens in one run, against about
  125K for a fresh narrow reviewer given only the defect list and the diff.
- Extending the deny-list after each miss: variants kept slipping through.
- Looping past the iteration cap.

# Solution
- Give a fresh narrow reviewer only the defect list and the diff; record which reviewer was used.
- After two deny-list failures switch to an allow-list.
- At the cap, report the open item instead of looping.
- A failing validator returns exact replacement text in a file, not prose.
- Related: `agent-self-reported-counts-are-not-evidence.md`, `workflows/task-quality-loop.md`.

# Why
Deny-lists enumerate known bad inputs, so the next variant passes; an allow-list defines the
accepted set. A narrow context also costs fewer tokens and carries less bias from earlier rounds.
