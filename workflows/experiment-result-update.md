---
description: Propagate an analytical or model result change into the docs, notebooks, and supporting context that depend on it
---

# Experiment Result Update Workflow

Use when a notebook, model, statistic, or pipeline rerun changes a result that is referenced in docs, reports, or decision notes.

## Steps

1. Identify the changed result and the artifact that produced it.
2. Confirm whether the change came from:
   - new data
   - code changes
   - different filters or assumptions
   - bug fixes
3. Update the result where it is interpreted:
   - notebook markdown
   - report or README sections
   - thesis-supporting docs
   - translated counterparts
4. State the new limitations, sample size, and assumptions if they materially affect interpretation.
5. If the result changes a downstream threshold, feature choice, or operational decision, document that linkage explicitly.

## Exit Criteria

- The producing code and consuming narrative agree.
- Assumptions and caveats are current.
- Downstream docs are not quoting stale numbers.
