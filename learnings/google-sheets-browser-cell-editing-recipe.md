---
title: Editing a Google Sheet through the signed-in browser - path choice and cell-editing recipe
category: toolchain
created: 2026-11-26
tags: [google-sheets, browser, tracker, cell-editing, connector, csv-export, read-back]
---

# Problem
A tracker sheet had to be read and updated, and the available surfaces differed per session.

# Failed Approaches
- CSV export as a reader: it returns only the first tab, and a 999-row checkbox column makes the
  export about 40 KB of base64.
- Typing into checkbox columns.
- Navigating away before the sheet saved.

# Solution
Preference order: a Sheets connector (read and write); the Drive connector for reading (each tab
as a table, long cells cut); otherwise the signed-in browser.

Browser recipe (UI labels observed 2026-10-22, may change):
1. Jump to a cell with `#gid=<tab>&range=<A1>`.
2. Type the value, Tab to the next cell, Enter to the first column of the next row.
3. Start new rows in the first free column and never type into checkbox columns.
4. Prefix `'` to keep ids and timestamps as text.
5. Find the first empty row with Ctrl+Up or Ctrl+Down.
6. Wait for the "Saved" indicator before navigating; an unsaved page raises a Leave-site dialog.
7. Read back through the CSV export and compare every written row.

Related: `drive-connector-reads-sheets-cannot-write-cells.md`,
`browser-extension-stalls-on-heavy-sheets-tab.md`, `drive-pdf-upload-converts-to-empty-google-doc.md`.

# Why
The connectors are read surfaces or may be missing; the browser path works only with
deterministic keyboard moves and a read-back that proves the write.
