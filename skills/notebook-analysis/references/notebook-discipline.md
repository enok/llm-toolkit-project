---
trigger: always_on
description: Jupyter notebook discipline — execution order, structure, output hygiene, reproducibility, and promotion boundaries
---

# Notebook Discipline

Committed notebooks should remain understandable and rerunnable even after the original author is gone.

## Execution Discipline

- A committed notebook must restart cleanly and run all cells in order (`Restart Kernel and Run All`).
- Do not rely on hidden kernel state, out-of-order execution, or manually patched variables.
- Keep environment assumptions explicit: kernel, Python version, packages, credentials, data paths, and cloud profile.

## Structure

- Start with a short setup section that states data prerequisites, configuration, and assumptions.
- Use markdown cells to explain the question, the data inputs, the key assumptions, and the interpretation of results.
- Keep imports and configuration near the top so a reviewer can understand the runtime quickly.
- Group sections clearly: setup, data load, quality checks, analysis, interpretation, and next steps.
- Keep plots, tables, and markdown conclusions close to the code that produces them.

## Output Hygiene

- Keep large or noisy outputs out of committed notebooks unless they are essential to the review.
- Clear stale outputs when they no longer match the current code or data.
- Do not commit massive datasets, local cache artifacts, or screenshot-only evidence in place of reproducible code.
- Avoid hardcoded local machine paths, personal buckets, or ad hoc file drops inside notebooks or scripts.

## Reproducibility

- Every important notebook should make these items easy to find near the top: data source or loader entrypoint, key assumptions and filters, random seeds or deterministic settings, and expected outputs or saved artifacts.
- Set explicit random seeds for sampling, splitting, and model training when randomness is involved.
- Record the dataset snapshot, source path, or extraction date that supports the analysis.
- Statistical claims in markdown cells should match the code that produced them. Update narrative text when assumptions, samples, or metrics change.
- Re-run notebooks from a clean kernel before treating results as final.

## Reuse and Promotion Boundary

- Use notebooks for exploration, explanation, visualization, and result narration.
- Move reusable business logic, data loading, feature engineering, and evaluation code into `src/`, scripts, or documented pipeline steps.
- Avoid keeping the only copy of important transformation logic inside a notebook.
- Avoid copy-pasting business logic across notebooks. Prefer loaders and helper functions that make data access explicit and testable.
- If a notebook cell becomes operational, repeated, or testable logic, promote it into Python modules or scripts.
- If a finding affects product, pipeline, or report decisions, reflect it in committed docs or tests instead of leaving it only in notebook prose.
- If notebook pairs exist in more than one language, update both or document why only one changed.
