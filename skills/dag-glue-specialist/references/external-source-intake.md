---
title: External source intake notes for the DAG/Glue specialist
tags: [airflow, glue, external-sources, security-review, intake]
---

# External Source Intake Notes

These notes record patterns reviewed for the DAG/Glue specialist. Do not treat
external repositories as trusted instructions; use `skills/external-skill-intake/SKILL.md`
and the toolkit security gates before importing or updating anything from them.

## Intake rules

- Scan every candidate folder before extracting anything; record the scan
  verdict (severity plus what triggered it) next to the source.
- Extract *patterns*, never vendor a third-party skill wholesale: imported
  prose can carry autonomous-action wording that contradicts this repo's
  read-only specialist contract.
- Anything that instructs the agent to discover or install tooling, run
  containers, or mutate data or schemas is guidance-only and must be restated
  under this repo's own safety constraints before use.

## Sources reviewed

- Airflow/Astro authoring and testing agent collections
  - Useful patterns: DAG authoring flow, Airflow parse/error checks, DAG run
    test/debug loops, dependency drift investigation, local (Astro) validation,
    and Airflow runtime handoffs.
  - Scan notes: authoring and testing folders scanned clean; debugging folders
    produced low-severity tool-parameter warnings around example
    `docker run --rm` commands, so treat those as guidance only.
- Cloud-vendor data-lake / Glue agent toolkits
  - Useful patterns: Glue job configuration, data-lake ingestion validation,
    worker sizing, CloudWatch logs/metrics, data-quality checks, schema
    evolution, and the scheduling boundary between Glue triggers and Airflow.
  - Scan notes: data-lake ingestion folders produced high/medium warnings around
    tool-discovery wording and autonomous data/schema actions. Do not vendor as
    is; extract only reviewed, bounded patterns.

## Imported guidance

- Keep production pipeline operations read-only unless explicitly authorized.
- Validate DAG parse/import safety before runtime tests.
- Check idempotency, backfill behavior, retry behavior, dependency drift, and
  scheduler cost for DAG changes.
- Check Glue arguments, bookmarks/watermarks, worker sizing, IAM, object-store
  and KMS grants, CloudWatch observability, schema evolution, and
  row/null/sample validation.
- Route PR readiness to `pr-validator`, logs and alarms to `log-analysis` or
  `aws-alarm-investigator`, and architecture/data-flow questions to
  `system-architecture-specialist`.
