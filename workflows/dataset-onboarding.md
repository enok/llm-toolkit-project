---
description: Add a new dataset or external feed to a data platform with contracts, validation, and docs
---

# Dataset onboarding workflow

Use when adding a new source dataset, external feed, or research extract to a data platform. This includes APIs, flat files, warehouse exports, and public open-data sources.

## Steps

1. Confirm source access, license, rate limits, refresh cadence, and permitted use.
2. Decide the raw landing contract first: path, filename, partitioning, replayability, and whether the source is immutable, append-only, or snapshot-based.
3. Add or update the metadata or config source of truth before writing downstream transformation logic.
4. Define downstream schema, keys, grain, nullability, and temporal semantics explicitly.
5. Implement ingestion with idempotency, retry behavior, and resumable or backfill-safe operation where feasible.
6. Add focused tests for contract parsing, schema validation, and at least one end-to-end happy path.
7. Update docs or runbooks with dataset purpose, refresh cadence, validation commands, and operational caveats.
8. If localized docs or translation maps exist, sync them in the same change or record intentional drift.
9. Call out cost, storage, and reprocessing impact when the dataset changes orchestration or infrastructure behavior.
