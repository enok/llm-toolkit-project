---
title: Chained email-to-folder and workbook-update tasks - split ingest from update and harden both
category: security
created: 2026-11-26
tags: [scheduled-task, email, automation, workbook, formula-injection, allow-list, sha256, dry-run, additive]
---

# Problem
A recurring flow had to turn emailed documents into saved files and then into rows of a
workbook. One task doing both was hard to review. The first scheduled firing also ran with the
old prompt and did nothing.

# Failed Approaches
- One task that downloads, parses and rewrites the workbook.
- Editing the task prompt after enabling it.
- Storing password material or personal ids in the prompt.

# Solution
Two chained tasks with a shared contract file:
- **Ingest task** is only the mail downloader: it removes mail-carried passwords, saves under the
  existing naming convention, emails the saved paths only when something new arrived, and uses a
  lookback window with slack and a cutoff date for the first run. Dry-run the first run and list
  the files it expects to save.
- **Update task** runs later, reads the saved files and changes the workbook additively (never
  regenerates), keeps a state file and a log, and ignores history before the cutoff.
- Update the prompt BEFORE enabling or first firing.
- Review findings:
  - Cells that start with `=`, `+`, `-` or `@` are prefixed so they stay text (formula injection).
  - Connector write tools cannot be removed from a task, so the prompt carries an allow-list and
    pins the SHA-256 of every script it may run; re-pinning needs the owner's approval.
  - No unattended deletes; unknown or generic routes go to quarantine; a poison-pill guard stops
    on `#REF`; regex limits; a spreadsheet-lock check before each commit.
  - A first create may attach only one requested folder: recreate once and verify.
- Local-folder tasks run only while the computer is on with the app open; say so in the task
  description.
- Never put derived passwords, tax ids, biller names or folder paths in the prompt; use an
  untracked local secrets file.

# Why
Splitting the writers gives each task a small blast radius, and additive updates plus pinned
scripts make unattended runs reviewable.
