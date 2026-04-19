# Machine Learning Engineering Rules (Template)

> **This is a template.** Copy and tailor it for repositories with feature engineering, modeling, and evaluation workflows.

## Modeling Scope

- **Primary task types:** [regression, classification, ranking, clustering, forecasting]
- **Prediction unit:** [user, account, device, transaction, document, organization]
- **Prediction horizon or observation window:** [describe]
- **Main feature sources:** [analytical tables, warehouse marts, notebook outputs, feature store]

## Baselines and Evaluation

- Required baselines: [mean predictor, logistic regression, historical average, rules-based baseline]
- Split policy: [time-aware, grouped by entity, stratified, rolling window]
- Metrics to report: [RMSE, MAE, AUC, F1, calibration, silhouette, etc.]
- Leakage checks: [what future or label-derived fields must be excluded]

## Reproducibility

- Random seed policy: [fixed seeds, repeated runs, confidence intervals]
- Artifact policy: [where metrics, plots, and model summaries live]
- Promotion rule: [when notebook code must move into `src/`]

## Documentation Expectations

- Summarize model purpose, feature set, metrics, and limitations in markdown.
- Add caveats for fairness, policy sensitivity, or operational risk when relevant.
- Update translated docs or reporting layers if the repo maintains more than one language.
