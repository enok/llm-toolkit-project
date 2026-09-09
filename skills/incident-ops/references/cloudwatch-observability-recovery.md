---
title: CloudWatch observability recovery
tags: [incident, observability, cloudwatch, metrics, alarms, dashboards, logs]
---

# CloudWatch Observability Recovery

Use this checklist when a service is healthy by load balancer or host checks but
CloudWatch dashboards, application metrics, or alarms have gone blank or moved
to `INSUFFICIENT_DATA`.

For root-cause work that depends on raw or aggregated log evidence, load
`skills/log-analysis/SKILL.md` and prefer bounded CloudWatch Logs Insights
queries before falling back to raw event scans.

## Triage order

1. Confirm user impact and request traffic separately from dashboard health.
2. Identify the metric sources involved:
   - infrastructure metrics such as ALB, target group, EC2, ECS, or Lambda
   - log metric filters
   - application reporters such as Dropwizard, Micrometer, or custom emitters
   - JVM or process metrics
3. Check startup logs for the application reporter configuration, including
   environment name, namespace, metric stack/dimension, and enabled flag.
4. Query CloudWatch for recently active metrics with the exact namespace and
   dimensions that dashboards and alarms expect.
5. Compare dashboard widgets and alarms with the current runtime resources:
   instance ids, target groups, log groups, namespaces, metric names, and
   dimensions.
6. Separate missing data from stale references. A dashboard can be blank because
   the app stopped publishing metrics, because widgets point at old dimensions,
   or because alarms still reference retired resources.

## Metric catalog expectations

For runbooks, release notes, or PR docs that add or depend on CloudWatch
metrics, include a compact catalog with:

| Column | Purpose |
|---|---|
| Service | Emitter or owning application |
| Metric name | Exact exported or CloudWatch name |
| Type | Count, timer, gauge, rate, or alarm input |
| Dimensions/tags | Stack, environment, flow, cache, outcome, or similar |
| Trigger | What increments or records the metric |
| Healthy signal | Expected value or range during known-good traffic |
| Troubleshooting use | What to inspect when the metric changes |
| Source | Code, metric filter, dashboard, or CloudWatch query evidence |

Record dimension quirks when environment labels differ between services or
dashboards.

## Read-only evidence commands

Bash / Git Bash:

```bash
AWS_PROFILE_NAME='<aws-profile>'
REGION='<region>'
LOG_GROUP='<service-log-group>'

aws logs start-query --profile "$AWS_PROFILE_NAME" --region "$REGION" \
  --log-group-name "$LOG_GROUP" \
  --start-time <epoch-start> --end-time <epoch-end> \
  --query-string 'fields @timestamp, @message | filter @message like /metrics|reporter|registry|CloudWatch/ | sort @timestamp desc | limit 20'

aws cloudwatch list-metrics --profile "$AWS_PROFILE_NAME" --region "$REGION" \
  --namespace <namespace> \
  --dimensions Name=<dimension-name>,Value=<dimension-value> \
  --recently-active PT3H
```

PowerShell:

```powershell
$awsProfile = '<aws-profile>'
$region = '<region>'
$logGroup = '<service-log-group>'

aws logs start-query --profile $awsProfile --region $region `
  --log-group-name $logGroup `
  --start-time <epoch-start> --end-time <epoch-end> `
  --query-string 'fields @timestamp, @message | filter @message like /metrics|reporter|registry|CloudWatch/ | sort @timestamp desc | limit 20'

aws cloudwatch list-metrics --profile $awsProfile --region $region `
  --namespace <namespace> `
  --dimensions Name=<dimension-name>,Value=<dimension-value> `
  --recently-active PT3H
```

Keep the first pass read-only. Do not delete alarms, change filters, edit
dashboards, restart services, or redeploy until the operator has approved a
specific mitigation and rollback path.

## Decision points

- If traffic and infrastructure health are good but application metrics are
  missing, inspect startup config, packaged artifacts, and external property
  resolution before editing dashboards.
- If log-filter metrics emit zeroes while application metrics are absent, treat
  them as different pipelines. A healthy log filter does not prove an in-process
  reporter is enabled.
- If multiple stacks or environments share an account, query by namespace and
  exact dimensions. Do not infer the expected stack from account-level metric
  listings alone.
- If alarms reference stopped or retired resources, verify replacement resources
  first, then update or remove stale alarms through the approved change path.

## Cross-service log ordering

CloudWatch cannot globally order a distributed async request across log groups,
streams, hosts, function instances, and async appenders. Treat raw timestamp
sort order as display evidence, not business-flow truth.

When reconstructing a multi-service flow, require a propagated trace envelope:

| Field | Purpose |
|---|---|
| `traceId` | Unique request-flow identifier across services |
| `step` / `stepOrder` | Stable event name and sortable sequence within one trace |
| `service` / `env` | Service and environment disambiguation |
| `requestStartEpochMs` | Original entry-point start time |
| `serviceReceiveEpochMs` / `servicePublishEpochMs` | Queue or handoff gap analysis |
| `durationMs` | Service-local work duration |
| message ids | Join publisher and consumer logs for queues, SNS, or streams |

Prefer service-local `durationMs` for bottleneck analysis. Use propagated epoch
fields only for handoff or delivery gaps. OpenTelemetry or AWS X-Ray is the
longer-term form of the same contract.

## Recovery verification

- Startup logs show the intended environment, metric namespace, dimensions, and
  reporter enabled state.
- `list-metrics --recently-active` returns the expected application and runtime
  metrics for the active dimensions.
- Dashboards reference current resources and log groups.
- Alarms have moved out of `INSUFFICIENT_DATA` for the right reason, not because
  thresholds or missing-data behavior were weakened.
- Any cleanup of stale alarms, filters, or widgets is documented with before and
  after evidence.
