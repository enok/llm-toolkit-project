---
name: confluence-documentation-specialist
description: Read-only Confluence documentation specialist for wiki pages, page hierarchy, comments, attachments, source-grounded docs sync, rendered page verification, and draft-only human-facing Confluence replies. Use whenever Confluence state affects documentation quality, PR/Jira readiness, architecture docs, diagrams, runbooks, or wiki publication, or when the user asks to validate wiki docs, review a Confluence page, or check source-to-wiki drift.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Confluence Documentation Specialist

Use this skill to route Confluence page, hierarchy, attachment, comment, or
source-to-wiki synchronization work through the Confluence Documentation
Specialist. The specialist is read-only: it reads the current wiki state,
compares it with repository evidence, and returns findings plus draft-only
replies; the root agent owns every page write and every posted comment.

Trigger examples:

- "is this Confluence page still accurate after the change?"
- "check the wiki hierarchy for the new runbook"
- "draft a reply to the reviewer comment on the design page"
- "sync the README changes to the team wiki"

## Workflow

1. Load `workflows/confluence-documentation-specialist-validation.md`.
2. Invoke or follow `tool-subagents/confluence-documentation-specialist.md`.
3. Keep root-agent ownership for edits, page publication, comments, validation,
   commits, pushes, and user-facing communication.
4. Compose with `skills/confluence-documentation/SKILL.md`,
   `workflows/confluence-documentation.md`, `integrations/confluence.md`,
   `documentation-reviewer`, `diagram-creation-specialist`,
   `system-architecture-specialist`, and `pr-validator` only when their
   evidence lanes are relevant. Use `prod-doc-promoter` when deployed ticket
   docs need promotion from an intake folder to canonical Confluence homes.
5. Keep space keys, page IDs, and page maps in the consumer repo's `docs/llm/`
   or in the request itself, not in this skill.
6. If the specialist misses a reusable pattern, run
   `workflows/confluence-documentation-specialist-evolution.md`.
