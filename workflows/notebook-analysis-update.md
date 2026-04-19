---
description: Update notebooks, EDA, or statistical analysis while preserving reproducibility
---

# Notebook analysis update workflow

Use when changing Jupyter notebooks, exploratory analysis, statistical tests, visualizations, or notebook-driven reporting.

## Steps

1. Confirm the source dataset, snapshot date, loader path, or extraction command behind the notebook.
2. Read the notebook together with any helper modules or loaders it depends on before editing cells.
3. Separate scratch work from reportable analysis. If the notebook is project-facing, keep the narrative clear and the cell order deterministic.
4. Set or confirm random seeds for sampling, splits, and model training when applicable.
5. Extract reusable logic to code if it appears in multiple cells, multiple notebooks, or project-facing scripts.
6. Restart and run all before considering the change complete.
7. Keep outputs reviewable. Avoid unnecessary heavy binary output or stale cell results.
8. Update related docs, findings summaries, and localized notebook text when the conclusions or interpretation changed.
