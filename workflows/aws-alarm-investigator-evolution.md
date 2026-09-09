---
description: Improve the AWS alarm investigator from validated misses, noisy hypotheses, unsafe evidence handling, and routing gaps
---

# AWS Alarm Investigator Evolution

Use this workflow when the AWS Alarm Investigator specialist needs a durable
improvement after a real alarm investigation, automation dry run, or reviewer
finding.

## Steps

1. Capture concrete evidence:
   - alarm type, namespace, dimensions, and investigation window
   - the specialist output that was wrong, noisy, unsafe, incomplete, or too
     expensive
   - the evidence that proved the better investigation path
2. Classify the fix target:
   - prompt procedure or output contract ->
     `tool-subagents/aws-alarm-investigator.md` (mirror the body into the
     `.toml`)
   - service probe hint or known false-positive pattern -> the same prompt's
     probe/false-positive sections
   - validation procedure -> `workflows/aws-alarm-investigator-validation.md`
   - skill entrypoint -> `skills/aws-alarm-investigator/SKILL.md`
   - trigger/routing -> `INTENTS.md`, `rules/request-orchestration.md`
   - companion skill/rule/runbook -> `skills/log-analysis/`,
     `rules/log-analysis-safety.md`, `skills/incident-ops/`
   - service- or account-specific fact -> the consumer repo's `docs/llm/`,
     never a shared asset
3. Keep the update generic:
   - add reusable alarm-shape guidance, not a one-off incident narrative
   - preserve read-only authority and human approval for email/remediation
   - keep production evidence redacted; never embed secrets, account IDs,
     real alarm/log-group/function names, or raw payloads
4. Make the smallest durable update.
5. Run `documentation-reviewer` on changed docs, prompts, and workflows.
6. Validate with:
   - `node scripts/validate-specialist-agent.js aws-alarm-investigator`
   - `npm run workflows:size:check`
   - `npm run subagents:check`
   - `npm run llm-content:security-check`
7. Report updated files, validation, residual risk, and any alarm patterns that
   still require owner-specific runbooks.
