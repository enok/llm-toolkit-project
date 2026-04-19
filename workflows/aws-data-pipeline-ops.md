---
description: Inspect AWS-backed data pipelines with read-first S3, MWAA, Airflow, CloudWatch, and Secrets Manager operations
---

# AWS Data Pipeline Ops Workflow

Use this workflow for operational inspection of AWS-backed data pipelines, especially S3 data lakes, MWAA or Airflow orchestration, CloudWatch logs, and pipeline secrets.

---

## Step 1: Confirm environment targeting

Before running commands, identify:

- AWS profile or credential source
- Region
- Environment name
- Bucket names and prefixes
- MWAA environment, Airflow DAG, or job identifiers

Do not guess production resource names.

---

## Step 2: Start with read-only inspection

Prefer read-only commands first:

```bash
aws sts get-caller-identity
aws s3 ls
aws s3 ls s3://<bucket>/<prefix>/
aws mwaa get-environment --name <environment> --region <region>
aws logs describe-log-groups --query "logGroups[].logGroupName"
aws logs tail <log-group> --since 1h
aws secretsmanager describe-secret --secret-id <secret-name>
```

Reduce output with `--query`, `--output json`, or precise prefixes so results stay reviewable.

---

## Step 3: Inspect the specific failure surface

Choose the right inspection path:

- **Missing data**: S3 prefixes, object timestamps, partition layout
- **Failed orchestration**: MWAA environment health, Airflow DAG run state, scheduler or task logs
- **Auth or config issues**: caller identity, profiles, region mismatch, missing secret or env name
- **Slow or partial runs**: CloudWatch logs, task retries, throttling, pagination, checkpoint or metadata behavior

---

## Step 4: Correlate code and cloud state

Match what the cloud shows against repo truth:

- Config files and schema definitions
- DAG IDs and task names
- Expected bucket and prefix layout
- Time windows, backfill logic, and partitioning
- Recent code or docs that changed the contract

---

## Step 5: Escalate writes deliberately

If you need a non-read-only action such as rerun, upload, delete, or mutate a resource:

- State the exact command
- State the target resource
- State the expected outcome
- Get explicit user approval before execution

Default posture is inspect first, mutate second.
