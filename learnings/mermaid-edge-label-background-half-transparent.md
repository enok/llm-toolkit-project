---
title: Mermaid 11 edge-label backgrounds are half transparent - fix with an mmdc CSS file
category: toolchain
created: 2026-11-26
tags: [mermaid, mmdc, flowchart, edge-label, css, render, htmllabels, png]
---

# Problem
In flowcharts rendered with Mermaid 11 and `htmlLabels: false`, each edge label sits on a
background rectangle drawn at opacity 0.5, so the connecting line shows through the label text
and the PNG is hard to read. Observed with Mermaid 11; later versions may differ.

# Failed Approaches
- Changing the diagram source: the source is correct and should stay unchanged.
- Increasing font size: the line still crosses the text.

# Solution
Render with a CSS file: `mmdc -i <diagram>.mmd -o <diagram>.png --cssFile mermaid-labels.css`.

```css
.edgeLabel rect,
.edgeLabel .background,
.edgeLabel .labelBkg,
.labelBkg {
  fill: #FFFFFF !important;
  opacity: 1 !important;
  stroke: #FFFFFF !important;
  stroke-width: 8px !important;
}
.edgeLabel,
.edgeLabel p {
  background-color: #FFFFFF !important;
}
```

The thick white stroke adds padding around the label. Only the render uses the CSS; the repository
source stays as it is. Related: `github-mermaid-custom-font-clips-labels.md`,
`skills/diagram-authoring/references/publication-diagram-style.md`.

# Why
Mermaid's own stylesheet sets the label background rectangle to opacity 0.5. A user CSS file with
`!important` overrides it at render time without touching the diagram.
