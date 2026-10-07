---
title: Destination legibility for published images
tags: [images, legibility, diagrams, png, svg, publication, article, readme, validator, visual-qa]
---

# Destination legibility for published images

Use this reference when an image will be shown at a known, usually narrow, width: an article column, a README, a social post, a slide. `image-quality-gate.md` requires text to be "readable at the target review size"; this file makes that measurable and defines the independent visual check that enforces it. Sharpness (pixels) and legibility (text size relative to the displayed width) are different properties: fix sharpness with a higher render scale, fix legibility by changing the layout.

## 1. Judge at the destination width

```text
effective text px = text px x column width / image width
```

Text px and image width must be in the same unit (both device pixels of the file, or both CSS pixels of the source).

| Case | Computation | Effective text |
| --- | --- | --- |
| PNG 1568 px wide holding 40 px text, 700 px column | 40 x 700 / 1568 | 17.9 px |
| Hand-drawn SVG 1200 wide, 28 px text | 28 x 700 / 1200 | 16.3 px |
| Same SVG, 24 px text | 24 x 700 / 1200 | 14.0 px |
| Same SVG, 22 px text | 22 x 700 / 1200 | 12.8 px (captions only) |
| Hand-drawn SVG 2800 wide, 20 px text | 20 x 700 / 2800 | 5 px (illegible) |
| Mermaid class diagram, natural width 639 px, 20 px text | 20 x 700 / 639 | 21.9 px |
| Mermaid flowchart, natural width 1385 px, 20 px text (even when the renderer shrank the PNG to 1568 px) | 20 x 700 / 1385 | 10.1 px (fails) |

- With a 20 px source font at 2x (40 px in the PNG) a 700 px column keeps text at 14 px or more up to a 2000 px wide PNG and at 16 px or more up to 1750 px; a diagram near 2000 px wide is borderline, and a wider one fails.
- Re-rendering at a higher scale does not change the result, because text and image width scale together. A diagram that fails on legibility is re-laid out (fewer nodes, split, fan out instead of a long chain, larger source font), never just re-exported bigger.
- Measure the real destination instead of trusting a remembered number: open the published page and read the rendered `<img>` width in CSS pixels (`getBoundingClientRect().width`). A long-form article column measured about 700 px.
- Some renderers fit a diagram into a page width and shrink its text silently (Mermaid CLI fits wide flowcharts into its 800 px page unless `-w` is raised). Compute effective text from the source's natural width (the SVG `viewBox` width), or measure the text in the PNG, not from the configured font size alone.

## 2. Thresholds

| Check | Pass |
| --- | --- |
| Effective text | 14 px floor, 16 px or more as the target, for every label that carries meaning |
| Aspect ratio (W:H) | between 2:1 (wide) and 1:1.6 (tall); no long strips |
| Margin | uniform white margin on every side, about 48 px at 2x render scale (24 CSS px; scale it with the render scale); no box, label, or arrow touches or crosses an edge |
| Resolution | the floors in `image-quality-gate.md` (2x the displayed size; 2000 or 3000 px on the longest side); when a narrow diagram falls under the floor, raise the render scale (for example 3x), which does not change legibility |
| Palette | only the project's palette; one colour per role |
| Edge weights | thick, thin, and dashed lines each mean one thing and are used consistently |
| Fidelity | rendered from the current source, in the single environment the validator inspected |

## 3. Producer pre-checks (mechanical, cheap)

Run these before asking for visual QA. A failing pre-check goes straight back to the producer; a passing one only earns a visual check. Dimensions, aspect ratio, effective text, and the renderer-shrink test need no image library: read width and height from the PNG header, as `skills/diagram-authoring/references/diagram-export-quality.md` prefers.

```python
import struct

def png_size(path):
    """Width and height from the PNG header (no image library needed)."""
    with open(path, "rb") as f:
        head = f.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{path} is not a PNG")
    return struct.unpack(">II", head[16:24])

def precheck(png, natural_width, font_px=20, scale=2, pad=48, column=700):
    """natural_width: viewBox width of the SVG source or export.
    pad: margin actually added to the file (0 for raw renderer output)."""
    w, h = png_size(png)
    return {
        "size": (w, h),
        "aspect_ok": 0.625 <= w / h <= 2.0,                   # 2:1 wide .. 1:1.6 tall
        "text_px_at_column": round(font_px * column / natural_width, 1),
        "shrunk_by_renderer": w < 0.95 * (natural_width * scale + 2 * pad),
    }
```

