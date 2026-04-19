---
trigger: model_decision
description: Safety and verification for AWS-backed data platform operations such as S3, orchestration, and CLI-based pipeline work
---

# AWS Data Platform Operations

Use this rule when a task involves AWS CLI commands, S3 objects, orchestration services, managed compute or analytics services, or infrastructure-backed pipeline operations.

## Verify Context First

- Confirm the AWS profile, region, account, bucket, environment, and target prefix before running write operations.
- Distinguish between inspect-only commands and commands that trigger pipelines, create objects, or alter infrastructure.
- Prefer repo scripts or documented entry points when they exist instead of ad hoc command sequences.

## Read Before Write

- Use list, head, or describe commands first when checking environment state.
- Narrow writes to explicit prefixes or resources instead of broad bucket-level actions.
- Do not assume the local cache reflects S3 truth. Verify current object presence and metadata when it matters.

## Operational Discipline

- Make expensive, long-running, or potentially destructive actions explicit before running them.
- For DAG or pipeline runs, note prerequisites, expected downstream writes, and how success will be verified.
- Preserve logs, report paths, or evidence links when the operation matters for reproducibility or audit.

## Follow-Through

- After an operational task, capture the result in a committed runbook or status doc if the workflow is likely to repeat.
- If a manual operational pattern keeps recurring, turn it into a script or documented workflow.
