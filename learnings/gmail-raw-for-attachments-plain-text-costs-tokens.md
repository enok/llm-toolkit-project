---
title: Fetch Gmail attachments through the RAW format; plain-text formats inline thousands of tokens of attachment ids
category: toolchain
created: 2026-11-26
tags: [gmail, mcp, attachments, raw, mime, tokens, bulk-read, base64url]
---

# Problem

An automation had to save PDF attachments from many emails. The Gmail connector has no
attachment-download tool, and reading each message with the plain-text or full-content
format returned about 10,000 tokens of attachment ids per email, which made a bulk run
slow and expensive without delivering the files.

# Failed Approaches

- Looking for an attachment-download tool: the connector does not offer one.
- Reading each message with PLAIN_TEXT or FULL_CONTENT: the body is short, but every
  attachment id is inlined, so a mailbox sweep burns the context window.
- Assuming an inline-only message carries a file: messages with no attachment part give
  only a view URL.

# Solution

- Fetch the message with `messageFormat=RAW`. The result is persisted to a file as JSON
  whose `raw` key holds the base64url-encoded MIME message.
- Decode it and parse with Python's `email` module using `policy=default`; walk the parts
  and write each attachment to disk with a script, not by pasting content through the model.
- For metadata only (sender, subject, dates, labels) use THREAD_VIEW_SUMMARY or
  METADATA_ONLY; never use the plain-text or full-content formats for bulk reads.
- Treat a message without an attachment part as "link only" and report the link instead of
  fetching it (see `learnings/email-automation-sender-auth-and-link-allowlist.md`).

# Why

The RAW format hands the model-free script the exact bytes, so the cost is one file read,
while the text formats embed attachment metadata in the model's context for every message.
