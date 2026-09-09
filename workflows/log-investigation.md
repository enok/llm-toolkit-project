---
description: Read-only operational log investigation across CloudWatch, server, application, and access logs
---

# Log investigation workflow

Use this workflow when the user asks to analyze operational logs, investigate an
alarm from logs, compare failing and healthy windows, or understand errors from
CloudWatch, server logs, Log4j/SLF4J, Apache, nginx, API Gateway, Lambda, Glue,
Firehose, or similar systems.

## Required posture

- Apply `rules/log-analysis-safety.md`.
- Use `skills/log-analysis/SKILL.md` for query patterns and interpretation.
- For active incidents, pair with `skills/incident-ops/SKILL.md`.
- When the entry point is a fired alarm rather than a log question, run
  `workflows/aws-alarm-investigator-validation.md` and use this workflow as its
  log-evidence lane.
- If independent log families or services exist, delegate a read-only lane to
  `tool-subagents/log-analyst.md` and reduce its findings before reporting.

## Steps

1. **Frame the question**
   - environment and production/read-only boundary
   - account/profile, region, service, tenant, route, job, alarm, or request ID
   - exact time window and timezone
   - expected normal behavior and known deploy or config-change timestamps

2. **Map log surfaces**
   - CloudWatch log groups, streams, alarms, dashboards, and metric filters
   - API Gateway, ALB, Apache, nginx, Elastic Beanstalk, or host access/error
     logs
   - application logs such as Log4j/SLF4J, Logback, pino, winston, or Python
   - Lambda `REPORT`, Glue, Firehose, scheduler, queue, or batch logs

3. **Query by reduction first**
   - counts by time bucket
   - top routes/statuses/exception classes/job names
   - p90/p99 latency and duration outliers
   - first seen / last seen per grouped signal
   - known-good versus failing-window comparison when available

4. **Sample only after grouping**
   - inspect a small sample for each grouped finding
   - redact sensitive values before reporting
   - verify parsed fields against the actual log format before using them as
     evidence

5. **Correlate carefully**
   - join with request IDs, correlation IDs, trace IDs, Lambda request IDs,
     message IDs, alarm timestamps, deploy timestamps, or scheduler run IDs
   - avoid cross-service causal claims without an explicit join signal

6. **Report the result**
   - confirmed facts
   - likely cause and confidence
   - exact read-only commands or query shapes used
   - blocked or missing evidence
   - next read-only checks, or the smallest approved remediation path

## Validation

- Confirm every reported conclusion has a count, grouped signal, or sampled log
  line behind it.
- Confirm raw sensitive values were not pasted into the report.
- Confirm no secrets, tokens, PII, cookies, authorization headers, session
  identifiers, or full payloads reached the report or any generated document.
- For toolkit changes, run the relevant index checks and the mandatory security
  gate (`workflows/security-check-required.md`).
