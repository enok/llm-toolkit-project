---
title: Cloud session to user PC via the device bridge - moving files, overwriting, scanning
category: toolchain
created: 2026-10-15
tags: [device-bridge, device_bash, desktop-commander, base64, heredoc, mount, overwrite, unlink, md5, cowork, permission-denied, native-shell, git]
---

# Problem
Refreshing files that already exist on the bridge mount: `tar -xzf pkg.tgz -C existing_dir` or
`cp new old` fails with `Cannot open: File exists`.

# Solution
- Never unlink/recreate existing names on the mount (no `tar -x`, `cp`, `mv` over them).
- Extract or copy to a NEW folder on the mount, then overwrite each existing file in place:
  `cat new/file > old/file` (truncate + write, no delete needed). Verify with `md5sum`.

# Why
The mount refuses unlink by default, so replace-by-recreate fails; an in-place write does not
need delete permission.
