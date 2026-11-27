---
title: Cloud session to user PC via the device bridge - moving files, overwriting, scanning
category: toolchain
created: 2026-10-15
tags: [device-bridge, device_bash, desktop-commander, base64, heredoc, mount, overwrite, unlink, md5, cowork, permission-denied, native-shell, git]
---

# Problem
A cloud session linked to the user's Windows PC had to (a) copy ~20 KB of generated files
to the PC, (b) refresh files that already existed there, (c) scan a ~13 GB folder tree, and
(d) read and commit in a connected repo folder that the bridge's Linux shell showed as
`d?????????` / "Permission denied" (it also could not delete git `.lock` files).

# Failed Approaches
- `base64 -d > out.tgz <<'B64' ... B64` in `device_bash` with ~19 KB of base64:
  md5 mismatch, archive corrupt (the payload is transcribed by the model; one wrong char breaks it).
- `tar -xzf pkg.tgz -C existing_dir` / `cp new old` on the bridge mount:
  `Cannot open: File exists` - the mount refuses unlink, so replace-by-recreate fails.
- `python3 scan.py $HOME/mnt/<folder>` walking the whole tree through the mount:
  timed out at 120 s (also `du -sh` on a large mounted folder timed out at 40 s).
- Retrying `ls`, `git status` or `git commit` in the bridge shell on a folder that shows as
  `d?????????`: the denial is stable, so retries only waste turns.
- `git commit`, `checkout`, `merge` or `pull` through the bridge: they leave `.git/*.lock`
  files that the bridge cannot delete, so later git commands fail with "File exists".

# Solution
- Container -> PC: `SendUserFile` the file, then `device_commit_files` with the returned
  `file_uuid`; verify with `md5sum` on both sides.
- Refresh an existing file on the mount: extract to a NEW folder, then `cat new > old`
  (truncate + write in place; no unlink needed).
- Whole-tree scans or long scripts: run them natively on the PC with Desktop Commander
  `start_process` (e.g. `python C:\path\script.py ...`), write results to a file, then
  `device_stage_files` the result into the container to analyse it.
- Folder shows as `d?????????` / "Permission denied", or git leaves undeletable `.lock`
  files: stop retrying and switch to the Windows-native shell (Desktop Commander PowerShell)
  for reads, writes and git. For the cause (junctions, protected folder names) and read-only
  alternatives see `learnings/cowork-bridge-hides-skills-dirs-read-via-cloud-clone.md`.
- Scratch that lives only in the cloud container (a ledger mirror, helper or rebuild scripts)
  is lost when the container is reclaimed between turns or the session ends. Persist the ledger
  and any reusable script to the device or the repo at each wave boundary, and ask before
  treating pipeline scripts as disposable.
- PowerShell one-liners with nested quotes break easily; put Python in a file instead.
- Multi-line Python through a PowerShell-backed remote shell: inline `python -c "..."` quoting broke.
  Write the code with a single-quoted here-string to a temp file, run it, remove it. The closing
  `'@` must start its own line. PowerShell 5.1 `-Encoding UTF8` adds a BOM, which Python source files tolerate.

```powershell
$code = @'
import json, pathlib
print(len(list(pathlib.Path('.').glob('*'))))
'@
Set-Content -Path "$env:TEMP\job.py" -Value $code -Encoding UTF8
python "$env:TEMP\job.py"
Remove-Item "$env:TEMP\job.py"
```

# Why
The bridge mount is a remote filesystem with per-call timeouts and no delete permission
by default, and anything the model types (base64, long literals) is subject to transcription
error. File-transfer tools move bytes without passing them through the model. Folders that the
Linux-side bridge cannot stat are unreadable from it by design or by filesystem type, so the
native shell is the working route, not a workaround to retry around.
