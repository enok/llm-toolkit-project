---
title: A scheduled run marked SUCCEEDED in seconds is not evidence the work happened
category: monitoring
created: 2026-10-22
tags: [scheduled-task, last_run, succeeded, duration, verification, silent-failure, cowork]
---

# Problem
A nightly scheduled task reported `SUCCEEDED` every night, but each run lasted about 7
seconds. Its prompt required browser work and file writes, which take minutes. The status
looked healthy while nothing useful was being produced.

# Failed Approaches
- Reading the status (and an empty failure reason) as proof of success.
- Looking for per-run history to spot the pattern: the scheduling tool exposes only
  `last_run`, not past runs, so a single bad run and a months-long one look the same.

# Solution
- Compare the run's duration with the work the prompt requires. A job that opens a browser,
  reads pages or writes files cannot finish in seconds; flag it as "unverified", not "ok".
- Open the run's session and read what actually happened. Typical causes of an early,
  graceful exit: a permission request nobody could approve, the device or attached folder
  unavailable, a sign-in redirect, or a "nothing to do" shortcut.
- Fix the cause, fire the task once, and check the evidence of work (output file with a new
  modified time, message sent, report written), not just the status.
- Give prompts an explicit final step that writes a result marker or reports why nothing was
  done, so success has an observable output.
- Because only `last_run` is kept, record durations when you inspect (in the plan or ledger).

# Related

- `learnings/agent-self-reported-counts-are-not-evidence.md`: the same rule for counts an
  agent reports about its own work.

# Why
`SUCCEEDED` means the session ended without a platform error. An agent that declines,
cannot reach a resource, or decides there is nothing to do also ends cleanly, so status
alone cannot tell "finished the job" from "gave up quietly".
