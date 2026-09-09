---
name: dag-glue-specialist
description: Read-only Airflow DAG, MWAA/Astro, AWS Glue job, crawler, workflow, Data Catalog, and ETL pipeline validation specialist. Use for DAG validation, Airflow implementation or fixes, Glue job/crawler review, ETL PR validation, MWAA/Astro pipeline readiness, schema-drift checks, and data-pipeline runtime safety.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# DAG and Glue Specialist

Use this skill to route Airflow DAG, MWAA/Astro, AWS Glue job, crawler,
workflow, Data Catalog, and ETL pipeline validation through the DAG/Glue
specialist.

Trigger examples:

- "validate this DAG", "fix this Airflow DAG", "DAG PR validation"
- "review this Glue job", "the crawler is failing", "MWAA pipeline"
- "check ETL backfill safety", "validate Airflow/Glue deployment"
- "DAG implementation", "pipeline schedule", "data catalog crawler"

## Workflow

1. Load `workflows/dag-glue-specialist-validation.md`.
2. Invoke or follow `tool-subagents/dag-glue-specialist.md`.
3. Read `references/validation-checklist.md` when the task involves Airflow
   schedules, Glue runtime behavior, crawler/schema drift, or production
   pipeline readiness.
4. Keep root-agent ownership for edits, validation command execution, commits,
   pushes, and user-facing communication; the specialist is read-only.
5. Compose with related specialists only when their evidence lanes are
   relevant: `pr-validator`, `python-best-practices`, `testing`,
   `log-analysis`, `aws-alarm-investigator`, `system-architecture-specialist`,
   `security`, `documentation-reviewer`, and `diagram-creation-specialist`.
   When the pipeline is defined as infrastructure code, route the IaC review
   through `skills/terraform-specialist/SKILL.md`.
6. If the specialist misses a reusable pattern, run
   `workflows/dag-glue-specialist-evolution.md` and review
   `references/external-source-intake.md` for prior external-source notes.

## Safety

- Treat production Airflow, MWAA, Glue, crawler, warehouse, S3, and Data
  Catalog evidence as read-only unless the user explicitly authorizes a
  mutation.
- Do not trigger DAGs, clear task instances, start Glue jobs, run crawlers,
  update catalog tables, or change schedules from the specialist lane.
- Prefer static parse/import checks, CI evidence, local tests, and read-only
  cloud CLI calls before recommending runtime actions.
- Report findings as evidence plus a confidence rating; the root agent decides
  what to change and asks the user before any mutation.

## Related

- `skills/data-pipeline/SKILL.md` — general data-pipeline design guidance
- `skills/data-pipeline-boundaries/SKILL.md` — ownership boundaries between
  pipeline stages
- `skills/terraform-specialist/SKILL.md` — IaC review lane for pipeline
  infrastructure
- `rules/log-analysis-safety.md` — read-only constraints for log evidence
