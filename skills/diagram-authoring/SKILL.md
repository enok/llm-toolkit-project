---
name: diagram-authoring
description: Create and validate architecture, flow, sequence, and C4-style diagrams from source evidence. Use when asked for architecture diagrams, Mermaid/PlantUML, Confluence diagrams, markdown PDFs, or diagram fixes.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Diagram Authoring

## Inputs

- Existing docs and diagrams.
- Source files that prove components, routes, jobs, queues, databases, and external dependencies.
- Deployment/config files for runtime names and environment boundaries.
- Ticket or Confluence context only when the diagram is tied to that work.

## Process

1. **Choose the diagram type**
   - Component/C4 for static ownership and boundaries.
   - Flowchart for request/data/deploy flow.
   - Sequence for runtime call ordering and retries/failures.
   - State diagram for lifecycle/status transitions.
2. **Prove every node** from code, config, or docs. Do not invent services.
3. **Make boundaries explicit**: user, browser/client, service, database, queue, third party, and external organization.
4. **Prefer Mermaid in Markdown** for portable source unless the repo already standardizes on PlantUML.
   - When the repo uses AWS-style PlantUML diagrams or the requested diagram is AWS-heavy, use `references/aws-plantuml-style.md`.
5. **Validate syntax** with the repository's renderer/export path when available.
   - For PlantUML source files (`*.puml`), always compile them with PlantUML before considering the diagram change complete.
   - If the repository versions generated images, re-export them from the compiled PlantUML source after every source change.
6. **Review the rendered output** after export.
   - Open the rendered PNG/SVG/PDF and inspect it visually before completion.
   - Improve layout, labels, grouping, spacing, or split the diagram if the rendered result is cramped, unreadable, misleading, or visually low quality.
7. **Keep source authoritative**. Treat PNG/PDF/SVG exports as generated artifacts unless the project intentionally versions them.

## Mermaid guardrails

- Use stable IDs without spaces or reserved words.
- Quote labels with punctuation, parentheses, colons, pipes, or slashes.
- Avoid hard-coded colors unless the repo has a diagram theme standard.
- Keep diagrams readable: split if labels or edges become dense.
- Include a short legend only when it reduces ambiguity.

## PlantUML guardrails

- Pin remote include libraries to release tags; do not use mutable `main` URLs for committed diagrams.
- Include only the AWS icon files needed by the diagram.
- Use AWS icons for AWS-managed services and generic `component`/`Client` nodes for app code, internal services, and third parties.
- Keep component diagrams grouped by boundary/responsibility and sequence diagrams grouped by runtime ownership.
- Use `alt`/`else` for decisions, `par`/`else` for concurrent flows, and notes/legends for constraints and operational details.
- Always compile changed `*.puml` files, and re-export tracked images when the repo versions generated diagrams.
- Always inspect the rendered image after export and improve the diagram if the visual result is unclear.

## Review checklist

- [ ] Every component exists in source or documented infrastructure.
- [ ] Trust boundaries and external systems are visible.
- [ ] Data direction and ownership are clear.
- [ ] Failure/rollback path is shown for operational diagrams.
- [ ] Diagram renders in the target viewer.
- [ ] PlantUML source files compile successfully when `*.puml` files are changed.
- [ ] Rendered PNG/SVG/PDF output was visually inspected and improved if needed.
- [ ] Confluence/wiki copies link back to the repo source of truth.

## Related

- `skills/diagram-authoring/references/aws-plantuml-style.md`
- `skills/diagram-authoring/references/diagram-quality-review.md`
- `skills/project-discovery/references/diagram-conventions.md`
- `workflows/document-creation.md`
- `workflows/markdown-pdf-export.md`
