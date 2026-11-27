---
title: Many back-to-back daily automations can exhaust usage limits before priority work
category: toolchain
created: 2026-10-22
tags: [scheduled-task, usage-limit, digest, consolidation, cost, scheduling, cowork]
---

# Solution
- Move the priority task well away from the digest window (hours, not minutes after it).
- Do not rely on retrying the priority task or nudging start times by a few minutes.

# Why
The usage limit is shared across the window: a retry hits the same limit, and small nudges
keep the same total work in it.
