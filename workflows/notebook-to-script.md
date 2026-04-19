---
description: Promote stable notebook logic into reusable code, scripts, or pipeline steps
---

# Notebook to script workflow

Use when a notebook contains logic that is no longer one-off exploration and should become reusable, testable, or schedulable code.

## Steps

1. Identify the stable logic to promote: loaders, preprocessing, feature engineering, validation, chart builders, or report generation helpers.
2. Separate reusable code from notebook-only narrative, visual interpretation, and scratch exploration.
3. Extract the logic into `src/`, a helper module, or a script with explicit inputs and outputs.
4. Replace duplicated notebook cells with imports or function calls so the notebook becomes a consumer of reusable code.
5. Add focused tests or validation checks for the promoted logic.
6. Update docs so future notebook work starts from the reusable path instead of re-copying cells.
7. Re-run the notebook end to end after the extraction to confirm the behavior still matches.
