---
title: A device commit to an existing path once kept the old bytes
category: environment
created: 2026-10-07
tags: [device-bridge, file-transfer, stale-content, fresh-filename, verification, sandbox, windows]
---

# Problem

Committing a file from the cloud sandbox to a path that already existed on the user's
machine once left the OLD content in place: the machine returned the previous content
on two reads, so the new version never took effect. Only the root session has the device
bridge; lanes in the sandbox cannot reach the machine.

# Failed Approaches

- Reading the path again after the commit: the machine returned the previous content both
  times.

# Solution

Write each new version to a fresh filename and verify a unique marker, length or hash on
the machine, through the device shell, before using the file. A name derived from the
content hash is both fresh and checkable. Sandbox side:

```bash
h=$(sha256sum draft.html | cut -c1-12)
cp draft.html "out/article-$h.paste.html"
echo "$h $(wc -c < draft.html)"
```

Machine side (Windows PowerShell 5.1 syntax, run through the device shell; the hash
prints in upper case, so compare case-insensitively):

```powershell
$p = '<path>\article-<hash>.paste.html'
(Get-Item $p).Length
(Get-FileHash -Algorithm SHA256 $p).Hash.Substring(0, 12)
```

Use the file only when the hash prefix and byte length match the sandbox side. A sandbox
command such as `wc -c` on the sandbox copy proves nothing about the machine. The same
rule applies to the archive when lane output is synced as one archive (zip, device
commit, `tar -xf` on the machine): give each archive version a fresh name.

Variant: re-committing a file staged under the SAME path once wrote an older version of it.
Stage every commit in a fresh staging subfolder (new directory per attempt, not only a new
filename), commit from there, and compare the SHA-256 computed on the machine with the
sandbox hash. The session did not show which layer (the reused staged copy or the
destination) served the old bytes; treat it as unknown - the hash check on the device catches either case.

Durable guidance: skills/multi-language-study-repo/references/toolchain-notes.md; workflows/career-profile-sync.md (Phase 6)

# Why

The session recorded the symptom and the fix, not a cause. Inference: some layer between
the commit and the read served the earlier content for that path; which layer is unknown.
Also inference: the old file is still a complete file, so nothing fails loudly. Only a
check on the machine itself (marker, length or hash) proves which version is there, and a
new filename removes the ambiguity about which write a read is seeing.
