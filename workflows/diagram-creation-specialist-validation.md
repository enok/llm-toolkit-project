---
description: Run the Diagram Creation Specialist for source-grounded C4, AWS, sequence, Mermaid, PlantUML, export, and image-quality validation
---

# Diagram Creation Specialist Validation

Use this workflow when architecture, flow, AWS, Mermaid, PlantUML, Confluence,
PDF, slide, or PR diagrams need specialist creation guidance or validation.

## Phase 1 - Scope And Evidence

1. Establish repo, base/head, dirty-tree ownership, destination, required
   diagram views, renderer/export path, and whether generated artifacts are
   versioned.
2. Load only relevant context: `skills/diagram-authoring/SKILL.md`,
   `skills/diagram-authoring/references/deterministic-diagram-system.md`,
   `workflows/document-creation.md`, `skills/image-quality-inspection/SKILL.md`,
   existing diagrams, source files, configs, tickets, PRs, wiki pages, and any
   checked-in diagram standard in the consumer repo's `docs/llm/`.
3. Identify whether `system-architecture-specialist` should first validate
   boundaries, ownership, or quality attributes.

## Phase 2 - Specialist Pass

1. Invoke or follow `tool-subagents/diagram-creation-specialist.md`.
2. Ask for a view plan, source grounding, draft diagram source if useful,
   deterministic style contract, compile/export checks, image-quality gates,
   claim drift, and handoffs.
3. Require every generated/exported image and final embedded render to have a
   real inspection path. Sampling is not acceptable.

## Phase 3 - Reduce And Act

1. Accept only source-grounded nodes, edges, labels, boundaries, and artifacts.
2. Reject diagrams that violate the deterministic style contract: mixed views,
   unpinned renderers, improvised palettes, dense labels, bad icon use,
   overfilled legends, crossed labels, or uninspected exports.
3. Apply the smallest diagram source or doc update only when requested.
4. Keep human-facing diagram comments draft-only until explicit approval
   (`rules/human-comment-reply-gate.md`).
5. Use `documentation-reviewer` on changed docs, diagram text, generated LLM
   surfaces, and draft replies.

## Phase 4 - Validate

Run the narrowest relevant checks:

- Mermaid/PlantUML syntax or the project renderer;
- export/re-export commands for tracked generated artifacts;
- deterministic style review against
  `skills/diagram-authoring/references/deterministic-diagram-system.md`;
- actual image/PDF/wiki/render inspection through `image-quality-inspection`;
- `npm run workflows:size:check`, index checks, and security scan when toolkit
  LLM surfaces changed.

## Phase 5 - Evolve

If the specialist misses a recurring diagram pattern, renderer issue, quality
gate, notation rule, or handoff gap, run
`workflows/diagram-creation-specialist-evolution.md`.
