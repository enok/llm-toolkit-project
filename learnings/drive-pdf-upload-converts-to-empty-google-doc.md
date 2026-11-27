---
title: Cloud-drive upload converts a PDF into an empty native document unless conversion is disabled
category: toolchain
created: 2026-10-22
tags: [google-drive, upload, pdf, conversion, connector, silent-failure]
---

# Problem

Creating a file in a cloud drive from base64 content returned a normal-looking
success payload (id, view link, correct title) but the stored item was a native
document of about one byte, not the PDF. Markdown and CSV uploads sent with the
conversion flag explicitly disabled stayed as files.

# Failed Approaches

- Treating the returned id and link as proof of success.
- Re-sending the same call hoping for a different result (same conversion).

# Solution

- Always pass the "disable conversion to native type" option for PDFs, other
  binaries, CSV and markdown.
- Check `mimeType` and `fileSize` in the response; a native document type or a
  tiny size means the upload is wrong.
- If a stray converted item exists, tell the owner to delete it (trashing is a
  separate, approved action) and deliver the real file in chat so the owner can
  place it in the folder.

# Why

Drive connectors convert uploads to native Google types by default, and the
success response looks identical either way. Only the returned type and size
reveal the conversion.
