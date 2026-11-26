---
title: The browser JavaScript tool blocks returned text that looks like query strings or cookies
category: toolchain
created: 2026-11-26
tags: [browser, javascript-tool, blocked, query-string, cookie, chunking, get-page-text]
---

# Problem
Bulk reads through the browser JavaScript tool returned about 1 KB per call, and text containing
query-string characters (`?`, `=`, `&`) came back as a BLOCKED notice for cookie or query-string
data. Observed 2026-10; behaviour may change.

# Failed Approaches
- Returning whole URLs.
- Reading session cookies for a private API call: the auto-mode classifier may refuse it.
- One long script call with a long wait.

# Solution
- Slice output into chunks of at most 900 characters and fetch the chunks in parallel calls.
- Return only the non-sensitive parts the task needs (a host and path, an id, a count), not whole URLs.
- Render visible text into a `<pre>` element and read it with the page-text tool.
- When a read is blocked or refused, report it. Do not retry, and do not reshape or encode the
  output to get it past the filter. For cookie data, use the page UI instead.
- Related: `browser-tool-operational-limits.md`.

# Why
The filter works on returned text. It is a safety control that keeps cookie and token data out of
model context, so read blocked content through the page-text tool or the UI instead of
transforming it.
