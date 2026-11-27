---
title: Sandbox change to device worktree via zero-context patch plus checksums
category: toolchain
created: 2026-11-25
tags: [git-apply, patch, checksum, sha256, worktree, cloud-session, sandbox, device]
---

# Solution
- Keep the re-emitted text small: a zero-context patch, not whole files, and never base64 or
  whole-file pastes as the transport.

```bash
git diff --cached -U0 > <patch-file>             # sandbox
git apply --unidiff-zero --check <patch-file>    # device worktree; --unidiff-zero is required for -U0
git apply --unidiff-zero --index <patch-file>
```

- Compare per-file SHA-256 with the sandbox values. On any mismatch do not commit; inspect or
  re-send that file only.

# Why
Every byte passes through the model; less text means fewer errors, and the checksum catches the rest.
