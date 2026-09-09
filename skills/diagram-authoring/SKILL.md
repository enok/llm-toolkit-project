---
name: diagram-authoring
description: Create, validate, and export high-resolution standardized C4 component, AWS architecture, and sequence detail diagrams from source evidence. Use when asked for architecture diagrams, Mermaid/PlantUML, Confluence diagrams, markdown PDFs, or diagram fixes.
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

1. **Choose the required architecture view**
   - Use a **C4 component diagram** for software components, ownership, boundaries, and dependencies.
   - Use an **AWS architecture diagram** for cloud topology, managed services, deployment boundaries, networking, storage, messaging, and observability.
   - Use a **sequence diagram** for implementation details: runtime ordering, request/message lifecycles, retries, branches, failures, and callbacks.
   - Create or update all three views when documenting a system or feature that has component, infrastructure, and runtime detail. If one view is not applicable, state why in the surrounding doc instead of silently substituting another type.
   - Use flowcharts only for non-architecture process documentation or as a secondary summary; do not use them as the primary architecture view.
   - Use a **state diagram** for lifecycle/status transitions (order states, job states, approval flows) when the transitions themselves are the subject; keep it separate from the three architecture views.
2. **Prove every node** from code, config, or docs. Do not invent services.
3. **Make boundaries explicit**: user, browser/client, service, database, queue, third party, and external organization.
4. **Apply the deterministic diagram system** in `skills/diagram-authoring/references/deterministic-diagram-system.md` before drafting.
   - Use its fixed view mapping, palette, label limits, layout budgets, pinned renderer defaults, and templates unless the destination repo has a stricter checked-in diagram standard.
   - Reject and split diagrams that cannot meet the deterministic gates instead of shrinking text or improvising new styles.
5. **Follow the standard type rules** in `skills/diagram-authoring/references/diagram-type-standards.md`.
6. **Prefer Mermaid in Markdown** for portable non-AWS sequence or simple process diagrams unless the repo already standardizes on PlantUML.
   - Never author or maintain diagrams with imperative pixel-drawing code (PIL/Pillow, matplotlib shapes, raw canvas coordinates). If a repo generates diagrams from such a script, migrate the content to declarative PlantUML/Mermaid sources and reduce the script to a thin compile/verify step; do not patch coordinates.
   - For C4 component diagrams, prefer C4-PlantUML when PlantUML is available or already used.
   - For AWS architecture diagrams, prefer AWS Icons for PlantUML with a pinned release tag; use `references/aws-plantuml-style.md`.
   - For polished AWS documentation diagrams, use the official AWS Architecture Icons package from `https://aws.amazon.com/architecture/icons/` or a verified local copy of that package. Do not use third-party AWS icon libraries as the source of truth unless the official package is unavailable and the user accepts the compromise.
   - Match the AWS Solutions architecture overview pattern: outer AWS Cloud boundary, meaningful account/VPC/subnet/component boundaries, short labels under icons, sparse orthogonal connectors, and numbered process explanations in surrounding documentation instead of embedding resource inventories, timing evidence, or long notes in the diagram body.
7. **Validate syntax** with the repository's renderer/export path when available.
   - For PlantUML source files (`*.puml`), always compile them with PlantUML before considering the diagram change complete.
   - If the repository versions generated images, re-export them from the compiled PlantUML source after every source change.
8. **Export at high quality** using `skills/diagram-authoring/references/diagram-export-quality.md`.
   - Prefer SVG/PDF for generated diagrams whenever the destination supports vector output.
   - If PNG/JPG is required, render from source at high resolution and verify actual dimensions before committing or attaching it.
   - Then apply the `image-quality-inspection` gate to every generated/exported image artifact and final embedded render.
9. **Run mandatory post-export quality control** after export.
   - Open the rendered PNG/SVG/PDF and inspect it visually before completion. This is not optional.
   - For AWS architecture PNG exports, also apply `skills/diagram-authoring/references/aws-architecture-quality-control.md`.
   - Use the loop: create/update/improve, validate against AWS reference diagrams, and repeat until the rendered result is at the same quality bar. Do not call the diagram ready when there are label overlaps, arrows through text, service icons sitting on network boundaries, unexplained boundary misuse, clipped labels, stale icons, or report-style tables inside the architecture canvas.
   - Improve layout, labels, grouping, spacing, or split the diagram if the rendered result is cramped, unreadable, misleading, or visually low quality.
   - If an exported image cannot be inspected, do not claim the diagram is ready; report the artifact and blocker.
