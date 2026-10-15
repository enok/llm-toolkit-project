---
title: Cloud session to user PC via the device bridge - moving files, overwriting, scanning
category: toolchain
created: 2026-10-15
tags: [device-bridge, device_bash, desktop-commander, base64, heredoc, mount, overwrite, unlink, md5, cowork]
---

# Problem
A cloud session linked to the user's Windows PC had to (a) copy ~20 KB of generated files
to the PC, (b) refresh files that already existed there, and (c) scan a ~13 GB folder tree.

# Failed Approaches
- `base64 -d > out.tgz <<'B64' ... B64` in `device_bash` with ~19 KB of base64:
  md5 mismatch, archive corrupt (the payload is transcribed by the model; one wrong char breaks it).
- `tar -xzf pkg.tgz -C existing_dir` / `cp new old` on the bridge mount:
  `Cannot open: File exists` - the mount refuses unlink, so replace-by-recreate fails.
- `python3 scan.py $HOME/mnt/<folder>` walking the whole tree through the mount:
  timed out at 120 s (also `du -sh` on a large mounted folder timed out at 40 s).

# Solution
- Container -> PC: `SendUserFile` the file, then `device_commit_files` with the returned
  `file_uuid`; verify with `md5sum` on both sides.
- Refresh an existing file on the mount: extract to a NEW folder, then `cat new > old`
  (truncate + write in place; no unlink needed).
- Whole-tree scans or long scripts: run them natively on the PC with Desktop Commander
  `start_process` (e.g. `python C:\path\script.py ...`), write results to a file, then
  `device_stage_files` the result into the container to analyse it.
- PowerShell one-liners with nested quotes break easily; put Python in a file instead.

# Why
The bridge mount is a remote filesystem with per-call timeouts and no delete permission
by default, and anything the model types (base64, long literals) is subject to transcription
error. File-transfer tools move bytes without passing them through the model.
