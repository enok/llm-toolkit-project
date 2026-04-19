# Data Pipeline Rules (Template)

> **This is a template.** Copy and replace the placeholders with your medallion, batch, or analytics pipeline details.

## Pipeline Topology

| Layer | Purpose | Storage | Main code paths |
|------|---------|---------|-----------------|
| Bronze / Raw | [source-faithful capture] | [S3, GCS, local lake] | `[src/ingestion/]` |
| Silver / Clean | [normalized and joinable] | [Parquet, Delta, tables] | `[src/processing/]` |
| Gold / Analytics | [aggregates, features, reporting] | [warehouse, parquet, mart] | `[src/analysis/]` |

## Contracts to Treat as Source of Truth

- Metadata/config files: `[config/*.json, yaml, etc.]`
- Schema definitions: `[schemas/, contracts/, protobuf, dbt models]`
- Dataset loaders or registries: `[src/.../data_loader.py]`
- Operational scripts or DAGs: `[scripts/, dags/]`

## Required Change Discipline

- State the grain, keys, date semantics, and output path before changing a dataset.
- Keep raw-source fidelity in the raw layer and move normalization into the clean layer.
- Prefer idempotent processing and backfill-safe scripts.
- Update tests and docs when schemas, dataset names, or public outputs change.

## Common Validation Commands

```bash
# Examples - replace with your project's real commands
pytest tests/processing -v
python scripts/validate_metadata_consistency.py
python -m src.processing.some_transformer
```
