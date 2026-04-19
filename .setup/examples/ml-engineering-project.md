# ML Engineering Project Context (Template)

> **This is a template.** Copy it and fill in the project-specific details.

## Modeling Objective

- **Prediction or ranking task:** [what the model should do]
- **Unit of analysis:** [row, user, account, transaction, device, document, organization]
- **Target definition:** [how the label is built]
- **Inference boundary:** [what is known at prediction time]

## Data And Features

- **Training sources:** [tables, buckets, datasets, feature views]
- **Feature generation path:** [scripts, pipelines, notebooks, services]
- **Leakage risks to watch:** [time overlap, future data, target leakage, entity leakage]
- **Feature ownership:** [who or what process maintains them]

## Evaluation

- **Split strategy:** [time split, grouped split, random split]
- **Baseline:** [simple heuristic or existing model]
- **Primary metrics:** [RMSE, MAE, ROC AUC, F1, MAP, calibration, etc.]
- **Threshold policy:** [if classification or ranking thresholds exist]

## Artifact Management

- **Experiment summary location:** [docs, notebooks, tracking tool]
- **Model artifacts location:** [S3, registry, local folder]
- **Dataset version or snapshot rule:** [how data versions are tracked]
- **Deployment or scoring path:** [batch, online, notebook-only, BI export]

## Working Conventions

- Keep feature logic reusable and out of ad hoc notebook cells when it may be reused.
- Record seeds, dataset versions, and key parameters for repeatable runs.
- Compare new work against a simple baseline.
- Update docs when model semantics, metrics, or conclusions change.
