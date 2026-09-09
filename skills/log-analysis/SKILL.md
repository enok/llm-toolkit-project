---
name: log-analysis
description: Analyze CloudWatch Logs, server logs, API Gateway/ALB access logs, Apache/nginx logs, Log4j/SLF4J logs, Lambda REPORT lines, Glue/Firehose/ingestion logs, and other operational log streams. Use for read-only production log investigation, incident evidence gathering, error/latency trend analysis, correlation-id tracing, and root-cause summaries built from logs.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Log Analysis

Use this skill when the task is to understand behavior from logs rather than to
change code or infrastructure.

## Default posture

- In production, stay read-only unless the user explicitly approves a concrete
  write action.
- Prefer bounded queries over unbounded tails. Always set a time window, limit,
  account/profile, region, and log group scope.
- Do not paste secrets, tokens, full PII, or large raw payloads into the chat.
  Summarize patterns and quote only the minimum fields needed as evidence.
- Treat log order as approximate across services. Require correlation IDs,
  request IDs, trace IDs, message IDs, or explicit handoff timestamps before
  claiming cross-service ordering.
- Separate symptom volume from root cause. A frequent error can be downstream
  noise from a rarer upstream failure.

## Workflow

1. **Frame the investigation**
   - incident or question
   - environment and account/profile
   - region
   - time window and timezone
   - expected normal behavior
   - known request IDs, trace IDs, users, routes, jobs, alarms, or deploy times

2. **Map log surfaces**
   - CloudWatch log groups and alarms
   - API Gateway, ALB, Apache, nginx, or Elastic Beanstalk access/error logs
   - application logs such as Log4j/SLF4J, Logback, pino, winston, or Python
   - Lambda `REPORT` lines
   - ETL, Glue, Firehose, queue, scheduler, or batch-job logs
   - dashboards and metrics that validate or contradict log evidence

3. **Choose the narrowest query lane**
   - CloudWatch Logs Insights for aggregation and large log groups.
   - Access-log aggregation for route/status/latency/hit-count questions.
   - Exception-class and stack-root grouping for Log4j/SLF4J logs.
   - Lambda report analysis for duration, memory, cold starts, and billed time.
   - Ingestion-pipeline analysis for delivery delay, transformation failure, and
     field sparsity.

4. **Reduce before concluding**
   - Count first, then sample.
   - Group by service, route, status, exception class, job name, function name,
     stream, or correlation ID.
   - Compare the failing window with a known-good window when possible.
   - Cross-check alarms/metrics with logs before declaring causality.

5. **Report evidence**
   - exact time window and timezone
   - commands or query shape used
   - confirmed facts
   - likely cause with confidence
   - unknowns and blocked signals
   - next read-only checks or approved remediation path

## References

- `references/cloudwatch-logs-insights.md` - Read-only AWS CLI workflow and
  CloudWatch Logs Insights query templates.
- `references/server-log-formats.md` - Apache, nginx, API Gateway, Elastic
  Beanstalk, and application-log parsing patterns.
- `references/external-patterns-reviewed.md` - Public repositories reviewed and
  the generic patterns adapted.

## Related workflow, rule, and subagent

- `workflows/log-investigation.md` - End-to-end operational log investigation.
- `rules/log-analysis-safety.md` - Read-only production, bounded query, and
  redaction constraints.
- `tool-subagents/log-analyst.md` - Parallel read-only evidence-reduction lane
  for multi-service investigations.

## Related skills

- `skills/incident-ops/SKILL.md` - Use when log analysis is part of active
  triage, mitigation, or communications.
- `skills/aws-alarm-investigator/SKILL.md` - Use when the entry point is a
  CloudWatch alarm rather than a log question.
- `skills/jmeter-performance-testing/SKILL.md` - Use for load-test log and
  metric analysis.
- `skills/java-best-practices/SKILL.md` - Use when a Java/Log4j/SLF4J code
  change is needed after diagnosis.
- `skills/python-best-practices/SKILL.md` and `skills/js-ts-best-practices/SKILL.md` -
  Use when log format or application logging changes are needed in those stacks.
- `skills/security/SKILL.md` - Use when logs may expose secrets, PII, or abuse
  evidence.
