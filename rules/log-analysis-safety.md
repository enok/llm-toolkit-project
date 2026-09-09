---
trigger: always_on
description: Read-only, bounded, redacted log analysis for CloudWatch and server logs
---

# Log analysis safety

When a task asks for CloudWatch, server, Apache, nginx, Log4j, API Gateway,
Lambda, ETL, or other operational logs:

1. Treat production as read-only unless the user explicitly approves one concrete
   write action with a rollback path.
2. Name the account/profile, region, environment, log groups or files, and time
   window before querying.
3. Prefer aggregation-first queries over raw dumps: counts, buckets, top
   routes, top exception classes, p90/p99 latency, first/last seen, and grouped
   error families.
4. Limit samples. Quote only the minimum fields needed as evidence, and redact
   secrets, tokens, PII, emails, IPs when not essential, session IDs, cookies,
   authorization headers, and full request/response bodies.
5. Do not claim cross-service order from timestamp proximity alone. Require a
   correlation ID, request ID, trace ID, message ID, alarm timestamp, or explicit
   handoff evidence.
6. Separate downstream noise from root cause by looking for the earliest
   upstream failure in the bounded window.
7. If logs are missing, prove whether the blocker is auth, wrong account,
   wrong region, retention, log group naming, ingestion delay, dashboard drift,
   or application telemetry absence.

Use `workflows/log-investigation.md` for end-to-end investigations and
`skills/log-analysis/SKILL.md` for query templates and log-format guidance.
