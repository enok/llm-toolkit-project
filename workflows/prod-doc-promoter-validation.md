---
description: Validate and safely execute production documentation promotion from a temporary Confluence intake folder to canonical Confluence homes after prod deployment gates pass
---

# Prod Doc Promoter Validation

Use this workflow when ticket-scoped documentation should be promoted from a
temporary Confluence intake folder into canonical Confluence pages after the
ticket is finished and deployed to production.

The `prod-doc-promoter` subagent is read-only. The root agent or scheduled
automation owns writes and may run independently only when the gates below pass.

## Phase 1 - Scope And Evidence Gates

1. Establish ticket key, repo, PR/release/deployment references, source
   Confluence intake folder URL or ID, intended destination map, and automation
   policy. Take the intake folder and destination map from the request, the
   automation prompt, or the consumer repo's `docs/llm/` (for example
   `docs/llm/doc-promotion-map.md`); never guess them.
2. Verify dirty-tree ownership before editing toolkit or generated surfaces.
3. Prove the ticket is finished and deployed to production using Jira status,
   PR merge/live head, release notes, deployment checks, CI/CD, or production
   smoke evidence. If the ticket is not deployed, return `monitor`.
4. Read the source Confluence folder/page and destination candidates before any
   write. If a URL uses `/folder/<id>`, verify folder support explicitly; a
   page-only CLI returning `page not found` is a tool-surface blocker, not
   evidence that the folder is absent.
5. Verify write capability and permissions for the exact operations needed:
   move/update pages, add labels, update attachments, and read permitted
   operations. If only read tools are available, block with the required
   REST/MCP/CLI capability.

## Phase 2 - Specialist Pass

1. Invoke or follow `tool-subagents/prod-doc-promoter.md`.
2. Provide source folder read-back, child pages, attachments, labels, comments,
   versions, destination map, ticket/PR/release/deploy evidence, and tool
   limitations.
3. Ask for a dry-run promotion plan, blockers, related specialist handoffs,
   validation checklist, and learning/token-efficiency signals.

## Phase 3 - Reduce And Decide

1. Accept only evidence-backed, in-scope specialist findings.
2. Choose `ready-to-promote` only when production deployment, source inventory,
   destination mapping, versions, permissions, and validation plan are all
   unambiguous.
3. Choose `blocked` when destination ownership, write permission, version state,
   content safety, attachments, or generated artifact quality cannot be proven.
4. Choose `monitor` when the ticket is not yet fully deployed to production or
   the release is still within an active rollback/verification window.

## Phase 4 - Execute Promotion When Ready

When the decision is `ready-to-promote`, the root agent or scheduled automation
may proceed without another prompt if the user or automation requested automatic
operation (`rules/external-write-authorization.md` still binds the write to that
standing instruction and its named intake folder).

1. Re-read source and destination versions immediately before each write.
2. Move pages to their canonical parent, or update/merge content only when the
   destination plan explicitly calls for it.
3. Preserve page history, attachments, labels, backlinks, and source links.
4. Add or update labels and titles only as planned.
5. Do not delete pages, delete attachments, archive or purge folders, or post
   explanatory comments without explicit user approval of the exact target and
   text. Automatic runs never archive; they report leftover children instead.
6. If a write fails or versions changed, stop and re-run the specialist pass
   with fresh evidence rather than retrying blindly.

## Phase 5 - Validate

Run the narrowest relevant checks:

- Confluence read-back for final parent, title, labels, versions, attachments,
  comments, and source folder remaining children.
- Link checks for Jira, PR/release, repository source docs, related runbooks,
  diagrams, and canonical Confluence destinations.
- `documentation-reviewer` for promoted or merged documentation content.
- `image-quality-inspection` for every generated/exported image, screenshot,
  PDF page render, slide/document render, or Confluence-processed attachment.
- `node scripts/validate-specialist-agent.js prod-doc-promoter`, workflow size
  validation, index validation, and LLM-surface security checks when toolkit
  assets changed.

## Phase 6 - Report And Evolve

Report:

- ticket and production evidence;
- source folder inventory and remaining count;
- destination mapping and final URLs;
- promotion operations performed or exact blocker;
- validation results;
- related specialist handoffs;
- reusable learning.

If this specialist misses a recurring issue or is too noisy, run
`workflows/prod-doc-promoter-evolution.md`.
