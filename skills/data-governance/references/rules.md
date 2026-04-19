---
trigger: always_on
description: Dataset governance for analytics projects - provenance, licensing, privacy, and evidence integrity
---

# Data Governance

Data science projects are accountable not only for code quality, but also for the legitimacy and traceability of the data they use.

## Provenance

- Know where each dataset comes from, how it was collected, and under what license or usage terms it can be used.
- Preserve lineage between raw data, cleaned data, analytical tables, and published outputs.
- Prefer append-only or replayable raw storage when reproducibility matters.

## Privacy And Sensitivity

- Minimize sensitive fields and identifiers to what the analysis truly needs.
- Do not expose credentials, raw secrets, or local auth material in code, notebooks, or generated outputs.
- If a project operates at aggregate level, do not add logic that turns it into individual profiling without an explicit decision.

## Evidence Integrity

- Treat audit logs, extraction logs, metadata files, and validation reports as evidence artifacts.
- Prefer fixing the generator or pipeline over hand-editing evidence artifacts.
- When exclusions, imputations, or masking rules are applied, document them where the data is transformed and where the result is interpreted.

## Governance Review

For new datasets or analytical outputs, review:

- licensing and permitted use
- retention expectations
- masking or de-identification
- downstream sharing scope
- documentation of assumptions and known gaps
