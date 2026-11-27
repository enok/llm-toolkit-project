---
description: Project-local companion to aws-airflow-terraform-change for the data-platform repo (Airflow DAGs plus Terraform roots)
---

# AWS Airflow Terraform Change Workflow

Use this repo-local workflow together with the shared workflow in `workflows/aws-airflow-terraform-change.md`.

## Repository-Specific Deltas

- Treat Terraform in `infra/` as the source of truth for AWS infrastructure in this repo.
- Treat the three `scripts/0N_*.sh` stage scripts as the source of truth for implemented ETL entry points unless real DAG code is added.
- Do not assume Airflow orchestration already exists. Confirm whether the change is infrastructure-only, DAG introduction, ETL task migration from shell orchestration into Airflow, or documentation/operating-model guidance only.
- Preserve current S3 naming and dataset contract assumptions unless the change is an intentional migration.

## Repository-Specific Steps

1. Read the current repository boundaries before designing infrastructure:
   - `infra/`
   - `scripts/01_bronze_ingestion.sh`
   - `scripts/02_silver_transformation.sh`
   - `scripts/03_gold_transformation.sh`
2. Decide whether the first migration step should wrap the existing shell scripts rather than rewrite ETL logic.
3. Keep Bronze, Silver, and Gold responsibilities traceable in DAG names, task names, and docs.
4. If the Airflow surface remains small, extending the current `infra/` root may be acceptable. If it becomes non-trivial, split into modules and explicit environment inputs.
5. Update repo artifacts that this migration affects:
   - `config/` contracts when behavior changes
   - `tests/`
   - `docs/`
   - `.gitignore` if local Terraform artifacts need coverage
6. Document whether shell scripts remain canonical, become task wrappers, or are deprecated.
