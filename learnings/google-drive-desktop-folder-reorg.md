---
title: Reorganizing a Google Drive for desktop folder without breaking links or IDs
category: environment
created: 2026-10-15
tags: [google-drive, drive-for-desktop, file-id, folder-id, rename, move, desktop.ini, gsheet, gdoc, reorg]
---

# Problem
A synced Drive folder had to be restructured while scheduled jobs and documents linked to it
by Drive folder ID (e.g. drive.google.com/drive/folders/<id>) and by local path.

# Failed Approaches
- Planning "new folder + move contents out": the new folder gets a NEW Drive ID, so every
  ID-based link to the old folder would open an empty or retired folder.
- Editing files with temp-file + rename (`os.replace`): risks Drive treating it as
  delete + create (new file ID). Existing jobs already used `cat new > file` for this reason.
- Verifying "file count before == after": failed because Drive itself created 20 and removed
  6 hidden `desktop.ini` files (Hidden+System, 106 bytes) in moved/new folders.

# Solution
- Rename/move folders and files in place on the same drive (`os.rename`); never copy.
  Verified afterwards with the Drive API: the renamed folder kept its ID and new title.
- Keep the folder that external links point to as the folder you RENAME, and keep the file
  those links are meant to reach at its top level.
- Overwrite edited files in place: open `r+b`, write, `truncate()`, `fsync`, read back.
- `.gsheet` / `.gdoc` are small JSON pointers (`doc_id`): move them, never recreate them.
- Verify per file (each pre-move file at its mapped path with the same size) and treat
  `desktop.ini` churn as tool-managed noise; explain any byte delta exactly.

# Why
Drive for desktop maps local renames/moves to Drive moves (same ID), but a new folder or a
re-created file is a new Drive object. desktop.ini files are managed by the Drive client.
