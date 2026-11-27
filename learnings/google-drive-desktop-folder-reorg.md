---
title: Reorganizing a Google Drive for desktop folder without breaking links or IDs
category: environment
created: 2026-10-15
tags: [google-drive, drive-for-desktop, file-id, folder-id, rename, move, desktop.ini, gsheet, gdoc, reorg]
---

# Solution
- Verify per file, not by count: each pre-move file exists at its mapped path with the same size.
- Ignore hidden `desktop.ini` files (Hidden+System, about 106 bytes) that appear or disappear in
  moved/new folders; report them as Drive-managed noise instead of failing on a count mismatch.

# Why
The Drive client creates and removes `desktop.ini` on its own (observed: 20 added, 6 removed),
so "count before == count after" fails on a correct move.