10. **Keep source authoritative**. Treat PNG/PDF/SVG exports as generated artifacts unless the project intentionally versions them.

## Mermaid guardrails

- Use stable IDs without spaces or reserved words.
- Quote labels with punctuation, parentheses, colons, pipes, or slashes.
- Avoid hard-coded colors unless the repo has a diagram theme standard.
- Keep diagrams readable: split if labels or edges become dense.
- Include a short legend only when it reduces ambiguity.
- Prefer SVG export for Mermaid when producing committed docs, PDFs, or wiki attachments. Use PNG only when the destination requires raster output.

## PlantUML guardrails

- Pin remote include libraries to release tags; do not use mutable `main` URLs for committed diagrams.
- Include only the AWS icon files needed by the diagram.
- Use AWS icons for AWS-managed services and generic `component`/`Client` nodes for app code, internal services, and third parties.
- C4 component diagrams show static structure only; move runtime ordering to sequence diagrams.
- Never use `skinparam linetype ortho` in C4-PlantUML diagrams: ortho routing drops `Rel` labels onto nodes and other labels. Rely on default spline routing with `LAYOUT_LEFT_RIGHT()`/`LAYOUT_WITH_LEGEND()`, and reserve `linetype ortho` for AWS icon topology diagrams with sparse connectors.
- AWS architecture diagrams show deployment/topology only; move class/package internals to C4 or text.
- AWS architecture diagrams must not use numbered edge labels or long legends to explain runtime ordering. Put ordered request, callback, retry, branch, and failure behavior in sequence diagrams.
- Keep component diagrams grouped by boundary/responsibility and sequence diagrams grouped by runtime ownership.
- Use `alt`/`else` for decisions, `par`/`else` for concurrent flows, and notes/legends for constraints and operational details.
- For sequence diagrams, include stateful upstream and downstream systems that
  materially explain the lifecycle, even when the current service does not call
  them directly. Use a concise note for upstream handoff state rather than
  hiding token/session, cache, calibration, or association tables.
- Always compile changed `*.puml` files, and re-export tracked images when the repo versions generated diagrams.
- Use `-DPLANTUML_LIMIT_SIZE=32768` for wide/detailed diagrams. Prefer `-tsvg`; use `skinparam dpi 300` or renderer-equivalent scale when PNG is required.
- Always inspect the rendered image after export and improve the diagram if the visual result is unclear. This post-export quality-control step is mandatory.

## Review checklist

- [ ] Every component exists in source or documented infrastructure.
- [ ] The deterministic diagram system was applied: view type, template, palette, labels, layout budget, renderer pins, and rejection gates are explicit.
- [ ] Trust boundaries and external systems are visible.
- [ ] Data direction and ownership are clear.
- [ ] Failure/rollback path is shown for operational diagrams.
- [ ] Diagram renders in the target viewer.
- [ ] PlantUML source files compile successfully when `*.puml` files are changed.
- [ ] Generated diagram artifacts are vector output or high-resolution raster output that meets the export-quality standard.
- [ ] 100% of generated/exported diagram images passed `image-quality-inspection`, including embedded PDF/wiki renders when present.
- [ ] AWS architecture diagrams were compared against official AWS reference diagrams and the official AWS Architecture Icons source, with resource names/timings/long explanations moved to nearby text or tables unless they are essential topology labels.
- [ ] Rendered PNG/SVG/PDF output was visually inspected after export and improved if needed; uninspected output is a blocker.
- [ ] Confluence/wiki copies link back to the repo source of truth.
- [ ] Published wiki pages and attachments were read back after publishing and pass any destination content gates (no forbidden identifier patterns, no stale run/version labels).

## Related

- `skills/diagram-authoring/references/deterministic-diagram-system.md`
- `skills/diagram-authoring/references/diagram-type-standards.md`
- `skills/diagram-authoring/references/aws-plantuml-style.md`
- `skills/diagram-authoring/references/aws-architecture-quality-control.md`
- `skills/diagram-authoring/references/diagram-export-quality.md`
- `skills/diagram-authoring/references/diagram-quality-review.md`
- `skills/image-quality-inspection/SKILL.md`
- `skills/project-discovery/references/diagram-conventions.md`
- `workflows/document-creation.md`
- `workflows/markdown-pdf-export.md`
