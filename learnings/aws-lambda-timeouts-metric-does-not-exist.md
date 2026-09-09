---
title: AWS/Lambda publishes no Timeouts metric — alarms on it are permanently silent
category: deployment
created: 2026-08-19
tags: [cloudwatch, lambda, timeouts, phantom-metric, metric-filter, alarm, dashboard]
---

# Problem

A CloudWatch alarm and two dashboard widgets referenced the metric
`AWS/Lambda Timeouts` (dimension `FunctionName=...`). `terraform validate`,
`plan`, and `apply` all succeeded, the alarm read back `OK`, and the widgets
rendered — but the alarm could never fire and the widget series stayed
permanently empty, because `AWS/Lambda` publishes no metric named `Timeouts`.
The defect survived a CI job template, a legacy hand-made alarm, and the
Terraform migration that faithfully mirrored both.

# Failed Approaches

- Trusting IaC signals: `terraform validate`/`plan`/`apply` and
  `describe-alarms` all pass for a nonexistent metric. CloudWatch accepts any
  namespace/metric string, and alarms on missing data simply sit
  `OK`/`INSUFFICIENT_DATA`.
- Trusting inherited configuration: the metric name came from a long-lived
  template, so every migration copied the defect without questioning it.
- Trying to keep the `FunctionName` dimension on the replacement metric: log
  metric filters can only derive dimensions from parsed JSON or space-delimited
  fields, and the runtime's timeout line is plain text that does not contain the
  function name.

# Solution

Prove a metric exists before alarming on it: run
`aws cloudwatch get-metric-data` over a window where sibling metrics
(`Invocations`, `Errors`, `Duration`) return datapoints — an empty result for
the target metric is the defect signal.

For Lambda timeouts specifically, create a CloudWatch Logs metric filter on the
function's log group with the pattern `"Task timed out"`, emitting a custom
metric (e.g. `<AppNamespace>/Timeouts`, value 1, unit Count), and point the alarm
and widgets at it. Make it **dimensionless** — the per-function log group
already scopes it. Set `default_value = 0` so periods with log traffic emit a
zero datapoint, keeping widget series dense and `treat_missing_data =
notBreaching` safe. When a filter is unwanted, alarm on `Duration` Maximum >=
the configured function timeout as a proxy.

# Why

CloudWatch namespaces are not schemas: any alarm or widget metric reference is
accepted and silently returns no data if the metric is never published. The real
`AWS/Lambda` metric set is Invocations/Errors/Duration/Throttles and friends —
timeouts appear only as an Error plus the "Task timed out" log line, so a
"Timeouts" alarm must be backed by a log-derived custom metric.
