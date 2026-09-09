---
title: CloudWatch Logs Insights read-only query patterns
tags: [cloudwatch, logs-insights, aws-cli, read-only, queries, lambda, api-gateway]
---

# CloudWatch Logs Insights

Use this reference for read-only AWS log investigations. It is written for
CloudWatch Logs Insights because aggregation usually beats raw event scans for
large production log groups.

## Read-only safety

Allowed commands for investigation:

- `aws sts get-caller-identity`
- `aws logs describe-log-groups`
- `aws logs describe-log-streams`
- `aws logs start-query`
- `aws logs get-query-results`
- `aws cloudwatch describe-alarms`
- `aws cloudwatch describe-alarm-history`
- `aws cloudwatch list-dashboards`
- `aws cloudwatch get-dashboard`
- `aws cloudwatch list-metrics`
- `aws cloudwatch get-metric-data`
- `aws lambda list-functions`
- `aws lambda get-function-configuration`
- `aws ecs list-clusters`, `aws ecs list-services`, `aws ecs describe-services`

Avoid in production unless explicitly approved:

- commands that change alarms, dashboards, log groups, subscriptions, metric
  filters, functions, services, schedules, or deployments
- `aws logs tail --follow` for long-running watches
- bulk raw event dumps without a tight time window and redaction plan

## AWS CLI shape

PowerShell:

```powershell
$profile = "<profile>"
$region = "<region>"
$start = [DateTimeOffset]::Parse("<start-iso>").ToUnixTimeSeconds()
$end = [DateTimeOffset]::Parse("<end-iso>").ToUnixTimeSeconds()
$logGroup = "<log-group>"
$query = @'
fields @timestamp, @message
| sort @timestamp desc
| limit 50
'@

$qid = aws logs start-query `
  --profile $profile --region $region `
  --log-group-name $logGroup `
  --start-time $start --end-time $end `
  --query-string $query `
  --query queryId --output text

aws logs get-query-results `
  --profile $profile --region $region `
  --query-id $qid --output json
```

Bash:

```bash
profile="<profile>"
region="<region>"
start="$(date -u -d '<start-iso>' +%s)"
end="$(date -u -d '<end-iso>' +%s)"
log_group="<log-group>"

query='fields @timestamp, @message
| sort @timestamp desc
| limit 50'

qid="$(aws logs start-query \
  --profile "$profile" --region "$region" \
  --log-group-name "$log_group" \
  --start-time "$start" --end-time "$end" \
  --query-string "$query" \
  --query queryId --output text)"

aws logs get-query-results \
  --profile "$profile" --region "$region" \
  --query-id "$qid" --output json
```

## Query patterns

Recent errors:

```sql
fields @timestamp, @log, @logStream, @message
| filter @message like /(?i)(error|exception|failed|timeout|throttl)/
| sort @timestamp desc
| limit 100
```

Error counts by time bucket:

```sql
fields @timestamp, @message
| filter @message like /(?i)(error|exception|failed|timeout|throttl)/
| stats count(*) as errors by bin(5m)
| sort bin(5m) asc
```

Exception class grouping:

```sql
fields @timestamp, @message
| filter @message like /Exception|Error/
| parse @message /(?<exception>[A-Za-z0-9_.$]+(?:Exception|Error))/
| stats count(*) as count, min(@timestamp) as firstSeen, max(@timestamp) as lastSeen by exception
| sort count desc
| limit 50
```

Correlation ID trace:

```sql
fields @timestamp, @log, @logStream, @message
| filter @message like /<correlation-id-or-request-id>/
| sort @timestamp asc
| limit 200
```

Lambda duration and memory:

```sql
filter @type = "REPORT"
| stats count(*) as invocations,
    avg(@duration) as avgMs,
    pct(@duration, 90) as p90Ms,
    pct(@duration, 99) as p99Ms,
    max(@duration) as maxMs,
    max(@maxMemoryUsed / 1024 / 1024) as maxMemoryMb
  by bin(5m)
| sort bin(5m) asc
```

Lambda cold starts:

```sql
filter @type = "REPORT"
| stats
    count(*) as invocations,
    sum(strcontains(@message, "Init Duration")) as coldStarts,
    100 * sum(strcontains(@message, "Init Duration")) / count(*) as coldStartPct
  by bin(5m)
| sort bin(5m) asc
```

API Gateway access logs when JSON fields are present:

```sql
fields @timestamp, httpMethod, path, status, integrationStatus, responseLatency, integrationLatency, requestId
| stats count(*) as requests,
    pct(responseLatency, 90) as p90ResponseMs,
    pct(responseLatency, 99) as p99ResponseMs,
    sum(if(status >= 500, 1, 0)) as serverErrors,
    sum(if(status >= 400 and status < 500, 1, 0)) as clientErrors
  by httpMethod, path
| sort serverErrors desc, p99ResponseMs desc
| limit 50
```

Access logs when a single text line must be parsed:

```sql
fields @timestamp, @message
| parse @message /(?<method>GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS) (?<path>[^ ]+) [^"]*" (?<status>\d{3}) [^ ]+ [^ ]+ (?<durationMs>\d+)/
| stats count(*) as requests,
    pct(durationMs, 90) as p90Ms,
    pct(durationMs, 99) as p99Ms
  by method, path, status
| sort requests desc
| limit 50
```

Ingestion or field-sparsity health checks:

```sql
fields @timestamp, @message
| filter @message like /(?i)(0 records|null|missing|empty|schema|field|column|delivery|firehose|redshift|glue)/
| stats count(*) as hits by bin(5m)
| sort bin(5m) asc
```

## Interpretation rules

- If `filter-log-events` is slow or noisy, pivot to Logs Insights aggregation.
- If an alarm is based on a log metric filter, inspect both the source log group
  and the alarm history.
- If a dashboard is blank, compare current log groups, metric namespaces, and
  dimensions against dashboard widgets before assuming telemetry stopped.
- If logs are JSON, use field names directly. If they are text, `parse` the
  smallest reliable fields and validate with a small sample.
- If a query finds many downstream failures, look for the earliest upstream
  exception or timeout in the same window.
