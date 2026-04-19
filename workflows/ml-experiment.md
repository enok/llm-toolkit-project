---
description: Run or update an ML experiment with explicit baselines, leakage checks, and reproducible evaluation
---

# ML experiment workflow

Use when changing feature engineering, model training, evaluation, thresholds, or experiment reporting in a data science or AI/ML engineering project.

## Steps

1. Write down the objective, target, unit of analysis, inference boundary, and intended decision before changing code.
2. Inspect the dataset source, feature pipeline, and split strategy before adding new features or models.
3. Check for leakage and temporal or entity overlap before trusting any metric improvement.
4. Establish or preserve a simple baseline so the new approach has a meaningful comparison point.
5. Choose metrics that match the problem and document threshold or calibration decisions explicitly when classification is involved.
6. Keep feature generation and preprocessing in reusable code when the experiment may be revisited or promoted beyond a notebook.
7. Record the dataset version, seed, major parameters, and key results in a doc, notebook section, or experiment summary.
8. Update downstream docs if the experiment changes feature semantics, operational recommendations, or published conclusions.
