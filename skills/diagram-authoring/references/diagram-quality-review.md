---
title: Rendered diagram quality review
tags: [diagrams, quality, review, c4, plantuml, mermaid]
---

# Rendered diagram quality review

Use this reference after compiling/exporting a diagram. Compilation proves syntax; visual review proves the diagram communicates clearly. This post-export quality-control step is mandatory. Do not sample generated diagram outputs; inspect every generated/exported image and any final PDF/wiki render that embeds it.

## Source and attribution

This guide adapts generic review patterns from:

- The shared toolkit's existing diagram-authoring guidance.
- Official C4 model guidance for audience-appropriate abstraction levels.
- `softaworks/agent-toolkit` C4 architecture skill patterns, reviewed from an MIT-licensed public repository.
- Public PlantUML skill documentation reviewed for troubleshooting ideas only where license metadata was unavailable; do not vendor or execute third-party scripts without the external-skill-intake process.

## Rendered-output review checklist

Open the generated PNG/SVG/PDF and verify:

- The title states the diagram scope and abstraction level.
- Architecture docs use the expected view type: C4 for components, AWS for architecture/topology, and sequence for detailed runtime behavior.
- Each element has a clear name, type, and short purpose or technology label when useful.
- Boundaries are visible: user/client, application, downstream service, storage, messaging, cloud provider, third party.
- Arrows are directional and labeled with action verbs such as `publishes`, `reads`, `writes`, `redirects`, or `invokes`.
- Labels are readable at the size used by the target documentation page.
- Measured values shown in the diagram (timings, counts, comparison results) were generated from the run's data artifact and match it; no measurement literal is hardcoded in the diagram source or render script.
- Generated output is vector format or a high-resolution raster export from current source.
- Every generated/exported image artifact passed `skills/image-quality-inspection/references/image-quality-gate.md`.
- Arrows do not cross enough to obscure ownership or ordering.
- Diagram content fits a normal documentation viewport; if not, split by flow, endpoint, or abstraction level.
- Sequence diagrams show important success, branch, retry, and failure paths with `alt`, `else`, or `par` blocks where applicable.
- Sequence diagrams show material stateful systems, including upstream handoff
  stores and downstream/cache tables needed to understand the lifecycle.
- Component diagrams avoid runtime ordering details that belong in sequence diagrams.
- AWS architecture diagrams avoid code/package internals that belong in C4 component diagrams or Markdown text.
- AWS architecture diagrams avoid numbered edge labels and long runtime legends that belong in sequence diagrams.
- AWS icons are used only for AWS-managed services; application code and third parties use generic nodes.
- Generated images are refreshed from current source and committed only when the repository versions them.

## Improve-and-re-export triggers

Improve the source and re-export when the rendered output has any of these issues:

| Issue | Improvement |
| --- | --- |
| More than about 20 major elements | Split into C4 component, AWS architecture, and sequence detail diagrams |
| Long wrapped labels dominate the diagram | Shorten labels and move detail into notes or README text |
| Multiple unrelated flows share one diagram | Create focused diagrams per endpoint, job, or runtime path |
| Arrows imply the wrong order or ownership | Reorder participants or group by runtime boundary |
| Icons make app code look cloud-managed | Replace AWS icon with generic `component`, `rectangle`, or `Client` |
| Notes obscure the diagram | Move long explanations to Markdown and keep only concise notes |
| Image is too wide/tall for review tools | Reduce participants, split the flow, or tune spacing/layout |
| PNG/JPG is blurry, pixelated, or below target dimensions | Re-render from source as SVG/PDF or high-resolution PNG; do not upscale a low-resolution export |
| AWS architecture view contains numbered runtime steps | Replace numbering with verb labels and create a separate sequence diagram for ordering |

## Mandatory review loop

1. Compile/export the diagram using the repository's documented renderer.
2. For raster output, verify dimensions meet `diagram-export-quality.md`.
3. Open the exported image with the IDE preview or image viewer.
4. Check readability and correctness using the checklist above.
5. Patch the diagram source if needed.
6. Re-export the image.
7. Repeat until the rendered artifact is clear enough for review.

If the exported image cannot be opened or inspected, stop and report the artifact as a blocker. Do not mark the diagram ready.
