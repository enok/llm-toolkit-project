---
title: A hung CI run needs force-cancel through the API, then a rerun
category: toolchain
created: 2026-10-07
tags: [github-actions, ci, hung-job, force-cancel, rerun, gh-api, timeout]
---

# Problem

A CI validate job hung for 50 minutes with no output. The session recorded this as a
low-severity env-constraint mistake, detected by CI itself.

# Failed Approaches

None recorded beyond the first attempt described in Problem: the job produced no output
for 50 minutes, and the recorded fix is the force-cancel below.

# Solution

Treat a job that sits in progress with no output far past its usual run time as hung, not
slow. Force-cancel the run through the API, then rerun it:

```text
POST /repos/<owner>/<repo>/actions/runs/<run-id>/force-cancel
```

Illustrative `gh` form, with placeholders (not executed in the authoring session):

```text
gh api -X POST repos/<owner>/<repo>/actions/runs/<run-id>/force-cancel
```

Force-cancel changes the run's state on the host, so get the user's go for that run first
(`rules/external-write-authorization.md`). Then start the run again. The record says "rerun
it" and does not name the rerun command.

# Why

The record gives the symptom (50 minutes, no output) and the fix, not the cause of the
hang. General guidance, not observed in this session: GitHub provides the force-cancel
endpoint for runs that do not respond to a normal cancel, which is why it is the recorded
fix for a run that is stuck. Related: `learnings/hanging-validator-trains-agents-to-skip-validation.md`
covers a validator that hangs every time, which is a defect to fix and not a run to cancel.