The margin check needs pixel access, so it is the one optional, Pillow-only step (skip it and rely on the validator's visual check if Pillow is not installed). A blank image has no content box, so guard for `None`:

```python
def margins(png):
    """Optional (needs Pillow): (left, top, right, bottom) white margin in px, or None for a blank image."""
    from PIL import Image, ImageChops
    im = Image.open(png).convert("RGB")
    box = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    if box is None:
        return None
    left, top, right, bottom = box
    return (left, top, im.width - right, im.height - bottom)
```

Pass when `min(margins(png))` is at least the margin threshold in section 2 (48 px at 2x).

Measured in sandbox renders with mermaid-cli 11.16 and headless Chromium 141 on 2026-10-07 (indicative, not universal): raw `mmdc` output had small margins, often under 35 px, so it fails the margin check until padded; a 7-node top-to-bottom chain was 608x1436 (fails `aspect_ok`); a wide left-to-right flowchart was squeezed to 1568x226 with `shrunk_by_renderer` true and 10.1 px effective text; a hand-authored 1200x900 SVG rendered with a browser at 2x had margins of 56 and 53 px and 14.0 px effective text for 24 px source text.

For SVG sources also parse them as XML and grep for `foreignObject`, `<image`, `<script`, `@import`, `href="http`; and check the bottom margin of the PNG, because a browser screenshot taken with a mismatched window size can cut off the lower edge of the drawing.

## 4. Independent visual validator

The validator is a different agent or person from the producer: a producer reviewing its own render tends to see what it intended. Give the validator the PNG paths, the destination width, the thresholds above, and the palette, but not the producer's verdict. Checking labels and arrows against the source is a separate content check (see the gate).

For each image the validator opens the actual PNG at the destination width (downscale a copy to the column width and look at it) and reports one line: file, size, aspect ratio, estimated effective text, margins, verdict PASS or FAIL, defect names.

Defects the validator must catch:

| Defect | Typical cause | Fix at the source |
| --- | --- | --- |
| Illegible strip (very wide, tiny text) | long left-to-right chain, renderer shrink | fan out or fold ranks, split the diagram, raise the renderer page width |
| Too-tall flowchart | long top-to-bottom chain | fan out, two columns, or split |
| Clipped label ends | font in the source missing in the viewer or renderer (mis-measured text) | use a safe font stack in committed sources; install the render font |
| Box, label, or arrow touching or cut by an edge | no margin, cropped screenshot | add the uniform margin; fix the viewport |
| Empty class compartments | classes with only methods or only attributes | give every class at least one attribute and one method |
| Label patches on thick edges (a grey or white block interrupting a line) | edge label background differs from the canvas | match the label background to the canvas; avoid labels on thick edges |
| Inconsistent edge weights | thick lines used without a meaning | one weight per meaning (main path thick, rest thin, configuration dashed) |
| Colours outside the palette | ad hoc fills or strokes | replace with the role colours |
| Overlapping text, arrow through a label | dense layout | spacing, fewer nodes, split |
| Text below the effective-size floor | wide diagram, small source font | split or enlarge text; do not export bigger |

## 5. Iterate until pass

1. Producer renders every image in one environment and runs the pre-checks.
2. Validator inspects every image and returns the table.
3. Producer fixes the source for each FAIL (never patches the PNG), re-renders in the same environment, and reruns the pre-checks.
4. Validator re-inspects every image whose source changed, and every image if a shared style element (init line, palette, margin, render settings) changed.
5. Stop when every image is PASS. If the same defect survives three rounds, change the layout (split or restructure) instead of tuning spacing.
6. Report per `image-quality-gate.md`: artifacts inspected, validator identity, fixes, residual blockers.

Related: `skills/diagram-authoring/references/publication-diagram-style.md` (the style these thresholds were derived from) and `skills/diagram-authoring/references/diagram-export-quality.md`.
