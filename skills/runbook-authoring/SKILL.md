---
name: runbook-authoring
description: >
    Write or update operational runbooks for deploy, triage, rollback, and recurring
    operational procedures. Trigger when the user asks to write a runbook, document an
    operational procedure, create triage instructions, or formalize a recurring ops workflow.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Runbook Authoring

Use this skill to create structured, actionable operational documentation.

## When to Apply

- Writing a new runbook for a deploy, triage, or rollback procedure
- Documenting an operational procedure after an incident
- Formalizing a recurring ops workflow that lives in tribal knowledge
- Updating an existing runbook with new learnings

## Workflow

1. **Check for existing runbooks** in the repo or wiki before creating a new one.
2. **Identify the audience:** on-call engineer, release manager, platform team, or external stakeholder.
3. **Structure the runbook:**
   - **Title and purpose** — one sentence on what this runbook is for
   - **When to use** — specific triggers or conditions
   - **Prerequisites** — access, tools, permissions needed
   - **Steps** — numbered, copy-pastable commands with expected output
   - **Decision points** — "if X, do Y; if Z, do W"
   - **Verification** — how to confirm each step worked
   - **Rollback** — how to undo if something goes wrong
   - **Escalation** — when and who to escalate to
4. **Keep commands copy-pastable** — no placeholders without clear instructions on what to substitute.
5. **Include expected output** for critical commands so the operator can confirm success.
6. **Test the runbook** by walking through it mentally or with a dry run.

## Output

Return:
- structured runbook in markdown
- location recommendation (repo docs, wiki, or runbook directory)
- gaps or assumptions that need validation

## Non-Goals

- Do not write vague prose instead of actionable steps.
- Do not assume the reader has deep context — they may be on-call at 2am.
- Do not skip rollback or escalation sections.

## Related Skills

- **incident-ops** — Runbooks often come from incident learnings
- **release-manager** — Release runbooks are a common use case
- **best-practices** — Operational doc patterns

## Related Rules

- `rules/operational-doc-required.md` — recurring deploy/mitigation/rollback/triage work must become a runbook (mirrored locally in `references/operational-doc-required.md` for consumer repos)
- `rules/release-safety.md` — release runbooks must carry verification and rollback gates
