---
title: Diagram conventions for project-discovery
tags: [mermaid, diagrams, architecture, flows]
---

# Diagram conventions

Use these when creating architecture or flow diagrams for the destination project. For architecture documentation, select the view type first with `skills/diagram-authoring/references/diagram-type-standards.md`: C4 component diagrams for software structure, AWS architecture diagrams for cloud topology, and sequence diagrams for runtime detail.

## Format

- Use **Mermaid** (flowchart, sequenceDiagram, etc.) in markdown code blocks so they render in GitHub and common editors when the destination repo is Markdown-first. For C4 component and AWS architecture diagrams, prefer the destination repo's existing PlantUML standard when one exists.
- Prefer committed paths under `docs/`: e.g. `docs/architecture.md` for system/component overview, `docs/flows/<name>.md` for specific flows (request-flow, deployment, data-flow).
- When exporting diagrams to images, follow `skills/diagram-authoring/references/diagram-export-quality.md` and `skills/image-quality-inspection/references/image-quality-gate.md`: prefer SVG/PDF, verify dimensions for required PNG/JPG output, inspect every generated/exported image after export, and fix/re-render until acceptable. This post-export quality-control step is mandatory.
- For AWS architecture diagrams, follow `skills/diagram-authoring/references/aws-architecture-quality-control.md`: keep the view topology-first, avoid numbered runtime arrows, and move ordered behavior to sequence diagrams.

## Mermaid syntax rules

- **Node IDs:** No spaces. Use camelCase, PascalCase, or underscores (e.g. `UserService`, `api_gateway`).
- **Edge labels** with special characters: Wrap in double quotes (e.g. `A -->|"O(1) lookup"| B`).
- **Node labels** with parentheses or colons: Use double quotes (e.g. `A["Process (main)"]`).
- **Reserved words:** Avoid as node IDs: `end`, `subgraph`, `graph`, `flowchart`.
- **Styling:** Do not use explicit colors or `style`/`classDef`; let the renderer use theme defaults.

## Placement

| Content | Suggested path |
|--------|-----------------|
| Overall architecture / components | `docs/architecture.md` |
| Request or API flow | `docs/flows/request-flow.md` or similar |
| Deployment pipeline | `docs/flows/deployment.md` |
| Data flow | `docs/flows/data-flow.md` |

Create `docs/` or `docs/flows/` if missing; keep filenames short and descriptive.
