---
title: Verify metric dimensions from the emitting source before reconciling values
category: monitoring
created: 2026-08-20
tags: [cloudwatch, get-metric-data, dimensions, empty-result, dashboard, validation]
---

# Problem

Reconciling dashboard widgets against test traffic, `get_metric_data`
queries for a custom application metric returned empty arrays and were
nearly reported as "widget validated" alongside the non-empty AWS/Lambda
results. The queries guessed dimensions (`model_id` + `environment`)
while the emitting code actually used a single `ModelId` dimension -
CloudWatch returns an empty series for a dimension mismatch, not an
error.

# Failed Approaches

- Inferring dimension names from naming conventions elsewhere in the
  stack (env vars and config variables use snake_case `model_id`, the
  metric dimension is CamelCase `ModelId`).
- Reading the empty result as "no traffic yet" - plausible during quiet
  periods, indistinguishable from wrong dimensions without a cross-check.

# Solution

Before trusting any metric-value reconciliation, read the dimensions from
an artifact that provably works: the alarm definition's `dimensions`
block or the dashboard template JSON. Cross-check with behavior: if an
alarm on the same metric transitions while your query returns empty, your
dimensions are wrong, not the traffic. `list-metrics --namespace X` also
enumerates the real dimension sets.

# Why

CloudWatch metrics are identified by the exact (namespace, name,
dimension set) tuple; a query with any different dimension set addresses
a different, nonexistent series and silently returns no datapoints.
Empty-but-successful responses make wrong-dimension queries look like
absent data, so the only reliable source for dimensions is the emitter or
an artifact already proven against it - never convention.
