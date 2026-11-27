---
title: Desktop Commander on Windows - PowerShell run mode, split destructive calls, scan per folder, hand off elevation
category: toolchain
created: 2026-11-26
tags: [desktop-commander, powershell, start_process, remove-item, long-scan, read_process_output, elevation, classifier, windows]
---

# Solution
- Never scan a whole drive in one recursive process. Start one `start_process` per top-level
  folder of each drive (and per suspect folder), narrowed to subtrees where possible.
- Poll each with `read_process_output` by pid with a timeout of at most about 170-175 seconds,
  writing results to a file so a timeout loses nothing.

# Why
Bridge calls have a per-call time limit; a whole-drive scan (over a million files) times out
before returning.
