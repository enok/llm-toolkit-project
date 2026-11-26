---
title: "My files were deleted" - list the folder and compare hashes before restoring anything
category: environment
created: 2026-11-26
tags: [files, rename, hash, listing, ledger, investigation, collision, scheduled-task]
---

# Problem
A user reported files missing from a working folder. In fact nothing was deleted: several files
had been renamed at a certain time by an unknown actor, and the new name now collided with a
different file that must not be sent to the recipient.

# Failed Approaches
- Restoring or recreating files from memory before looking at the folder.
- Speculating about who renamed them.
- Attaching a file by name without checking which content sits behind it.

# Solution
1. List the folder from the device and diff it against the last saved listing or ledger.
2. Hash the files; report facts only: nothing deleted, N files renamed at time T, content
   byte-identical, actor unknown.
3. Check the new names for collisions with other files; if one exists, warn the user and say
   which copy to attach.
4. State the shell's own limits (for example deletion is disabled in that shell) so the user
   knows what the tool could and could not have done.
5. Do not guess the cause; a rename by a scheduled task is one known cause, see
   `scheduled-task-attached-folder-rename.md`.

# Why
The listing and hashes turn a worry into checkable facts, and the collision warning prevents the
real damage, sending the wrong file under the expected name.
