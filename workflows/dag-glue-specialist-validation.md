---
description: Validate Airflow DAGs, MWAA/Astro deployments, AWS Glue jobs, crawlers, Data Catalog changes, and ETL pipeline PRs with the DAG/Glue Specialist
---

# DAG and Glue Specialist Validation

Use this workflow when Airflow DAG, MWAA, Astro, AWS Glue job, Glue crawler,
Data Catalog, ETL, or data-pipeline code needs validation before implementation,
approval, merge, deployment, rerun, or handoff.

## Steps

1. Establish repo, base/head, dirty-tree ownership, scope, and relevant evidence.
2. Identify the pipeline inventory: DAG IDs, Glue job/crawler/workflow names,
   catalog databases/tables, schedules/triggers, connections, IAM roles,
   downstream consumers, and environment/runtime versions.
3. Load only the needed evidence: changed DAG/job/crawler files, unchanged
   dependency paths, Airflow/Glue config, IaC, dependency manifests, tests, CI,
   docs, logs, and runbooks. Use
   `skills/dag-glue-specialist/references/validation-checklist.md` when the task
   needs deeper validation prompts.
4. Invoke or follow `tool-subagents/dag-glue-specialist.md`.
5. Reduce findings locally: accept only evidence-backed, in-scope findings and
   reject generic style advice or unsupported PR-comment agreement.
6. If the user requested fixes, implement the smallest safe change in the root
   agent, preserving unrelated dirty work.
7. Run the narrowest meaningful validation available for the repo and runtime:
   static parse/import checks, unit tests, DAG import tests, `airflow dags test`
   or `astro dev parse`/`astro dev pytest` when configured, Glue script tests,
   IaC plan, read-only cloud checks, and relevant CI evidence.
8. Route adjacent lanes when needed:
   - PR/Jira readiness: `pr-validator`
   - Python/PySpark implementation: `python-best-practices`
   - Pipeline infrastructure as code: `terraform-specialist`
     (`workflows/terraform-specialist-validation.md`)
   - Logs/alarms: `log-analyst` or `aws-alarm-investigator`
   - Architecture/data flow: `system-architecture-specialist`
   - Docs/diagrams/wiki: `documentation-reviewer`, `diagram-creation-specialist`,
     or `confluence-documentation-specialist`
   - Secrets/IAM/data exposure: `security`
9. Keep production pipeline operations read-only: do not trigger DAGs, clear
   task instances, start jobs, run crawlers, or change schedules without
   explicit user authorization for that specific mutation.
10. Report findings, validation, residual risk, related-specialist handoffs, and
    reusable learning.

---

## Evolution

If this specialist misses a recurring issue or is too noisy, run
`workflows/dag-glue-specialist-evolution.md`.
