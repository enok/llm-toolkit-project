---
title: A worktree created in the cloud VM carries VM paths and breaks the gates on the device
category: environment
created: 2026-11-26
tags: [git, worktree, cloud-vm, device-bridge, shellcheck, history-scan, push, gate-skipped]
---

# Problem
A git worktree was created from the cloud VM and then used on the owner's computer. Its `.git`
file and admin directory store VM paths, so on the device the history scans and the shell
linter were skipped or failed. The run risked reporting "gates passed" while steps had been
skipped. Pushing was also impossible (no sign-in on the device, the bridge refused git's lock
files).

# Failed Approaches
- Running the gates on the VM-created worktree as is: skipped steps look like a pass.
- Reporting a gate as passed from a summary line that did not list the skipped step.
- Retrying a push that the bridge refuses.

# Solution
- Recreate the worktree on the device, or run `git worktree repair` there, before any gate.
- Read each gate's output for "skipped" or "not found" lines. A skipped step is reported as
  skipped, never as passed.
- When a push is impossible, commit locally and give the owner the exact two or three commands
  to run, saying that this push is also the first test of the new authentication.
- Move work between the sandbox and the device with a checksummed patch or bundle
  (`sandbox-to-device-zero-context-patch-with-checksums.md`), and read protected folders as in
  `cowork-bridge-hides-skills-dirs-read-via-cloud-clone.md`. For a dirty shared checkout see
  `dirty-shared-checkout-use-a-worktree.md`.

# Why
A worktree's link files hold absolute paths of the machine that created them, so another
machine cannot resolve them. Tools that fail to find the repository tend to exit quietly,
which turns a broken check into an apparent success.
