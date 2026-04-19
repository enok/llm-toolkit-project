---
title: Diagram conventions for project-discovery
tags: [mermaid, diagrams, architecture, flows]
---

# Diagram conventions

Use these when creating architecture or flow diagrams for the destination project.

## Format

- Use **Mermaid** (flowchart, sequenceDiagram, etc.) in markdown code blocks so they render in GitHub and common editors.
- Prefer committed paths under `docs/`: e.g. `docs/architecture.md` for system/component overview, `docs/flows/<name>.md` for specific flows (request-flow, deployment, data-flow).

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
