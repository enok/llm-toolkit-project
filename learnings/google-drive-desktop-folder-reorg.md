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
- Assuming temp-file + rename (`os.replace`) always gives a new Drive file ID: not confirmed (see
  Solution). Existing jobs still used `cat new > file` out of caution.
- Verifying "file count before == after": failed because Drive itself created 20 and removed
  6 hidden `desktop.ini` files (Hidden+System, 106 bytes) in moved/new folders.

# Solution
- Rename/move folders and files in place on the same drive (`os.rename`); never copy.
  Verified afterwards with the Drive API: the renamed folder kept its ID and new title.
- Keep the folder that external links point to as the folder you RENAME, and keep the file
  those links are meant to reach at its top level.
- Overwrite edited files in place: open `r+b`, write, `truncate()`, `fsync`, read back.
- Observed: an .xlsx written about daily by a script that saves to a temp file and `os.replace()`s
  it in the same folder kept its Drive file ID for more than three weeks (Drive API: same id,
  `createdTime` unchanged). The real risks are delete-then-recreate and moving a file out of the
  folder and back. For one-off edits, overwriting in place remains the safest choice.
- `.gsheet` / `.gdoc` are small JSON pointers (`doc_id`): move them, never recreate them.
- Verify per file (each pre-move file at its mapped path with the same size) and treat
  `desktop.ini` churn as tool-managed noise; explain any byte delta exactly.

# Why
Drive for desktop maps local renames/moves to Drive moves (same ID), but a new folder or a
re-created file is a new Drive object. desktop.ini files are managed by the Drive client.
