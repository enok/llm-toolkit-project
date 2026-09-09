---
title: DAG and Glue validation checklist
tags: [airflow, mwaa, astro, glue, crawler, data-catalog, etl, validation, spark]
---

# DAG and Glue Validation Checklist

Use this checklist only when the request needs deeper Airflow, MWAA, Astro,
AWS Glue, crawler, Data Catalog, or ETL-pipeline validation.

## Airflow and MWAA

- DAG files parse without import errors in the repo's supported Airflow version.
- Top-level DAG code is cheap and deterministic: no database calls, network
  calls, Airflow Variable lookups, secret fetches, large file reads, or expensive
  catalog scans during scheduler parse.
- `dag_id`, tags, owner, schedule, timezone, `start_date`, `catchup`,
  `max_active_runs`, retries, timeouts, task concurrency, pools, queues, and
  trigger rules are intentional.
- Tasks are atomic and idempotent under retries, backfills, clears, partial
  failures, duplicate upstream events, and late-arriving data.
- Sensors are bounded or deferrable where supported; long waits do not exhaust
  worker slots.
- XCom payloads are small and non-sensitive; large data moves through durable
  stores such as object storage, databases, or catalog tables.
- Provider packages and runtime dependencies are pinned or bounded enough to
  prevent silent scheduler/runtime drift.
- Tests cover DAG import, dependency graph, schedule expectations, task
  parameter construction, and failure-path behavior where practical.

## AWS Glue Jobs

- Glue scripts parse required arguments with `getResolvedOptions`, initialize
  `GlueContext` and `Job`, call `job.commit()`, and avoid hard-coded
  environment-specific secrets or account IDs.
- Job mode is explicit: append, upsert/merge, full refresh, migration, or
  streaming. Retry and rerun behavior does not duplicate, drop, or corrupt data.
- Bookmarks, watermarks, checkpoints, deduplication keys, and late-arrival
  buffers match the source data semantics.
- Spark and Glue version choices match libraries, Data Catalog formats, and
  runtime syntax. Static Spark catalog configuration is passed as job arguments
  when the runtime requires it.
- Worker type/count, timeout, retries, max concurrency, temp/checkpoint paths,
  Spark UI logs, CloudWatch logs, and metrics fit expected data volume.
- Glue connections, subnet/security-group reachability, IAM, object-store and
  KMS grants, Lake Formation, and cross-account assumptions are named and
  least-privilege.
- Data-quality validation checks row counts, nulls on critical columns, schema
  compatibility, duplicate keys, and representative sample rows.

### SQL aggregate limits

- String aggregates with internal size limits fail before any outer truncation
  runs - for example, a warehouse `LISTAGG` raises its byte-limit error (65535
  bytes on several engines) before an outer `left(listagg(...), N)` ever sees
  the result, and one extreme group (thousands of distinct elements) aborts the
  entire statement, losing every other group in the batch. Casting to a
  wider/`max` type does not change the internal limit. Cap rows per group
  **inside** the aggregate: rank elements with a `row_number()` window,
  aggregate `case when rank <= N then element end`, and exploit NULL-skipping
  so `count(*)` still reports the uncapped true cardinality. Choose N from
  element byte size (elements times per-element bytes must stay under both the
  target column width and the aggregate's internal limit), and keep the outer
  truncation as a second guard.

## Crawlers and Data Catalog

- Crawler scope is bounded to the intended object-store/JDBC paths and excludes
  temp, checkpoint, logs, archive, or duplicate directories.
- Classifiers, table prefixes, partition behavior, recrawl policy, and schema
  change policy match downstream consumers.
- Catalog database/table names, partition keys, casing, column types, and
  SerDe/storage descriptors are compatible with the query engines in use
  (Athena, Redshift Spectrum, Lake Formation) and with job code.
- Schema evolution is explicit: additive columns, type changes, deletes, nested
  JSON, and partition changes have validation and rollback notes.

## Validation Evidence

Prefer repo-native and read-only checks:

- `python -m pytest`, DAG import tests, and static lint/type checks.
- `airflow dags list`, `airflow dags test <dag_id> <date>`, `airflow tasks test`,
  `astro dev parse`, `astro dev pytest`, and the CLI's DAG error/warning
  listings when configured.
- Glue script unit tests with mocked `getResolvedOptions`, local Spark tests, or
  AWS Glue Docker/local library tests when the repo supports them.
- Read-only AWS CLI checks such as `aws glue get-job`, `get-crawler`,
  `get-table`, `get-partitions`, CloudWatch log queries, and IAM policy reads.
- IaC checks such as `terraform validate`, `terraform plan`, CDK synth, or
  CloudFormation validation when the pipeline is defined as infrastructure code.

Do not start production DAGs/jobs, clear task instances, run crawlers, update
catalog tables, or change schedules unless the root agent has explicit user
approval for that mutation.
