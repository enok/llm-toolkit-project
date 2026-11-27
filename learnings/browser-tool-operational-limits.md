---
title: Browser-extension tool limits that break long automation runs
category: toolchain
created: 2026-10-22
tags: [browser, extension, limits, wait, page-text, file-upload, tab-group, javascript-tool, multi-browser, mid-publish]
---

# Problem

Long browser-automation sessions failed in ways unrelated to the target site:
a single wait over 10 seconds was rejected; a very long page extraction exceeded
the result-size limit; the file-upload tool refused host file paths; the
JavaScript tool redacted cookies and query strings; tab handles from an earlier
turn were reported "not in the tab group"; a screenshot right after navigating to
a heavy app failed with a zero-width error.

# Failed Approaches

- Reusing tab ids across turns.
- One long wait instead of chained waits.
- Passing a local path to the file-upload tool.
- Extracting a whole lazy list in one call.

# Solution

- Start each browser turn with the tab-context call and use the ids it returns.
- Chain waits of 10 seconds or less; retry a failed screenshot after a short wait.
- Split long extractions (fewer scrolls per call, or a subtree).
- When a file must be attached from the owner's disk and the tool cannot read the
  path, ask the owner to click the page's upload control and continue after.
- Expect redaction in script results; log what you need in short fields. Query-string-like
  returned text is blocked outright; see
  `browser-tool-blocks-urls-with-query-strings-in-returned-text.md`.
- A "not connected" message from the extension is often transient: retry once,
  then tell the owner how to reconnect.

# Several browsers connected

- When more than one browser is connected, do an explicit select-browser (or
  switch-browser) step before any tab action; a tab call without it can land in the
  wrong browser or fail.
- Each account or identity may have its own Chrome profile. Pick the profile that is
  signed in to the account the task needs, and never sign in for the owner.
- Prefer the real signed-in browser over the built-in app browser, which is often signed
  out of the services the task needs.
- A "not connected" message can also appear in the middle of a publish or save. Re-read
  the page state before doing anything else and never assume the publish landed (or did
  not land); a retry on an unread state can duplicate it.

# Why

These are tool-side limits, not site behavior; knowing them avoids misdiagnosing
the page and wasting retries.
