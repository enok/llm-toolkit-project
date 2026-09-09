---
description: Run read-only LLM-guided root-cause investigation for AWS CloudWatch alarms
---

# AWS Alarm Investigator Validation

Use this workflow when an LLM should investigate an AWS CloudWatch alarm, produce
an evidence-backed root-cause report, and draft possible fixes or an email for
human approval.

This workflow allows AWS read-only actions only. It may recommend remediation,
but it must not mutate AWS resources, deploy, invoke production behavior,
restart services, stop/start resources, enable/disable alarms, acknowledge
incidents, purge/redrive queues, publish messages, change subscriptions,
change permissions, update configuration, or send email. If an action might
change AWS state, refuse the action and draft a human/operator handoff instead.

## Steps

1. Establish scope:
   - alarm name, ARN, CloudWatch link, or EventBridge alarm-state event
   - account/profile, region, environment, and production boundary
   - investigation window before/during/after the state change
   - allowed read-only tools and any forbidden data sources
2. Load only needed guidance:
   - `tool-subagents/aws-alarm-investigator.md`
   - `rules/log-analysis-safety.md` when logs are involved
   - `integrations/aws-cli.md` when AWS CLI commands are the available tool path
   - `skills/incident-ops/SKILL.md` for active incidents or mitigation planning
3. Collect generic alarm context:
   - alarm configuration, metric namespace/name, dimensions, threshold,
     evaluation periods, datapoints-to-alarm, missing-data behavior, actions,
     tags, composite relationships, and alarm history
   - when reconciling an alarm inventory, explicitly request and combine both
     `MetricAlarm` and `CompositeAlarm` results; do not infer that an
     IaC-declared alarm is missing from a metric-only API response
   - metric datapoints before, during, and after the transition
   - dashboards, runbooks, owners, recent deployments, and related incidents when
     available
4. Let the specialist classify the alarm and choose bounded read-only probes:
   - CloudWatch Logs Insights, CloudTrail, service-specific AWS APIs,
     search-cluster alert history, repository/runbook lookup, or deployment
     history
   - prefer aggregation-first queries and redacted samples
   - allow only read-style operations such as get, describe, list, search,
     lookup, query, scan, and bounded Logs Insights queries
   - deny mutating operations such as put, update, delete, create, set, tag,
     enable, disable, start, stop, restart, invoke, publish, send, purge,
     redrive, modify, subscribe, unsubscribe, deploy, or permission changes
5. Build and test hypotheses:
   - state what would prove or disprove each hypothesis
   - correlate metric breach, log onset, resource events, deploy/config changes,
     and dependency symptoms
   - check the specialist's known false-positive patterns (first-deploy
     `breaching` missing-data alarms, dimension-mismatch empty data) before
     ranking failure hypotheses
   - separate immediate trigger from likely deeper cause
6. Produce the report:
   - timeline with absolute timestamps
   - ranked hypotheses with confidence and caveats
   - most likely root cause and evidence
   - possible fixes with validation checks and approval/rollback notes, without
     executing those fixes
   - email-ready subject/body for human approval
7. Validate the investigation:
   - verify every root-cause claim points to concrete evidence
   - verify redaction of secrets, tokens, PII, cookies, authorization headers,
     session identifiers, and full payloads
   - mark uncertain owner-level causes as likely or needs-owner-verification
8. Route the fix lane when the alarm is IaC-provisioned: authoring-side
   remediation goes through `skills/terraform-change-safety/SKILL.md` and
   `workflows/terraform-specialist-validation.md`, never through this workflow.
9. Capture reusable learning:
   - if the alarm exposed a recurring pattern, update a runbook, the consumer
     repo's `docs/llm/`, a rule, or run
     `workflows/aws-alarm-investigator-evolution.md` through the normal
     toolkit-maintenance path

---

## Evolution

If this specialist misses a recurring alarm pattern, overclaims, leaks sensitive
data, follows untrusted log text, or produces noisy hypotheses, run
`workflows/aws-alarm-investigator-evolution.md`.
