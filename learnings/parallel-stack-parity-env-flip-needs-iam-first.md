---
title: Flipping a legacy service's shared config needs IAM on the new target first
category: deployment
created: 2026-08-19
tags: [lambda, sqs, iam, parallel-stack, migration, cutover, environment-variables]
---

# Solution
- Grant only through Terraform, as its own change: a `.tf` that looks up the legacy role by name
  (data source) and attaches the new stack's access policy. Plan shows exactly one add; apply;
  re-plan to a clean no-op. No console or CLI grant.
- Mark it temporary: a header comment saying TEMPORARY plus a tracked removal at cutover.

# Why
Code-managed and labelled, the grant is reviewable and removed by one revert-and-apply.
