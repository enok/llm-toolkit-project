---
title: The Drive connector reads every Sheet tab but cannot write cells - plan the write path
category: toolchain
created: 2026-11-26
tags: [google-drive, google-sheets, connector, browser, tracker, template-mapping, resume, revalidate]
---

# Problem
Filling a flat template sheet from a multi-tab tracker needed both reads and cell writes. The
Drive connector could read the tracker but had no tool to edit cells, and the built-in browser
pane was signed out of Google.

# Failed Approaches
- Exporting the sheet as CSV to read it: the export contains only the first tab, so the other
  tabs (and dropdown lists) were missing.
- Looking for a cell-edit action on the Drive connector: it does not have one.
- Resuming a plan approved weeks earlier without re-reading the source: the tracker had grown
  (10 to 27 rows), statuses had changed and dates had been corrected.

# Solution
- **Read:** the Drive connector's content read returns every tab, including dropdown lists.
  Use it instead of CSV export. Cross-check a PDF-sourced copy with
  `learnings/drive-pdf-upload-converts-to-empty-google-doc.md` when relevant.
- **Write:** use a Sheets connector if one is installed; otherwise drive the signed-in browser
  into the same file. Use the user's own Chrome, because the built-in browser pane may not be
  signed in. A heavy sheet tab can stall the extension; see
  `learnings/browser-extension-stalls-on-heavy-sheets-tab.md`. The browser write recipe is in
  `learnings/google-sheets-browser-cell-editing-recipe.md`.
- **Mapping:** when a multi-tab tracker maps to a flat template, write an explicit column map
  and a rows builder plus a validator script, and run the validator before writing.
- **Resume:** a plan approved earlier must re-verify its source on resume (row count, statuses,
  dates) before any write, and write only after the user re-approves changed scope
  (`rules/external-write-authorization.md`).

# Why
The connector is a read surface; edits need a tool that exposes cell updates or a real browser
session. Sources change between approval and execution, so an old approval covers the data as
it was then, not as it is now. Do not record sheet ids or owners in shared notes.
