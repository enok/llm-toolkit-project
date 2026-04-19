---
trigger: always_on
description: Analytical artifact governance, dataset discipline, reproducibility, and evidence hygiene for data science repositories
---

# Analytics Discipline

Analytical work should be repeatable by another engineer without hidden notebook state, missing environment details, or undocumented data assumptions.

## Artifact Governance

- Define the source of truth for every artifact pair: English plus translated docs, notebook plus exported report, or code plus generated figure.
- When a paired artifact changes, update both sides or leave an explicit note describing the remaining drift and where it will be resolved.
- Prefer text-friendly committed summaries (Markdown, JSON, CSV, code) over opaque binary-only outputs when preserving results or review evidence.
- Keep filenames, numbering, and headings aligned with pipeline stages or analysis sequence so reviewers can map outputs back to code and data.
- Charts, tables, and conclusions should include enough context to reproduce them: dataset, time window, aggregation level, filters, and metric definitions.
- Do not commit heavy notebook outputs or generated datasets unless the repository already treats those artifacts as source-of-truth inputs.

## Dataset Governance

- Every analytical dataset should declare its entity grain, time grain, primary keys, and intended use before new features are added.
- Keep feature engineering aligned with the question being answered. Regression, classification, and clustering datasets may need different grains and filtering rules.
- Derived columns must be traceable to committed transformations, documented notebook cells, or config-driven rules.
- Name features so units and time meaning stay obvious. Prefer columns like `income_change_pct` or `sanctions_per_100k` over ambiguous short names.
- When aggregating from one entity level to another, validate that the numerator, denominator, and weighting strategy still match the analytical objective.
- Treat translation maps and loader dataset maps as part of the analytical contract when localized notebooks or reports depend on them.
- Add or update tests when new analytical datasets, feature columns, or dataset aliases are introduced.
- If a feature can leak future information or post-outcome signals, exclude it or document the reason it is still valid for the task.

## Data Artifact Hygiene

- Do not commit generated datasets, temporary exports, cache files, credentials, or local-only environment state.
- Large plots, tables, and reports should be committed only when they are intentionally reviewed artifacts and their regeneration path is documented.
- Prefer reproducible source code, configs, and small markdown summaries over opaque binary artifacts.
- Keep notebook outputs focused. Avoid committing noisy cell output that obscures the logic or inflates diffs unless the output itself is the reviewed artifact.
- Never hardcode local machine paths, personal buckets, or ad hoc file drops inside notebooks or scripts.
- Logs and audit artifacts should use stable names and timestamps so reruns are easy to compare.
- When the repo contains sensitive public-sector or compliance data, double-check masking, row-level exposure, and screenshots before committing anything derived from it.

## Reproducibility

- Set explicit random seeds for sampling, splitting, and model training when randomness is involved.
- Record the dataset snapshot, source path, or extraction date that supports the analysis.
- Make environment assumptions explicit: Python version, required packages, cloud profile, local paths, or feature flags.
- If logic is reused across notebooks, scripts, or production code, extract it into `src/`, a shared utility, or a documented pipeline step.
- Treat plots, tables, and markdown conclusions as derived artifacts that should be reproducible from committed code.
- Do not hand-edit generated tables, cached exports, or audit logs unless the task is specifically about repairing a broken artifact.
- When a result depends on filtering or exclusions, document the rule next to the result.

## Statistical Honesty

- State sample-size limitations and uncertainty clearly.
- Separate exploratory findings from confirmed conclusions.
- If a notebook changes project-facing conclusions, update the related docs in the same change.
