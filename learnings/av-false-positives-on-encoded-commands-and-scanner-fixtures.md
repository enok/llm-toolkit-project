---
title: Endpoint antivirus alerts on encoded commands and scanner test fixtures - triage by evidence, do not disable it
category: security
created: 2026-11-26
tags: [antivirus, false-positive, base64, gzip, scanner-fixtures, allow-list, triage, git-fsck]
---

# Solution
- Folder allowlist: every folder the access log shows in use (work repos, tool cache, temp
  scratch). Exclude `.ssh` and the tool's own config folder: a session able to write the tool
  config can lift its own limits.
- Restore fixtures with the AV on: confirm the checked-out tag; `git fsck`; `git diff <tag>`
  shows only the fixture files; installed package intact; `git checkout <tag> -- <fixtures>`.

# Why
The checks prove the tree matches the tag before restoring.
