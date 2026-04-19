---
name: data-governance
description: Review dataset provenance, privacy, licensing, and evidence integrity in analytics projects. Use for new datasets, public-sector or regulated analytics, masking decisions, data-sharing concerns, and documentation of lineage or audit artifacts.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Data Governance

Help engineers make data changes that are technically correct and operationally legitimate.

## When to Apply

- onboarding a new dataset
- reviewing provenance or licensing questions
- handling sensitive identifiers or masked data
- public-sector or regulated analytics
- audit logs, validation reports, and lineage-sensitive outputs
- deciding what can be shared, exported, or published

## Steps

1. Confirm where the data comes from, who is allowed to use it, and what retention or sharing constraints exist.
2. Review the project grain and purpose before adding sensitive or individual-level fields.
3. Keep lineage explicit from raw data through cleaned tables, analytical outputs, and published artifacts.
4. Prefer fixing generators or pipelines over hand-editing audit evidence.
5. Document masking, exclusions, imputations, and major assumptions where the data is transformed and interpreted.
6. Escalate when a change would materially widen access, identifiability, or downstream use.

## Related Rules And Workflows

- `rules/data-governance.md`
- `rules/data-pipeline-contracts.md`
- `workflows/dataset-onboarding.md`
- `workflows/bilingual-doc-sync.md`

## Pair With

- `security`
- `data-pipeline`
- `doc-delta`
