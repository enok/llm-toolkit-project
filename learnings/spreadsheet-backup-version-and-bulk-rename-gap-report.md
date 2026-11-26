---
title: Spreadsheet sessions - versioned backups, linked ledgers and a gap report after bulk renames
category: toolchain
created: 2026-11-26
tags: [spreadsheet, backup, ledger, bulk-rename, gap-report, assumptions, calendar, new-chat]
---

# Problem
Sessions that rebuilt planning spreadsheets and renamed document sets repeated the same slips:
overwriting the old version, mixing two ledgers, hiding assumptions and leaving gaps unreported.

# Failed Approaches
- Editing the only copy of a workbook.
- Keeping personal and company figures in one ledger.
- Computing before checking the calendar and mailbox for due items.

# Solution
- Keep separate ledgers separate and link them by cell reference.
- Write a new version and keep the old as a backup.
- When told to remove fixed values, replace placeholders with the figures from the statements.
- Check the calendar and mailbox for due items before computing.
- Scenario analyses print their assumptions (rates, dates, lags).
- Bulk rename: derive the period from the data (for example month to quarter), apply it to the whole
  set, then list the gaps found (missing documents).
- Start a new chat when contexts must not mix.
- Related: `skills/folder-reorganization/SKILL.md`.

# Why
Versioning makes every change reversible, and a gap report turns a rename into an audit of what is
missing.
