---
trigger: always_on
description: Contract-first data pipeline changes - metadata, schemas, lineage, partitions, and backfill safety
---

# Data Pipeline Contracts

Treat data contracts as first-class code. In analytics platforms, schemas, keys, grain, partitions, filenames, storage paths, and metadata configs are part of the public surface area.

## Contract Sources

Before editing pipeline code, identify the authoritative source for:

- dataset metadata
- schema definitions
- partition strategy
- naming conventions
- translation or semantic dictionaries
- orchestration entrypoints

If behavior changes, update the contract artifact in the same change.

## Layer Boundaries

- Raw or Bronze layers preserve source fidelity, ingestion traceability, and replayability.
- Clean or Silver layers normalize types, keys, and schema shape.
- Gold, marts, or feature-ready layers hold analysis-facing aggregates, features, or summary tables.

Do not hide Silver or Gold logic inside raw ingestion unless the upstream source contract truly changed.

## Non-Negotiables

- Grain, primary keys, time semantics, and join semantics are contracts.
- Stable storage paths, partitions, and filenames are contracts once downstream readers depend on them.
- Backfill requirements, cache invalidation, and reprocessing cost must be reviewed before merging.
- Prefer idempotent, incremental, observable processing over one-off rewrites.
- Fail loudly on unexpected schema drift instead of silently coercing data away.

## Review Checklist

For pipeline changes, inspect the impact on:

- config and contract files
- ingestion or extraction code
- transformation or feature code
- orchestration scripts and jobs
- tests and fixtures
- documentation and runbooks
- generated evidence or audit artifacts

## Promotion Rule

If a transformation matters outside a single notebook or ad hoc analysis, move it into reusable code or a documented pipeline step.
