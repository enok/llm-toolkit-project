---
title: A scheduled job can overwrite a newly rebuilt source-of-truth file with an older generation
category: toolchain
created: 2026-11-26
tags: [scheduled-task, sync, regeneration, source-of-truth, dry-run, csv, tsv, overwrite]
---

# Problem
A plan document was rebuilt interactively. A weekly scheduled task that regenerated or synced
the same file from an older generator was about to overwrite the new version with the old plan.
A related nightly sync pushed a CSV into a third-party sheet template.

# Failed Approaches
- Finishing the rebuild without asking which scheduled tasks write the same file.
- Letting a nightly sync write straight into the authoritative file.
- Pasting a hand-converted CSV into the sheet without checking it against the sheet schema.

# Solution
- After rebuilding any generated plan or document, list every scheduled task that writes the same
  file (sync, weekly regeneration) and repoint or disable it.
- A nightly sync runs a dry run on copies first and never overwrites the authoritative file with
  an older generation.
- Convert CSV to TSV with a deterministic step and validate it against the target sheet schema
  before pasting.
- Add this audit to the checklist whenever a generated artifact changes
  (`workflows/automation-maintenance.md`).

# Why
Scheduled tasks keep their own copy of the old assumptions and run unattended, so the newest
version loses silently unless someone reconciles the writers.
