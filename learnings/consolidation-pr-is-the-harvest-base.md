---
title: A long-lived consolidation PR is the base for further harvests
category: toolchain
created: 2026-11-26
tags: [consolidation, integration-pr, harvest, branch-hygiene, stacking, scheduled-writers]
---

# Solution
While consolidating, pause exactly the scheduled tasks that are enabled AND write to the
repository; record which you paused; resume exactly those. Leave tasks that do not write,
and tasks already disabled, untouched (never enable one).

# Why
The recorded list is the only way to restore the prior schedule state without side effects.
