---
title: Server and application log formats
tags: [apache, nginx, api-gateway, elastic-beanstalk, log4j, slf4j, lambda, glue, firehose, parsing]
---

# Server and Application Log Formats

Use this reference when the evidence is local server logs, CloudWatch-ingested
server logs, API access logs, or application logs.

## Apache and nginx access logs

Common fields to extract:

- timestamp
- client IP or forwarded IP
- HTTP method
- route/path
- status code
- response bytes
- referer and user agent when useful
- upstream status
- upstream or request duration

Useful reductions:

- request count by route and status family
- top 4xx/5xx routes
- p90/p99 latency by route
- route hit count during the incident window versus a known-good window
- user-agent or IP outliers when abuse or bot traffic is plausible

Do not overfit to one Apache format. Confirm the actual field order before
claiming latency or status. Some Apache formats put request duration in
microseconds, others omit it entirely.

## API Gateway access logs

Prefer JSON access logs when available. Useful fields include:

- `requestId` or extended request ID
- route/resource path and method
- `status` and `integrationStatus`
- `responseLatency` and `integrationLatency`
- source IP, user agent, domain, stage, and authorizer outcome

Separate API Gateway failures from backend failures:

- 4xx with no integration error often means caller/auth/request validation.
- 5xx or high integration latency points toward backend, Lambda, network, or
  integration timeout.
- High response latency with low integration latency can point to gateway,
  authorizer, mapping, or payload size behavior.

## Elastic Beanstalk and host logs

Common CloudWatch log group families:

- `/var/log/nginx/access.log`
- `/var/log/nginx/error.log`
- `/var/log/httpd/access_log`
- `/var/log/httpd/error_log`
- application logs such as `application.log`, `application_error.log`, or
  framework-specific process logs

Analyze in layers:

1. access log status and latency by route
2. proxy error log for upstream resets, 502/504, socket, timeout, or disk issues
3. application error log for exception classes and request IDs
4. deployment or platform logs for restarts, health agent transitions, or
   config changes

## Log4j, SLF4J, and Java logs

Look for:

- exception class and root cause line
- request/correlation ID from MDC
- thread name, pool name, or async executor
- service method, route, tenant, message ID, or job name
- log level transitions around the failing window
- repeated stack traces that are downstream symptoms

When logs include stack traces, group by exception class and the first
application frame rather than treating every stack line as a separate error.

Example reduction targets:

- top exception classes
- first seen / last seen per class
- count by service method or route
- count by request ID or message ID
- before/after deploy comparison

## Lambda logs

Use application log lines for business errors and `REPORT` lines for runtime
performance:

- `@duration`, `@billedDuration`, `@maxMemoryUsed`, `@memorySize`
- cold-start marker: `Init Duration`
- request ID joins between application logs and `REPORT` lines

Do not infer business failure from slow duration alone. Cross-check application
error lines, retries, DLQs, destination failures, or alarm history.

## Glue, Firehose, and ingestion logs

For ETL or streaming investigations, separate:

- source record volume
- delivery failures or retries
- transformation/schema errors
- destination write failures
- field sparsity or null-rate checks
- scheduler/job success metrics

Field sparsity alarms require different proof than delivery outage alarms.
Confirm whether records arrived and whether the specific field/column was
non-null or transformed as expected.

## Evidence quality checklist

- Time window is explicit and in one timezone.
- Query scope names account/profile, region, and log groups.
- Counts are shown before raw samples.
- At least one sample log line supports each grouped conclusion.
- Cross-service conclusions use a join key, not only timestamp proximity.
- Sensitive values are redacted or summarized.
