---
name: prod-doc-promoter
description: Read-only production documentation promotion specialist for moving deployed ticket documentation from a configured Confluence intake folder to canonical Confluence destinations after prod deployment gates pass. Use when the user asks to promote deployed ticket docs, clean up the ticket documentation folder, or keep canonical Confluence pages current after a production release.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Prod Doc Promoter

Use this skill when a finished ticket has been deployed to production and the
agent needs to promote temporary ticket documentation from a configured
Confluence intake folder into the correct durable Confluence location.

Trigger examples:

- "after prod deploy, move ticket docs to the right Confluence page"
- "promote deployed ticket documentation"
- "clean up the Jira/Confluence ticket docs folder"
- "keep canonical Confluence docs up to date after production deployment"

This skill supports automatic scheduled runs. The specialist stays read-only and
returns a write-ready plan; the root agent or automation may execute Confluence
writes without another prompt only when every gate in
`workflows/prod-doc-promoter-validation.md` passes.

## Pattern

1. **Intake folder** - ticket-scoped pages are written under one configured
   Confluence folder (or parent page) while the ticket is in flight.
2. **Production gate** - promotion starts only after the ticket is Done and the
   change is verified in production (merged head, release, deployment record,
   or smoke evidence).
3. **Destination map** - each page kind (design note, runbook, API change,
   diagram, decision record) maps to one canonical parent page. The map lives in
   the consumer repo's `docs/llm/` (for example
   `docs/llm/doc-promotion-map.md`), never in this shared skill.
4. **Non-destructive by default** - pages are moved or merged, history and
   attachments are preserved, and nothing is deleted, archived, or purged
   without explicit human approval of the exact target.
5. **Verify after write** - re-read the final hierarchy, titles, labels, links,
   and the remaining intake-folder children.

## Workflow

1. Load `workflows/prod-doc-promoter-validation.md`.
2. Invoke or follow `tool-subagents/prod-doc-promoter.md`.
3. Compose with `confluence-documentation`,
   `confluence-documentation-specialist`, `documentation-reviewer`,
   `pr-validator`, `release-manager`, `diagram-creation-specialist`, and
   `system-architecture-specialist` only when their evidence lanes are relevant.
4. Keep root-agent or scheduled-automation ownership for Confluence/Jira/GitHub
   writes, validation, commits, pushes, and user-facing communication.
5. Never delete pages, delete attachments, archive or purge folders, or post
   comments without explicit approval of the exact target and text.
6. If the specialist misses a reusable pattern, run
   `workflows/prod-doc-promoter-evolution.md`.

## Configuration

Keep tenant-specific defaults (space key, intake folder ID or URL, destination
map, label conventions) in the automation prompt or in the consumer repo's
`docs/llm/`. Pass the Confluence folder URL or folder ID as source-folder input
instead of embedding tenant values in generic routing rules.

Example destination map shape (consumer repo, `docs/llm/doc-promotion-map.md`):

| Page kind | Detect by | Canonical parent | Labels |
| --- | --- | --- | --- |
| Runbook | title prefix `Runbook:` or label `runbook` | `<SPACE>/Operations/Runbooks` | `runbook`, `<service>` |
| Design note | label `design` | `<SPACE>/Architecture/<service>` | `design`, `<TICKET-ID>` |
| API change | label `api` | `<SPACE>/APIs/<service>` | `api-change` |
