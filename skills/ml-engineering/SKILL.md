---
name: ml-engineering
description: Design and update feature engineering, model training, evaluation, and experiment reporting in end-to-end data science projects. Use for ML experiments, feature pipelines, model baselines, leakage checks, threshold tuning, notebook-to-code promotion, and analysis-ready datasets.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# ML Engineering

Help engineers make machine learning changes that are reproducible, comparable, and honest about their limits.

## When to Apply

- feature engineering changes
- model training or evaluation changes
- baseline comparisons
- leakage checks and split strategy reviews
- threshold, calibration, or metric decisions
- promoting notebook logic into reusable code

## Steps

1. Define the task in plain language: objective, target, unit of analysis, inference boundary, and consumer.
2. Inspect the dataset source and split strategy before changing features or models.
3. Check for leakage, temporal overlap, or entity overlap before trusting any result.
4. Compare against a simple baseline and pick metrics that fit the real decision.
5. Keep reusable preprocessing and feature logic in code, not trapped inside a notebook.
6. Record seeds, dataset versions, major parameters, and result summaries so the run can be reproduced.
7. Update docs or analysis summaries when the interpretation or recommended action changes.

## Related Rules And Workflows

- `rules/analytics-reproducibility.md`
- `rules/ml-experiment-rigor.md`
- `rules/data-governance.md`
- `workflows/ml-experiment.md`
- `workflows/notebook-analysis-update.md`

## Pair With

- `python-best-practices`
- `testing`
- `notebook-analysis`
- `data-governance`
