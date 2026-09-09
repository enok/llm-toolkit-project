---
name: diagram-creation-specialist
description: Read-only diagram creation specialist for source-grounded C4 component, AWS architecture, sequence, flow, Mermaid, PlantUML, export, image-quality inspection, Confluence/wiki attachments, PDF/doc renders, and diagram-related human reply drafts. Use whenever a diagram is created, changed, reviewed, exported, or used for PR/Jira/architecture evidence, or when the user asks for a strict C4, AWS, or sequence diagram with a deterministic style contract.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Diagram Creation Specialist

Use this skill to route diagram creation or validation through the Diagram
Creation Specialist. The specialist is read-only: it proves every node, edge,
and boundary from source evidence, fixes the style contract before drafting,
and hands the root agent draft diagram source plus the checks to run.

Trigger examples:

- "create a C4 component diagram for this service"
- "draw the AWS architecture for this stack"
- "add a sequence diagram of the retry path to the PR"
- "review this Mermaid diagram against the code"
- "export this diagram for Confluence and check the image"

## Workflow

1. Load `workflows/diagram-creation-specialist-validation.md`.
2. Invoke or follow `tool-subagents/diagram-creation-specialist.md`.
3. Keep root-agent ownership for source edits, exports, generated artifacts,
   validation, commits, pushes, and user-facing communication.
4. Compose with `skills/diagram-authoring/SKILL.md`,
   `skills/diagram-authoring/references/deterministic-diagram-system.md`,
   `skills/image-quality-inspection/SKILL.md`,
   `system-architecture-specialist`, `confluence-documentation-specialist`,
   `documentation-reviewer`, and `pr-validator` only when their evidence lanes
   are relevant.
5. Require a deterministic style contract for every diagram handoff: chosen
   view type, template, palette/icon standard, label limits, layout budget,
   renderer pins, split decision, and rejection gates.
6. For AWS documentation-style architecture diagrams, enforce the AWS
   reference loop from `diagram-authoring`: official AWS Architecture Icons,
   AWS Solutions layout comparison, visual inspection, fix, and repeat until the
   exported artifact passes.
7. Keep project-specific renderer facts (checked-in templates, export commands,
   icon library pins) in the consumer repo's `docs/llm/`, not in this skill.
8. If the specialist misses a reusable pattern, run
   `workflows/diagram-creation-specialist-evolution.md`.
