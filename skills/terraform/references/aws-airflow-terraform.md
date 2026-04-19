---
trigger: model_decision
description: Use when provisioning or changing AWS-hosted Apache Airflow with Terraform or OpenTofu
---

# AWS Airflow Terraform

Use this rule when a task involves provisioning or evolving AWS-hosted Apache Airflow through Terraform or OpenTofu.

## Scope The Decision First

- Confirm whether the task is:
  - infrastructure-only
  - DAG introduction
  - ETL migration into Airflow
  - operational documentation only
- Keep platform provisioning concerns separate from pipeline business logic.

## Service Choice

- Choose the AWS Airflow hosting model explicitly:
  - Amazon MWAA
  - self-managed Airflow on ECS, EKS, or EC2
- Document the constraint that drives the choice, such as executor needs, plugin requirements, network model, cost envelope, or operational control.

## Terraform Responsibilities

- Use Terraform or OpenTofu for:
  - Airflow environment resources
  - DAG, plugin, requirements, and startup-script storage
  - IAM roles and policies
  - networking and security groups
  - logging, encryption, and observability dependencies
- Do not put business logic or credentials into Terraform.

## Code Boundaries

- DAG Python belongs in an Airflow code location such as `dags/`.
- Reusable pipeline logic belongs in application code or scripts, not copied into Terraform templates.
- Runtime secrets and connection material belong in managed secret stores or runtime configuration systems, not in source-controlled IaC.

## Terraform Structure

- Keep environment-specific values in variables, tfvars, or environment folders instead of hardcoding account, region, subnet, bucket, or role details.
- Introduce `versions.tf`, `outputs.tf`, and provider constraints when the infrastructure surface is more than trivial.
- Prefer explicit outputs for environment names, ARNs, bucket or prefix locations, log destinations, and network identifiers that operators or automation will need.
- Do not commit local state files, plan files, generated secrets, or credential artifacts.

## Security And Operations

- Apply least-privilege IAM to Airflow execution roles and supporting AWS integrations.
- Prefer private networking with explicit egress assumptions.
- Prefer encryption-at-rest and encryption-in-transit defaults for buckets, logs, and secret stores.
- Make logging and observability explicit enough to diagnose DAG parse failures, scheduler failures, and task failures.

## Change Discipline

- Preserve output contracts while moving scheduling or infrastructure into Airflow.
- Document how DAG deployment, Terraform deployment, and runtime operations fit together.
