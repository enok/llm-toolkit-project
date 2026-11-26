---
description: Validate a batch of job-posting analyses - re-check sampled rows against the source postings, the pay math, duplicates, and the tier recommendations before they go into a plan or tracker
---

# Job Posting Analyst Validation

Use this workflow when `tool-subagents/job-posting-analyst.md` has returned rows
and the root agent is about to put them in a plan document, a tracker or a
shortlist for the owner.

## Steps

1. Establish the inputs: the candidate profile figures used (floor, target,
   currency, period), the posting list, and which postings the analyst marked
   `not read`.
2. Invoke or follow `tool-subagents/job-posting-analyst.md` for any posting still
   unread (one retry each); otherwise leave it out of rankings and say why.
3. Sample at least a third of the rows (all rows if fewer than six) and re-open the
   source posting: confirm pay, location/work mode, contract form, required
   stack and any residency or work-authorization text.
4. Re-do the pay math for every sampled row: annual / 12, hourly x hours x
   realization, FX assumption and range. Reject a row whose normalized pay cannot
   be reproduced from the posted figure.
5. Check duplicates and superseded rows against the known-applied list and each
   other (same client via agency and direct, same task at two bands).
6. Check tiers: no `apply-now` row below the floor; no row marked passing with
   unknown pay or unknown work authorization; deal-breakers respected.
7. Accept only evidence-backed corrections; route the rest back with a defect
   list (`mechanical` or `reasoning`) through `workflows/task-quality-loop.md`.
8. Report findings, rows changed, validation done and residual risk (rows not
   re-opened, FX uncertainty).

---

## Evolution

If the analyst misses a recurring issue or is too noisy, run
`workflows/job-posting-analyst-evolution.md`.
