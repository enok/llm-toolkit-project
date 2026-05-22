---
title: Rendered diagram quality review
tags: [diagrams, quality, review, c4, plantuml, mermaid]
---

# Rendered diagram quality review

Use this reference after compiling/exporting a diagram. Compilation proves syntax; visual review proves the diagram communicates clearly.

## Source and attribution

This guide adapts generic review patterns from:

- The shared toolkit's existing diagram-authoring guidance.
- Official C4 model guidance for audience-appropriate abstraction levels.
- `softaworks/agent-toolkit` C4 architecture skill patterns, reviewed from an MIT-licensed public repository.
- Public PlantUML skill documentation reviewed for troubleshooting ideas only where license metadata was unavailable; do not vendor or execute third-party scripts without the external-skill-intake process.

## Rendered-output review checklist

Open the generated PNG/SVG/PDF and verify:

- The title states the diagram scope and abstraction level.
- Each element has a clear name, type, and short purpose or technology label when useful.
- Boundaries are visible: user/client, application, downstream service, storage, messaging, cloud provider, third party.
- Arrows are directional and labeled with action verbs such as `publishes`, `reads`, `writes`, `redirects`, or `invokes`.
- Labels are readable at the size used by the target documentation page.
- Arrows do not cross enough to obscure ownership or ordering.
- Diagram content fits a normal documentation viewport; if not, split by flow, endpoint, or abstraction level.
- Sequence diagrams show important success, branch, retry, and failure paths with `alt`, `else`, or `par` blocks where applicable.
- Component diagrams avoid runtime ordering details that belong in sequence diagrams.
- AWS icons are used only for AWS-managed services; application code and third parties use generic nodes.
- Generated images are refreshed from current source and committed only when the repository versions them.

## Improve-and-re-export triggers

Improve the source and re-export when the rendered output has any of these issues:

| Issue | Improvement |
| --- | --- |
| More than about 20 major elements | Split into context, component, and sequence diagrams |
| Long wrapped labels dominate the diagram | Shorten labels and move detail into notes or README text |
| Multiple unrelated flows share one diagram | Create focused diagrams per endpoint, job, or runtime path |
| Arrows imply the wrong order or ownership | Reorder participants or group by runtime boundary |
| Icons make app code look cloud-managed | Replace AWS icon with generic `component`, `rectangle`, or `Client` |
| Notes obscure the diagram | Move long explanations to Markdown and keep only concise notes |
| Image is too wide/tall for review tools | Reduce participants, split the flow, or tune spacing/layout |

## Suggested review loop

1. Compile/export the diagram using the repository's documented renderer.
2. Open the exported image with the IDE preview or image viewer.
3. Check readability and correctness using the checklist above.
4. Patch the diagram source if needed.
5. Re-export the image.
6. Repeat until the rendered artifact is clear enough for review.
