---
name: ml-experiment
description: |
  Run or update ML experiments with baselines, leakage checks, and reproducible
  evaluation. Use for model training, feature engineering, classification,
  regression, clustering, or model comparison.
license: MIT
---

# ML Experiment

Run or update ML experiments with proper baselines, leakage prevention, and reproducible evaluation.

> **Reference**: For complete guidance, see `workflows/ml-experiment.md` and `rules/ml-experiment.md`

## Quick Reference

### Task Framing
- Define the prediction/optimization target clearly
- Specify success metrics before training
- Establish baseline (random, majority class, simple heuristic)

### Leakage Prevention
- Train/test split by time (not random) for temporal data
- No future information in feature engineering
- Cross-validation aware of data dependencies
- Feature scaling fit on train only, applied to test

### Dataset Governance
- Document entity grain, time grain, primary keys
- Keep feature engineering aligned with question
- Validate aggregations match analytical objective
- Check for features that leak future information

### Evaluation
- Hold-out test set never used during development
- Report confidence intervals where possible
- Compare against baseline, not just previous model
- Document assumptions, exclusions, limitations

### Reproducibility
- Set explicit random seeds
- Record dataset snapshot/version
- Version control code, not just notebooks
- Document environment (Python version, packages)

## When to Apply

- Designing a new ML experiment
- Training classification/regression models
- Feature engineering for ML
- Evaluating model performance
- Preventing train/test leakage
- Promoting notebook experiments to production

## Related

- `workflows/ml-experiment.md` — Complete workflow
- `rules/ml-experiment.md` — ML experiment rules
- `skills/notebook-analysis` — EDA before ML
