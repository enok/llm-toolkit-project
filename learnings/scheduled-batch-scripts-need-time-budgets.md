---
title: Scheduled batch scripts need per-item alarms and a global time budget below the tool timeout
category: toolchain
created: 2026-11-26
tags: [scheduled-task, batch, timeout, budget, alarm, parsing, idempotency, bom, retries]
---

# Problem

A daily scheduled script parsed many email attachments. One slow PDF stalled the whole run
until the shell tool timed out, and because the run restarted from the same state the next
day, the same item killed every run.

# Failed Approaches

- One global timeout only: a single slow item consumes the entire budget.
- Quadratic regular expressions on untrusted text: a crafted or merely large input takes
  minutes.
- A script that stops at the first error: one bad message hides the rest of the batch.
- Re-running an assign or drop step with the raw-content flag omitted: the item or its
  manifest entry was lost.

# Solution

- Put caps on sizes and counts, and use linear-time parsing (an HTML parser, not regexes
  with nested quantifiers) for untrusted text.
- Give each message its own alarm (about 90 seconds) and wrap it in try/except that records
  an error status and a bounded retry count, then moves on.
- Set a global budget strictly below the tool timeout, which itself is below the foreground
  cap, for example budget 420 s < tool timeout 540 s < 10-minute foreground cap.
- Make state handling tolerant: the state file may be `{}`; read text files with
  `utf-8-sig` so a byte-order mark does not corrupt the first key; skip comment lines in
  secret or allowlist files.
- Before committing a file, check the final path with `[ -e ]` and never overwrite, including
  items marked locked.
- Re-run assign or drop steps with the same raw flag the first pass used, or the manifest
  loses the item.

# Why

A bounded unit of work per item and a bounded total turn a poison item into one recorded
error instead of a daily outage, and idempotent writes make the retry the next day safe.
Related: `learnings/short-succeeded-run-is-not-evidence-of-work.md`,
`workflows/automation-maintenance.md`.
