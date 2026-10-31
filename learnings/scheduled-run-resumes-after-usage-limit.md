---
title: A scheduled run that ends FAILED on a usage limit may resume later and overlap a catch-up
category: monitoring
created: 2026-10-22
tags: [scheduled-task, fire_trigger, usage-limit, catch-up, overlapping-runs, single-run-guard, mtime-guard, tracker]
---

# Problem
A daily scan task (one schedule only) skipped its normal run while it was paused for a folder
move. Afterwards, catch-up runs were fired by hand. The owner received three digest emails and
the run history showed more sessions of the task than fires.

# Failed Approaches
- Treating a catch-up that ended FAILED as finished: the first catch-up ended FAILED with reason
  USAGE_LIMIT_REACHED after about 9 minutes, and a second catch-up fired 2 hours later ended the same way.
- Firing again until one succeeded: the third fire, hours later, succeeded (22 minutes), but it was
  not the only run of that day.

# Solution
What happened, in order:
- During the successful third run, two other sessions of the same task also ran: one of about 41
  minutes that started before the third fire, and one of about 1 minute that saw the work already
  done and only sent a note.
- Most likely these two were the FAILED catch-ups resuming once usage returned. This was inferred
  from timing, not confirmed.
- The shared xlsx tracker survived because every write was guarded by the file's mtime: one write
  aborted with exit 3, the run re-read the file and redid the write. A read-only audit afterwards
  found no duplicate ids.

General guidance, not observed in this session: before a catch-up fire check the run history for
FAILED runs that may still resume, fire at most once, add a single-run guard to the prompt, and
audit shared files after a suspected overlap (`workflows/automation-maintenance.md`).

# Why
The overlap suggests that a run that ends FAILED on a usage limit is not necessarily dead: the
scheduler may continue it once usage is available (cause inferred from timing, not confirmed). A
hand-fired catch-up would then run beside it, and the task has no way to know about the other
session unless its prompt checks for work already done today.
