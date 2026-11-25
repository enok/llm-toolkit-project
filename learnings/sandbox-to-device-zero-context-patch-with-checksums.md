---
title: Sandbox change to device worktree via zero-context patch plus checksums
category: toolchain
created: 2026-11-25
tags: [git-apply, patch, checksum, sha256, worktree, cloud-session, sandbox, device]
---

# Problem
A cloud session prepared and validated a ten-file change in its sandbox. The
commit had to be made in a git worktree on the user's machine, but no folder was
connected to the session, so the file bridge could not copy the files. The
remote file-write tool was the way to carry the change.

# Failed Approaches
None recorded beyond the first attempt described in Problem. For the recorded
failure of pasted base64 payloads, see
`learnings/cloud-session-device-bridge-file-io.md` (as read from that
learning, its case has a connected folder; this one does not).

# Solution
Observed once, on a ten-file change; it worked first time.
1. In the sandbox, stage the change and build a zero-context patch.
2. Write the patch text to a scratch file on the device with the remote
   file-write tool.
3. In the worktree, run `--check` first, then apply to the index.
4. Compare the first 16 hex digits of the SHA-256 of every changed file on the
   device with the values computed in the sandbox for the validated files.

```bash
git diff --cached -U0 > <patch-file>             # in the sandbox
git apply --unidiff-zero --check <patch-file>    # in <worktree>
git apply --unidiff-zero --index <patch-file>    # in <worktree>
```

All ten checksums matched, so the device files were byte-identical to the ones
validated in the sandbox. The index lines and the trailing context text of each
hunk header can be dropped from the patch; the hunk ranges must be kept exactly.

# Why
The per-file checksum comparison is what makes re-emitting text through a tool
call safe: one wrong character shows up as a mismatch on one file.
Distinction drawn from the two learnings, not an observation: read together
with the bridge learning, there a pasted payload was corrupted in
transcription; here the result is checked per file, so such an error would be
caught rather than silently kept.
General guidance, not observed: a zero-context patch keeps the re-emitted text
small, and the `--check` step rejects a malformed patch before it touches the
index.
