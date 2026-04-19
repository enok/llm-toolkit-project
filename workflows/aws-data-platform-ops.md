---
description: Inspect or operate AWS-backed data pipelines with explicit scope, verification, and evidence
---

# AWS Data Platform Ops Workflow

Use when a task requires AWS CLI inspection, S3 verification, MWAA environment checks, pipeline triggers, or infrastructure-adjacent operational work.

## Steps

1. Confirm operating context:
   - AWS profile
   - region
   - account or environment
   - bucket and target prefix
   - MWAA environment name if applicable
2. Classify the action:
   - inspect only
   - pipeline execution
   - data validation or audit
   - infrastructure apply or teardown
3. Prefer narrow read commands first such as list, head, or describe.
4. Use repo scripts when available for repeatable operations.
5. Before any write or trigger action, state:
   - what will be affected
   - what success looks like
   - what evidence will be captured
6. After the operation, verify the result using the destination system rather than trusting command success alone.
7. If the operation is likely to repeat, update or create a runbook.

## Exit Criteria

- Scope and environment were verified.
- Result was checked in AWS or the produced artifact.
- Reusable operational knowledge was captured.
