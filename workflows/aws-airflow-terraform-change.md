---
description: Plan and implement Terraform-managed Apache Airflow on AWS with clear platform boundaries, validation, and deployment inputs
---

# AWS Airflow Terraform Change

Use when introducing or modifying Terraform-managed Apache Airflow on AWS.

## Steps

1. Classify the operating model:
   - Amazon MWAA
   - self-managed Airflow on AWS
   - infrastructure bootstrap only
   - full orchestration migration
2. Confirm what belongs in infrastructure versus code:
   - Terraform or OpenTofu for AWS resources, IAM, networking, storage, and environment settings
   - DAG code for orchestration logic
   - application code or scripts for reusable ETL logic
3. Design the minimum dependency set explicitly:
   - DAG, plugin, and requirements storage
   - execution roles and policies
   - VPC, subnets, security groups, and egress path
   - logging and encryption dependencies
   - optional secret-store integration
4. Decide the Terraform shape before writing resources:
   - simple root configuration extension
   - reusable modules
   - environment separation
5. Keep deployment inputs explicit:
   - Airflow version
   - environment class and scaling
   - network IDs
   - bucket names and prefixes
   - requirements, plugins, and startup-script object paths
   - tags and environment naming
6. Preserve migration safety:
   - keep orchestration changes separate from business logic changes when possible
   - defer deeper execution-code rewrites unless the task requires them
   - keep task naming and documentation traceable to the intended execution stages
7. Add or update support files as needed:
   - `variables.tf`
   - `outputs.tf`
   - `versions.tf`
   - `.gitignore`
   - deployment and operations docs
8. Validate with the narrowest meaningful checks first:
   - `terraform fmt`
   - `terraform validate`
   - targeted application tests for changed execution code
   - `terraform plan` when credentials and environment are available
9. Document:
   - how DAGs are deployed
   - how infrastructure is deployed
   - prerequisites and rollback considerations
   - whether previous orchestration entry points remain supported, wrapped, or deprecated

## Exit Criteria

- Airflow platform boundaries are clear.
- Deployment inputs and outputs are explicit.
- Security, networking, storage, and logging are intentional.
- Validation and operating docs are updated.
