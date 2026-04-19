---
trigger: model_decision
description: ML engineering discipline — task framing, leakage prevention, baselines, evaluation, reproducibility, governance, and artifact management
---

# ML Experiment Discipline

Machine learning changes are not complete when the code runs. They are complete when the target, data boundaries, evaluation method, and limitations are all explicit.

## Define the Task First

Before changing features or models, write down:

- the prediction or decision objective
- the unit of analysis
- the target definition
- the inference or prediction time boundary
- the intended consumer of the output

Start with a clearly stated prediction or analytical objective, then establish a simple baseline before proposing a more complex model.

## Leakage Prevention

- Split data using the boundary that matches real-world inference: time, entity, geography, or experiment cohort.
- Split before fitting transforms whenever the transforms learn from data.
- Do not let features depend on information that would be unavailable at prediction time — no post-outcome fields, target-derived transforms, or future periods.
- Treat pre-aggregated analytical tables, marts, and notebook outputs as potentially leaky until feature provenance is verified.
- Be explicit about feature provenance for every derived variable used in modeling.

## Baselines and Metrics

- Always compare against a simple baseline before claiming improvement.
- Choose metrics that match the real decision cost, not just what is easiest to compute:
  - Regression: error metrics, residual behavior, and baseline comparisons.
  - Classification: class balance, threshold choice, confusion-matrix tradeoffs, and calibration when relevant.
  - Clustering: stability, silhouette or alternate diagnostics, and interpretability of cluster profiles.
- Include sample size, class balance, and important caveats with every evaluation summary.
- If thresholds are used, make threshold selection explicit and document the tradeoff.
- For small datasets, prefer robust validation and careful interpretation over aggressive optimization claims.

## Interpretation and Review

- Inspect feature importance, error slices, residual behavior, or confusion patterns before claiming success.
- Do not present predictive association as causal evidence.
- Document threshold choices, tradeoffs, and known failure modes if the model output is turned into a decision signal.
- Favor interpretable features and explainability when the output will influence public-sector, compliance, or anomaly discussions.

## Reproducibility

- Record reproducibility inputs: dataset version or time window, filters, target definition, feature list, random seeds, split strategy, and metric definitions.
- Keep feature generation and preprocessing deterministic where possible.
- Version the feature source or dataset snapshot used in the experiment.
- Prefer reusable pipelines or scripts over notebook-only model training logic when the work may be revisited.
- Reuse stable feature generation code from `src/` or other committed paths when notebook experiments become important to the project.

## Governance and Limits

- Report limitations honestly, especially for small samples, aggregate datasets, or proxy labels.
- Separate exploratory signal from production-ready evidence.
- Document major model limitations, fairness or bias caveats, and operational assumptions when outputs influence prioritization or decisions.
- If the project has governance, fairness, or public-policy constraints, document them with the experiment result.
- Document uncertainty, data limitations, and sample-size caveats before drawing strong policy or compliance conclusions.

## Artifact Discipline

- Keep exploration separate from reusable logic. When a loader, transform, feature builder, or metric becomes stable, move it into versioned source code and import it from notebooks.
- Distinguish analysis artifacts from operational artifacts. Figures and tables for reports are not a substitute for versioned training code, evaluation outputs, or deployment inputs.
- Version the code and document the data slice used for each reported result.
- Generated conclusions should be traceable back to code, data, parameters, and the exact artifact that produced them.
