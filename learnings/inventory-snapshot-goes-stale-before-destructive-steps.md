---
title: An inventory snapshot goes stale before the destructive or config step
category: toolchain
created: 2026-10-22
tags: [inventory, stale-state, concurrency, destructive-actions, scheduled-task, approval-gate, validation]
---

# Problem
During a workspace cleanup, a scheduled task was observed PAUSED at inventory time. About
ten minutes later another session had re-enabled it. The classification lane, working from
the snapshot, still recommended "PAUSE (already paused)". Acting on the plan as written
would have left a running task in place while reporting it as handled.

# Failed Approaches
- Trusting the lane's classification as current state because it was well-formed.
- Presenting the approval plan straight from the snapshot.
- Treating a facts file (memory, notes, an earlier summary) as current truth; it is a
  hint about what to check, not a record of what is there now.
- Assuming a single actor: other sessions, scheduled runs and the user's other devices all
  change the same workspace.

# Solution
- Timestamp the snapshot and treat it as evidence of the past, not of the present. Facts
  files are hints to verify against the live item, never the authority.
- Have the root session validate the plan against live state just before the approval gate
  (this caught wrong rows that the classifier had passed), and again just before each
  destructive or configuration step: re-read that one item by ID and compare the fields the
  action depends on (enabled, name, last updated, emptiness).
- Give each executing lane an ID allow-list plus the expected pre-state ("expect enabled=false;
  if different, skip and report"), so a mismatch stops the step instead of being overridden.
- Verify the live state again after the step, and report skipped items.

# Why
The gap between inventory and execution includes classification time and a human approval,
which is long enough for shared state to change. Identity-by-ID and a pre-state check turn
that drift from a silent wrong action into a visible skipped item.
