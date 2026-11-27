---
title: Moving a repo that user-level Claude config points to - grep first, repoint, verify
category: environment
created: 2026-11-26
tags: [relocate, symlink, claude-config, claude-md, ln, readlink, sed, macos, launch-agents]
---

# Problem
A toolkit repo was moved to a new folder while user-level configuration still pointed at the
old location: the personal `CLAUDE.md`, agent and skill symlinks, shell startup files, other
tools' configs, launch agents and container mounts. After the move, sessions silently lost the
instructions or the skills.

# Failed Approaches
- Moving first and fixing paths as errors appear: some references fail silently (a symlink
  that dangles just shows nothing).
- Running `sed` over config files without a backup: a wrong pattern had no way back.
- Editing references inside snapshots and backups: that rewrites history that should stay as it was.

# Solution
1. Search read-only first for the old path across user-level agent config, shell rc files,
   other tools' configs, launch agents or scheduled jobs, symlinks and container mounts. List
   what you would change and ask before editing.
2. Move the folder.
3. Back up `CLAUDE.md` (and any file you will edit) before running `sed`.
4. Repoint with `sed`; on macOS (BSD sed) the in-place flag needs an empty suffix:
   `sed -i '' 's|<old>|<new>|g' <file>`.
5. Recreate the agents and skills symlinks with `ln -sfn <new-target> <link>` and verify with
   `readlink <link>`.
6. Tell the user that sessions already open keep the old `CLAUDE.md` until restarted.
7. Leave snapshots and backups untouched.

# Why
Path references are spread over files that no single tool lists, so a read-only inventory
before the move is the only complete view. `ln -sfn` replaces the link itself instead of
creating a link inside the target directory. Untested: Windows junctions; see
`learnings/cowork-bridge-hides-skills-dirs-read-via-cloud-clone.md` for junction behaviour
through the device bridge.
