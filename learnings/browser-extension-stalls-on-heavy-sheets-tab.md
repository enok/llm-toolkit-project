---
title: The browser extension can stall for minutes on a hosted spreadsheet tab; fall back to a CSV import
category: toolchain
created: 2026-10-22
tags: [google-sheets, browser, extension, timeout, csv-import, fallback, approval-prompt]
---

# Problem

Navigating the automation tab to a hosted spreadsheet to fill rows made the next
browser calls time out after minutes ("no result received"), and a following
context call timed out too. The Drive connector could read the sheet but exposes
no cell-writing tool.

# Failed Approaches

- Retrying the same call several times.
- Waiting for the grid to load before screenshotting (zero-width screenshot).

# Solution

- Read the sheet structure with the Drive connector first (columns, existing
  rows), so the data can be prepared without the browser.
- If the extension stalls, stop after one retry; ask the owner to check for a
  pending permission prompt in the desktop app.
- Save the rows as a CSV in the sheet's exact column order beside the working
  files and give the import steps: select the first empty cell, File -> Import ->
  Upload -> "Replace data at selected cell", then delete any duplicated header.
- Tell the owner which columns were left blank because the data was unknown.

# Related

- `learnings/drive-connector-reads-sheets-cannot-write-cells.md`: what the connector can
  and cannot do with a sheet, and the order of fallbacks.

# Why

Heavy single-page apps and unanswered approval prompts can hang the extension
bridge; a file the owner can import in thirty seconds beats an open-ended retry.
