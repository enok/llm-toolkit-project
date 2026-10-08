---
title: Staging a file just written into a cloud-synced folder can be refused as "hardlinked"
category: environment
created: 2026-10-07
tags: [device-bridge, staging, cloud-sync, hardlink, retry, file-transfer]
---

# Problem

A file had just been written into a folder that a cloud-sync client watches. Staging it
through the device bridge (to reach it from the session) was refused with a message saying the
file was "hardlinked".

# Failed Approaches

None recorded in the session notes; the default behaviour produced the failure described above.

# Solution

Wait for the sync client to settle, then retry the same stage call on the same file. It
staged on the retry. No extra copy of the file was needed, so do not create one (general guidance, not
observed: a copy under a second name or folder leaves two files that can diverge and adds a
path to verify).

After the stage succeeds, verify what arrived the usual way: a marker, length or hash on the
machine side for text files, and for PNGs a decoded-pixel digest
(learnings/device-bridge-transfer-reencodes-png-compare-decoded-pixels.md). Use a fresh
filename for each revision (learnings/device-commit-to-existing-path-can-keep-stale-bytes.md).

General guidance, not observed: if the refusal persists, stop and report the exact text to the
user instead of improvising a different transfer path.

Durable guidance: skills/linkedin-publishing/SKILL.md (Known pitfalls) and
skills/multi-language-study-repo/references/toolchain-notes.md

# Why

The session observed the refusal on a freshly written file in a synced folder and the success
after the sync settled. It did not establish the mechanism. Inference: while the sync client
is still processing a new file, the file system reports it in a state (a link or placeholder)
that the staging check treats as hardlinked, and the state clears when the client finishes. A
copy would hide the symptom without addressing it.
