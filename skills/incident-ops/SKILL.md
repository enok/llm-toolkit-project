---
name: incident-ops
description: >
    Support incident triage, mitigation, and communication. Trigger when the user asks for
    incident handling, blast-radius analysis, mitigation sequencing, comms cadence, or
    post-incident follow-up planning.
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
