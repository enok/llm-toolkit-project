---
name: notebook-analysis
description: Work safely in Jupyter notebooks and analysis reports. Use for EDA, statistical analysis, plots, notebook cleanup, narrative reporting, translation of notebook markdown, and extracting reusable code from exploratory work.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Notebook Analysis

Help engineers improve notebooks without sacrificing reproducibility, readability, or downstream reuse.

## When to Apply

- exploratory data analysis
- statistical testing notebooks
- visualization or dashboard prototyping in notebooks
- notebook cleanup and restructuring
- extracting notebook logic into reusable modules
- localized notebook markdown updates

## Steps

1. Inspect the notebook inputs first: loaders, source datasets, cache paths, and environment assumptions.
2. Keep the notebook readable: clear markdown, deterministic cell order, and explicit assumptions.
3. Set seeds when randomness is used and make filtering or exclusion logic visible near the result.
4. Extract reusable transformations or feature logic into code when it is no longer one-off exploration.
5. Restart and run all before finishing.
6. Keep outputs lightweight enough for review and version control.
7. Update paired docs or localized notebook text when findings or conclusions changed.

## Related Rules And Workflows

- `rules/analytics-reproducibility.md`
- `rules/bilingual-doc-sync.md`
- `workflows/notebook-analysis-update.md`
- `workflows/bilingual-doc-sync.md`

## Pair With

- `ml-engineering`
- `python-best-practices`
- `doc-delta`
