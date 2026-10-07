---
description: Change an existing Bronze, Silver, Gold, or warehouse-style data pipeline safely
---

# Data pipeline change workflow

Use when modifying ingestion, normalization, aggregation, storage layout, feature generation, or pipeline orchestration in an existing data platform.

## Steps

1. Classify the scope first: ingestion, schema, transformation, feature logic, orchestration, infrastructure, docs, or mixed.
2. Read the authoritative contract files before changing code: metadata, schemas, translation maps, job config, or storage conventions.
3. Trace the impacted path across config, pipeline code, scripts, tests, notebooks, and docs before editing.
4. Check whether the change alters grain, keys, partitions, filenames, S3 or warehouse paths, cache behavior, or downstream expectations.
5. Decide whether a backfill, reprocess, cache reset, or migration note is required and document that decision.
6. Implement the smallest safe change that preserves idempotency and observability.
7. Run the narrowest meaningful validation first, then broader tests if the change crosses layers.
8. Update docs, runbooks, and localized counterparts when behavior, commands, or outputs change.
9. Summarize operational impact clearly: what changed, what must be rerun, and what downstream readers should expect.

## Known pitfalls

- When a Gold (or other consumed) dataset changes schema (for example a column rename), update every notebook that reads it, English and pt-BR pairs alike. Also search for dynamically built names (for example `f'{col}_norm'` over a `raw_features` list), which a grep for explicit names misses, and check the pt-BR translation map for renamed columns and update it. See learnings/gold-schema-drift-breaks-notebooks.md.
