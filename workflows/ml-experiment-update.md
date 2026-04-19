---
description: Update notebooks, feature pipelines, or model code with reproducibility, leakage checks, and deployment-minded ML discipline
---

# ML Experiment Update Workflow

Use this workflow for EDA, feature engineering, model training, statistical analysis, notebook revisions, and ML engineering changes.

---

## Step 1: Define the analytical change clearly

Write down the exact question before editing:

- What outcome or target is being modeled or explained?
- What data window or dataset version is in scope?
- Is the goal exploration, reporting, comparison, or operationalization?

If the objective is still fuzzy, avoid broad refactors until the experiment question is stable.

---

## Step 2: Inspect data, features, and splits

Confirm:

- Input datasets and filtering logic
- Feature definitions and derived columns
- Train, validation, and test split strategy
- Time-order or entity leakage risks
- Baselines already available in the repo

If sample size is small, be explicit about the limits of inference and the stability of metrics.

---

## Step 3: Choose notebook versus source-code placement

Use notebooks for iteration and narrative. Use versioned source code for stable logic:

- Move reusable loaders, transforms, metrics, and plotting helpers into `src/` once they are repeated
- Keep notebooks focused on orchestration, interpretation, and presentation
- Prefer deterministic parameters over hidden manual steps

---

## Step 4: Validate the experiment

Run the narrowest useful validation for the change:

- Notebook execution or the relevant scripted equivalent
- Unit tests for loaders, feature builders, or evaluators
- Baseline comparison
- Leakage and assumption checks
- Metric review with confidence or uncertainty caveats when appropriate

Do not present a model improvement without showing the baseline, metric definition, and evaluation slice.

---

## Step 5: Capture reproducibility and artifacts

Make the result reproducible by recording:

- Data source and time window
- Parameters and seeds
- Metrics and thresholds
- Output tables, figures, or reports
- Follow-up work needed to turn analysis into reusable code or deployment assets

---

## Step 6: Update paired deliverables

If the repo maintains translated notebooks, reports, or thesis chapters:

- Update both sides
- Keep commands, dataset names, and conclusions aligned
- Note any intentional drift instead of leaving silent mismatches

---

## Step 7: Hand off with engineering context

Summarize:

- What changed in the experiment
- Whether logic stayed in a notebook or moved into `src/`
- Reproducibility inputs
- Leakage or validity checks performed
- Remaining limitations and next steps
