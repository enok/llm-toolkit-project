---
description: Run the Confluence Documentation Specialist for source-grounded wiki page, hierarchy, attachment, comment, and draft-reply validation
---

# Confluence Documentation Specialist Validation

Use this workflow when Confluence page state, wiki hierarchy, attachments,
comments, or source-to-wiki synchronization need specialist validation before
publication, approval, PR readiness, or handoff.

## Phase 1 - Scope And Tool Surface

1. Establish repo, base/head, dirty-tree ownership, target space/page IDs,
   parent page, title, labels, attachments, comments, and intended audience.
   Take space keys and page IDs from the request or the consumer repo's
   `docs/llm/`; never assume them.
2. Confirm the available Confluence surface: search, view by ID, children,
   labels, comments, versions, attachments, create/update, or read-only only.
3. Load only relevant context: `workflows/confluence-documentation.md`,
   `skills/confluence-documentation/SKILL.md`, `integrations/confluence.md`,
   `rules/human-comment-reply-gate.md`, and source artifacts for the claims.

## Phase 2 - Specialist Pass

1. Invoke or follow `tool-subagents/confluence-documentation-specialist.md`.
2. Provide current page read-back, source docs, code diffs, diagrams, Jira/PR
   context, and rendered artifact evidence when available.
3. Ask for Confluence state, claim drift, blockers, draft-only reply text, and
   related-specialist handoffs.

## Phase 3 - Reduce And Act

1. Accept only evidence-backed, in-scope findings.
2. Prefer source doc, diagram, attachment, or page-content fixes over comments.
3. Keep every human-facing wiki or review reply as a draft until the user
   approves the exact target and text.
4. Use `documentation-reviewer` after any doc, prompt, generated surface,
   Confluence draft, or page-comment draft changes.

## Phase 4 - Validate

Run the narrowest relevant checks:

- read-back page/child/label/comment/version evidence;
- link/render checks and attachment inventory;
- `image-quality-inspection` for every generated/exported image and final wiki
  render;
- `npm run workflows:size:check` and index checks when toolkit docs changed.

## Phase 5 - Evolve

If the specialist misses a repeated Confluence pattern, noisy finding, weak
handoff, or token-heavy context load, run
`workflows/confluence-documentation-specialist-evolution.md`.
