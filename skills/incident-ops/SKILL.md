---
name: incident-ops
description: >
    Support incident triage, mitigation, and communication. Trigger when the user asks for
    incident handling, blast-radius analysis, mitigation sequencing, comms cadence,
    observability/dashboard recovery, or post-incident follow-up planning.
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Incident Ops

Use this skill for active operational response and structured mitigation.

## When to Apply

- Active production incident or degraded service
- Blast-radius analysis for a known issue
- Mitigation sequencing and communication planning
- Post-incident follow-up and runbook creation

## Workflow

1. **Establish current impact:**
   - customers or tenants affected
   - user-visible symptoms
   - time window
   - severity
2. **Build the initial hypothesis list** from the most recent changes, infrastructure events, and known hotspots.
3. **Drive mitigation before explanation** when customers are impacted — restore service first, root-cause later.
4. **Track throughout:**
   - current hypothesis
   - evidence gathered
   - mitigation in progress
   - next update time
5. **When the system is stable**, convert the outcome into a runbook or follow-up checklist using **runbook-authoring**.
6. **For observability gaps** — service healthy but dashboards, metrics, or alarms blank or
   stuck in `INSUFFICIENT_DATA` — use `references/cloudwatch-observability-recovery.md`
   to separate health, logs, application metrics, alarms, and dashboard drift.
7. **For log-root-cause analysis**, use `workflows/log-investigation.md` and
   **log-analysis** to run read-only, bounded log-query investigations
   (CloudWatch Logs Insights, server logs, Log4j, Apache/nginx, API gateway,
   serverless function, or streaming-job logs) before proposing changes.

## Output

Return:
- current impact summary
- active hypotheses with supporting evidence
- mitigation plan (ordered by impact reduction)
- communication/update cadence
- follow-up items (root cause investigation, preventive measures)

## Non-Goals

- Do not skip mitigation to pursue root cause while users are impacted.
- Do not make destructive changes without explicit approval and a rollback plan.

## Related Skills

- **runbook-authoring** — Convert incident learnings into operational runbooks
- **release-manager** — If the incident requires a hotfix release
- **security** — If the incident has security implications
- **log-analysis** — Read-only operational log investigation and evidence reduction
- **aws-alarm-investigator** — When the entry point is a specific alarm rather than a reported outage

## References

- `references/cloudwatch-observability-recovery.md` — CloudWatch dashboard,
  metric, alarm, and log-signal recovery checklist
