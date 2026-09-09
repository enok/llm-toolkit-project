---
name: data-pipeline
description: Plan and implement ingestion, transformation, schema, storage, and backfill changes in data platforms. Use for Bronze or Silver or Gold layers, raw or staging or curated datasets, metadata-driven pipelines, S3 or warehouse paths, incremental loads, and lineage-sensitive work.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Data Pipeline

Help engineers make safe changes to data platforms where contracts, lineage, and reprocessing cost matter.

## When to Apply

- adding or changing ingestion jobs
- schema or partition changes
- storage path or naming changes
- dataset onboarding
- backfills, reprocessing, or cache invalidation
- S3, warehouse, Airflow, or script-driven data movement

## Steps

1. Find the authoritative contract first: metadata, schemas, naming rules, translation maps, or orchestration config.
2. Trace the impacted flow across config, ingestion code, transformation code, scripts, tests, and docs before editing.
3. Protect layer boundaries. Raw layers keep source fidelity; clean layers normalize; analytical layers aggregate or prepare features.
4. Review the operational blast radius: downstream readers, storage paths, partitions, backfills, cost, and evidence artifacts.
5. Implement the smallest safe change that stays idempotent and observable.
6. Verify with focused validation first, then broader tests if the change crosses layers.
7. Document reruns, backfills, and downstream expectations when behavior changes.

## Related Rules And Workflows

- `skills/data-pipeline/references/data-pipeline-contracts.md`
- `skills/data-governance/references/rules.md`
- `workflows/dataset-onboarding.md`
- `workflows/data-pipeline-change.md`

## Pair With

- `python-best-practices`
- `shell-scripting`
- `testing`
- `terraform`
- `security`
