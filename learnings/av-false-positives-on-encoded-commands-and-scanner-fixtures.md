---
title: Endpoint antivirus alerts on encoded commands and scanner test fixtures - triage by evidence, do not disable it
category: security
created: 2026-11-26
tags: [antivirus, false-positive, base64, gzip, scanner-fixtures, allow-list, triage, git-fsck]
---

# Problem
Endpoint antivirus raised a "malicious command line" alert on an agent session that had written
a config file through a gzip+base64 one-liner (`FromBase64String`). In another case it
quarantined files of a security scanner's own unit tests from a tool cache, because those tests
contain attack samples as plain text.

# Failed Approaches
- Treating the alert as proof of compromise without reading what the session did.
- Disabling the antivirus to continue: removes the protection for a likely false positive.
- Running more investigative queries that contain the same encoded token: they can raise a
  second alert.

# Solution
- Rebuild the timeline from the tool's command log, read every file the session produced, and
  give a verdict with the evidence (what ran, what was written, no network or credential
  access).
- Write files as plain text; avoid encoded one-liners.
- Grant a tool folder access by evidence: allow only the folders the access log shows in use,
  and exclude credential folders, configuration folders and the tool's own config folder (a
  session that can write there can lift its own limits).
- For quarantined scanner fixtures: confirm the checked-out tag, run `git fsck`, check that
  only those test files differ from the tag and that the installed package is intact; restore
  from the tag. Do not disable the antivirus.
- Related: `rules/command-safety.md`.

# Why
Encoded blobs and attack-sample text are exactly what signature engines look for, whatever the
intent. The command log and file contents are the evidence that separates a false positive from
a real incident.
