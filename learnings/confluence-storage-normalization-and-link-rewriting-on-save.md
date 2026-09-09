---
title: Confluence rewrites entities and same-site links on save; validate readbacks semantically
category: api
created: 2026-08-19
tags: [confluence, storage-format, ac-link, entity-encoding, readback-validation]
---

# Problem

After inserting a single paragraph into fetched HTML and re-saving through the
MCP `updateConfluencePage`, the readback did not byte-match the submitted body,
and a freshly created page's stored body differed from the submitted HTML —
raising false "content corrupted?" alarms during verification.

# Failed Approaches

- Expecting byte-identical round-trips: Confluence normalized the inserted
  apostrophe (`applications'`) to `&#039;` and the em dash to `&mdash;`.
- Expecting `<a href>` links to stay as written: absolute links to pages on the
  same Confluence site are rewritten on save into
  `<ac:link><ri:page ri:content-title="..."/></ac:link>` references
  (title-based, with `ri:version-at-save`), and panel `div`s become
  `<ac:structured-macro ac:name="info">` with server-generated macro IDs.

# Solution

Validate readbacks semantically rather than byte-for-byte: compare heading
counts and order, confirm the inserted fragment appears exactly once, and
byte-compare only after normalizing the known rewrites (entity encoding,
`ac:link` substitution).

Note the upside: because same-site links become page references by content
title or ID, they survive later page renames. Plain external URLs (for example
cloud console links) stay literal `<a href>` values.

# Why

Confluence parses submitted HTML into its own document model and re-serializes
it; the serialization choices (entity encoding, macro IDs, link resolution,
`ri:version-at-save` refresh) are server-owned and non-deterministic from the
client's point of view. Byte identity is not a contract — only semantic
structure is. This also means "insert one paragraph, resend the rest verbatim"
is a safe edit strategy, but the proof of correctness must tolerate
normalization.
