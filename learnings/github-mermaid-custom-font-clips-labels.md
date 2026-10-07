---
title: GitHub's Mermaid viewer clips labels when the init font is not installed
category: toolchain
created: 2026-10-07
tags: [mermaid, github, diagram, font-family, rendering, png, label-clipping]
---

# Problem

GitHub's Mermaid viewer clipped the last characters of every label when the diagram's
init directive asked for a custom font, for example `"fontFamily": "Inter, ..."`. The
font is missing on the machines of people viewing the repository.

# Failed Approaches

None recorded in the session notes; the default behaviour produced the failure described above.

# Solution

Commit the `.mmd` sources with a font stack every viewer has, and put the nicer font in
only when the PNG is rendered:

```text
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Arial, Helvetica, sans-serif"}}}%%
flowchart LR
    A["Client"] --> B["Service"]
```

The PNG renderer swaps the font in a temporary copy, so the committed source never
changes:

```python
SAFE = '"fontFamily": "Arial, Helvetica, sans-serif"'
NICE = '"fontFamily": "Inter, Arial, sans-serif"'   # only where that font is installed
render_copy = source_text.replace(SAFE, NICE)       # render this copy to PNG; never commit it
```

The full init line in the toolkit's diagram style names the font twice (inside
`themeVariables` and at the top level), and `replace` swaps both occurrences.

Verify on GitHub itself, the way the fix was verified: push a test commit to the PR
branch and inspect the rendered diagram there.

Durable guidance: skills/diagram-authoring/references/publication-diagram-style.md

# Why

The session established the trigger (a requested font missing on viewers), the fix (an
Arial stack in the source, the nicer font only at PNG render time) and how it was
verified (a test commit on the PR branch, inspected on GitHub). It did not isolate the
mechanism. Inference: Mermaid sizes label boxes from text measured in the requested font,
and when the viewer substitutes another font the box is too narrow for the real text.
The Arial stack was verified on that one viewer check, so re-check on GitHub after
changing the init line.
