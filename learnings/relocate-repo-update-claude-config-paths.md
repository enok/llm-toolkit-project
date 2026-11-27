---
title: Moving a repo that user-level Claude config points to - grep first, repoint, verify
category: environment
created: 2026-11-26
tags: [relocate, symlink, claude-config, claude-md, ln, readlink, sed, macos, launch-agents]
---

# Solution
- Repoint every occurrence (`g` flag) in every kind of file found: `CLAUDE.md`, shell rc,
  other tools' configs, launch-agent plists, compose files.
  macOS: `sed -i '' 's|<old>|<new>|g' <file>`.
- Tell the user that already-open sessions keep the old `CLAUDE.md` until restarted.

# Why
A line can hold the path twice, and open sessions read config only at start.
