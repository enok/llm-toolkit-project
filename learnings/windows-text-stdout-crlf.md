---
title: Windows text-mode stdout writes CRLF, so normalise newlines in test helpers
category: testing
created: 2026-10-07
tags: [windows, crlf, newline, subprocess, stdout, test-helpers, assertions, cross-platform]
---

# Problem

Tests that asserted on subprocess output failed on Windows because the child process's
text-mode stdout wrote CRLF line endings. A validator caught it; the session recorded it as
a medium-severity env-constraint mistake.

# Failed Approaches

None recorded beyond the first attempt described in Problem: the assertions compared
output against LF text and failed on Windows.

# Solution

Normalise newlines in the test helper that captures the output, before any assertion
compares it. Illustrative helper (not executed in the authoring session):

```python
def normalize_newlines(text: str) -> str:
    return text.replace("\r\n", "\n")
```

Call it on the captured stdout (and on any expected text read from a file) inside the shared
test helper, so each test keeps asserting against LF text and the helper is the only place
that knows about Windows line endings.

# Why

The record states the cause as Windows text stdout writing CRLF. An assertion written
against `"\n"` therefore fails there even though the content is identical. The same
line-ending mismatch is why byte pins and hashes are computed on the LF form in
`rules/cross-platform-scripts.md`; treat a failure that appears only on Windows and shows
identical text as a line-ending problem first.
