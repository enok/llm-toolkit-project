---
title: Publication diagram style
tags: [diagrams, mermaid, svg, publication, github, readme, article, palette, class-diagram, sequence, flowchart, hexagonal, ports-and-adapters]
---

# Publication diagram style

Use this reference for teaching and explainer diagrams that are read in a GitHub README and as a PNG inside an article or social post: class, sequence, and flowchart views of a pattern, a use case, or a small design. The look is reference-driven: white canvas, flat saturated fills, one hue per role, dark borders, UML-style compartments, written relationship labels.

Scope. Architecture views (C4 component, AWS topology, runtime sequence for a system) keep following `deterministic-diagram-system.md`, including its 5-colour gate. This profile is a repo-level theme standard for publication diagrams: a single diagram uses only the roles it needs (usually 3-5), never a colour outside the table below. Export and inspection gates from `diagram-export-quality.md` and `skills/image-quality-inspection/references/image-quality-gate.md` still apply; judge the final PNG at its destination width with `skills/image-quality-inspection/references/destination-legibility.md`.

## 1. Init line

Every `.mmd` source starts with exactly this one line (copy verbatim).

```text
%%{init: {"theme": "base", "themeVariables": {"fontFamily": "Arial, Helvetica, sans-serif", "fontSize": "20px", "background": "#FFFFFF", "primaryColor": "#FFFFFF", "primaryBorderColor": "#1B1F23", "primaryTextColor": "#1B1F23", "secondaryColor": "#FDDCB5", "tertiaryColor": "#F5F7FA", "lineColor": "#3D4650", "textColor": "#1B1F23", "mainBkg": "#FFFFFF", "nodeBorder": "#1B1F23", "clusterBkg": "#F5F7FA", "clusterBorder": "#9AA5B1", "edgeLabelBackground": "#FFFFFF", "noteBkgColor": "#FFF6D6", "noteBorderColor": "#B8860B", "noteTextColor": "#1B1F23", "actorBkg": "#B8E2B4", "actorBorder": "#2F6B35", "actorTextColor": "#1B1F23", "actorLineColor": "#7A8794", "signalColor": "#3D4650", "signalTextColor": "#1B1F23", "labelBoxBkgColor": "#F5F7FA", "labelBoxBorderColor": "#7A8794", "labelTextColor": "#1B1F23", "loopTextColor": "#1B1F23", "activationBkgColor": "#DDEFDB", "activationBorderColor": "#2F6B35", "sequenceNumberColor": "#FFFFFF", "classText": "#1B1F23"}, "flowchart": {"curve": "linear", "nodeSpacing": 50, "rankSpacing": 60, "padding": 16, "htmlLabels": false}, "sequence": {"actorMargin": 50, "messageMargin": 38, "boxMargin": 10, "noteMargin": 10, "mirrorActors": false, "useMaxWidth": false}, "class": {"padding": 12, "htmlLabels": false}, "fontFamily": "Arial, Helvetica, sans-serif"}}%%
```

- Font: the committed source says Arial. GitHub's viewer clipped the last characters of every label when the init named a font viewers do not have (Mermaid measured the fallback wrongly). Put a nicer font in only at PNG render time (section 8). `fontFamily` appears twice; a render-time swap must replace both.
- Text size: `fontSize` 20px is the floor; never lower it and never use `<small>` or tiny labels. `htmlLabels: false` keeps labels as SVG text, which survives GitHub and PNG export.
- Text colour is always `#1B1F23`; the canvas is white (`-b white` when rendering).

## 2. Role palette

Use these names and values exactly. A role is a meaning, not a decoration.

| Role | Meaning | Fill | Stroke |
| --- | --- | --- | --- |
| `context` | Owner: Context, use case, the object that holds the abstraction | `#B8E2B4` | `#2F6B35` |
| `strategy` | Abstraction: interface, strategy, port | `#FDDCB5` | `#B35C0F` |
| `concrete` | Implementers: concrete strategies, adapters | `#F7B267` | `#B35C0F` |
| `adhoc` | Lambda or function implementers, experiments (dashed) | `#FFF1D6` | `#B35C0F` |
| `data` | Value objects, configuration, stores | `#BBDDF7` | `#1F5FA8` |
| `external` | Systems outside the boundary (dashed) | `#FFFFFF` | `#3D4650` |
| `danger` | Fallback, error, breaker open | `#F9C5C0` | `#A5222B` |
| `client` | Callers | `#FFFFFF` | `#1B1F23` |

```text
classDef context fill:#B8E2B4,stroke:#2F6B35,stroke-width:2.5px,color:#1B1F23
classDef strategy fill:#FDDCB5,stroke:#B35C0F,stroke-width:2.5px,color:#1B1F23
classDef concrete fill:#F7B267,stroke:#B35C0F,stroke-width:2.5px,color:#1B1F23
classDef adhoc fill:#FFF1D6,stroke:#B35C0F,stroke-width:2.5px,stroke-dasharray:6 4,color:#1B1F23
classDef data fill:#BBDDF7,stroke:#1F5FA8,stroke-width:2.5px,color:#1B1F23
classDef external fill:#FFFFFF,stroke:#3D4650,stroke-width:2px,stroke-dasharray:6 4,color:#1B1F23
classDef danger fill:#F9C5C0,stroke:#A5222B,stroke-width:2.5px,color:#1B1F23
classDef client fill:#FFFFFF,stroke:#1B1F23,stroke-width:2.5px,color:#1B1F23
```

Subgraph panels: `style SG fill:#F5F7FA,stroke:#7A8794,stroke-width:2px,stroke-dasharray:8 5` (dashed grey group outline). Add a one-line colour key under every class diagram in the surrounding Markdown, for example `Green = context, light orange = abstraction, orange = implementers, blue = data, white dashed = external, red = failure`.

## 3. Grammar per diagram type

Verified with mermaid-cli 11.16: all three grammars below render with the init line and palette above.

### classDiagram

- Colour with one `style ClassName <fill/stroke/stroke-width/stroke-dasharray from the palette>` line per class; omit `color:`. `cssClass` and `class X:::role` did not colour boxes.
- Annotations (`<<interface>>`, `<<lambda>>`) go on their own line inside the class body; on a member line they render as `<>`.
- Keep at most 4 members per class. Mermaid draws an empty attributes compartment when a class has only methods (and an empty methods compartment when it has only attributes), which reads as broken. Give every class at least one attribute and one method, or accept the empty band knowingly.
- Layout: `direction TB`; Client at the top, abstraction in the middle, implementers in one row below.
- Relationships always carry a written label: `Context o-- Strategy : has-a` (aggregation), `Strategy <|.. Concrete : implements` (realisation, dashed), `Child --|> Parent : extends`, `Client ..> Context : uses`, `Client ..> Concrete : creates`, composition `A *-- B : owns`. Add multiplicities (`"1" o-- "*"`) only where they explain something. A `note` is allowed for the one-line idea.

```text
classDiagram
    direction TB
    class Context {
        -strategy Strategy
        +run() Result
    }
    class Strategy {
        <<interface>>
        +execute(input) Result
    }
    Context o-- Strategy : has-a
    style Context fill:#B8E2B4,stroke:#2F6B35,stroke-width:2.5px
    style Strategy fill:#FDDCB5,stroke:#B35C0F,stroke-width:2.5px
```

### sequenceDiagram

- Start with `autonumber`. Participants are plain; they all take the green actor colour from the init. Use short participant ids (avoid `x`/`X` with the `+`/`-` activation shorthand).
- Phases: `rect rgb(245,247,250)` wrapping `Note over A,Z: 1 · Title`, then the calls. Do not combine `box` with `rect` (the rect overdraws the box edge); use one or the other.
- `activate`/`deactivate` (or `+`/`-`) on the object that delegates; solid `->>` calls, dashed `-->>` returns; labels short.

### flowchart

- Apply roles with `class A,B concrete;` plus the `classDef` lines. Shapes carry meaning: rounded `(...)` components, stadium `([...])` start/end and callers, hexagon `{{...}}` ports and interfaces, rhombus `{...}` decisions, cylinder `[(...)]` stores. Quote every label with punctuation: `A["Port: Repository"]`.
- Edge weight carries meaning and nothing else: thick `==>` only for the main request path, thin `-->` for the rest, dashed `-.->` for configuration or "implemented by". Edge labels are role words ("implemented by", "injects", "on error").
- At most about 12 nodes, labels 5 words or fewer (28 characters).
- The shape of the layout decides legibility. Measured in a sandbox render with mermaid-cli 11.16 at scale 2 (2026-10-07): a 7-node chain top-to-bottom rendered 608x1436 (2.4:1, too tall); an 8-node left-to-right layout with a two-way fan-out rendered 1568x226 (6.9:1, a strip whose text was also shrunk by the page-width cap in section 4); a top-to-bottom fan-out (caller, use case, two ports, two adapters, two targets) rendered 846x1140 (1:1.35, passes). Fan out, fold into ranks, or split into two diagrams; do not rely on a subgraph `direction` (ignored when its nodes link outside it).

## 4. Legibility and layout

The thresholds (effective text size, aspect ratio, margin, resolution floor) and their worked numbers live only in `skills/image-quality-inspection/references/destination-legibility.md`; apply them to every PNG and do not copy them here. What this style adds:

- Never lower the init `fontSize` (20px) and never use `<small>` or tiny labels. A diagram too wide to pass the legibility check is split or given fewer participants or nodes, not shrunk.
- Keep node count and label length within the limits in section 3.
- `mmdc` fits diagrams whose `useMaxWidth` is true (the flowchart default) into its page width (`-w`, default 800), so a diagram whose natural width is larger is silently shrunk, text included. Measured in a sandbox render with mermaid-cli 11.16 at scale 2 (2026-10-07): a flowchart with natural width 1385 px came out 1568 px wide; with `-w 2400` it came out 2770 px wide at natural size. A PNG exactly 1568 px wide at scale 2 is the signature of that cap. Pass a large `-w` (section 8), and compute effective text from the SVG's natural `viewBox` width as described in `destination-legibility.md`.
- Pilot sizes from the original run (scale 2, before the margin): class 1568x1256, flowchart 1568x1700, sequence 2032x1490. The two 1568-px widths match the page-width cap above, so their text may have been shrunk; recompute every PNG from its natural width.

## 5. GitHub inline Mermaid compatibility

GitHub renders the inline ` ```mermaid ` blocks, so use only long-standing syntax: the `%%{init}%%` directive, `classDef`, `class`, `style`, `subgraph`, `autonumber`, `box`, `rect`, `Note`, `activate`. `cssClass` parses but does not colour class boxes (section 3). Avoid frontmatter config, the `look:` option, icons or images, HTML labels, `click` callbacks, and beta diagram types.

If the repo keeps `.mmd` files and inline copies, keep them byte-identical and let CI check it (see `skills/multi-language-study-repo/SKILL.md`).

## 6. Ports-and-adapters (hexagonal) views: hand-authored SVG

Mermaid cannot draw a real hexagon core with ports on its edges and adapters outside. Author the view as an SVG source file and render it with headless Chromium. This is the one allowed hand-authored diagram (plain markup committed as the source, not generated by drawing code).

- Valid XML, a `viewBox` (for example `0 0 1200 900`), `<title>` and `<desc>`, a white background `<rect>`.
- No external fonts, images, scripts, `@import`, or `foreignObject`; `font-family="Arial, Helvetica, sans-serif"` on the root.
- Text 22-28 px in a 1200-wide viewBox: 24 px or more for labels that carry meaning, 22 px for non-essential captions only (the effective sizes for this case are in `destination-legibility.md`).
- Same role palette as section 2: core `context`, ports `strategy`, adapters `concrete`, outside systems `external` (dashed). Driving adapters on one side pointing in, driven adapters on the other pointing out.
- Geometry: hexagon with centre (cx, cy) and radius R has vertices at (cx+R, cy), (cx+R/2, cy+0.866R), (cx-R/2, cy+0.866R), (cx-R, cy), (cx-R/2, cy-0.866R), (cx+R/2, cy-0.866R). Centre each port rectangle on an edge midpoint so it straddles the edge. Keep at least 28 px between every shape and the viewBox edge (56 px at 2x render scale; the margin threshold is in `destination-legibility.md`).
- Arrowheads: `markerUnits="userSpaceOnUse"` with a fixed size; the default scales with stroke width and gives oversized heads.

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 900" width="1200" height="900"
     role="img" aria-labelledby="t d" font-family="Arial, Helvetica, sans-serif">
  <title id="t">Ports and adapters</title>
  <desc id="d">Application core as a hexagon; ports on its edges; adapters and external systems outside.</desc>
  <defs>
    <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse"
            markerWidth="20" markerHeight="20" orient="auto">
      <path d="M0,0 L10,5 L0,10 z" fill="#3D4650"/>
    </marker>
  </defs>
  <rect width="1200" height="900" fill="#FFFFFF"/>
  <polygon points="870,450 735,683.8 465,683.8 330,450 465,216.2 735,216.2"
           fill="#B8E2B4" stroke="#2F6B35" stroke-width="5" stroke-linejoin="round"/>
  <text x="600" y="440" text-anchor="middle" font-size="30" font-weight="700" fill="#1B1F23">Application core</text>
  <!-- port on the upper-left edge (centred on its midpoint 397,333) -->
  <rect x="302" y="301" width="190" height="64" rx="12" fill="#FDDCB5" stroke="#B35C0F" stroke-width="4"/>
  <text x="397" y="342" text-anchor="middle" font-size="24" fill="#1B1F23">Command port</text>
  <!-- adapter and outside system, with arrows pointing into the core -->
  <rect x="30" y="278" width="190" height="110" rx="14" fill="#F7B267" stroke="#B35C0F" stroke-width="4"/>
  <text x="125" y="326" text-anchor="middle" font-size="26" fill="#1B1F23">Web</text>
  <text x="125" y="358" text-anchor="middle" font-size="26" fill="#1B1F23">adapter</text>
  <rect x="30" y="28" width="190" height="80" rx="10" fill="#FFFFFF" stroke="#3D4650" stroke-width="3" stroke-dasharray="10 6"/>
  <text x="125" y="77" text-anchor="middle" font-size="26" fill="#1B1F23">Browser</text>
  <g stroke="#3D4650" stroke-width="4" fill="none" marker-end="url(#arrow)">
    <path d="M125,108 V274"/>
    <path d="M220,333 H298"/>
  </g>
</svg>
```

Repeat the port, adapter, outside-system and arrow groups for the other three corners (mirror the right side with outward arrows); the full 4-port view renders cleanly at 1200x900.

Render with a browser at an explicit viewport and scale (Playwright shown; any headless Chromium driver that sets the viewport works):

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1200, "height": 900}, device_scale_factor=2)
    pg.goto("file:///abs/path/view.svg")
    pg.screenshot(path="view.png")
    b.close()
```

Do not use `chrome --headless --screenshot --window-size=W,H` for this: in a sandbox render with Chromium 141 (2026-10-07) the captured viewport was shorter than the window and the bottom of the drawing (about 90 px at 1x) was cut off. Always confirm the PNG's bottom margin is intact (`destination-legibility.md`, pre-checks). Validate the source before rendering: parse it as XML and grep for `foreignObject`, `<image`, `<script`, `@import`, `href="http`.

## 7. Pilot first

Before restyling a whole set, render 2-3 pilots (one class, one sequence, one flowchart or SVG) and show them to the user. Apply the style to the full set only after the user accepts the pilots; a rejected style costs three diagrams, not thirty. Keep the pilot sources: they become the templates.

## 8. Optional render step (PNG for articles and social posts)

Mermaid sources stay on the safe font. The render step makes a temp copy with the nicer font, renders at scale 2, and adds a uniform white margin, because `mmdc` crops tightly (margins were small and variable, often under 35 px, in sandbox renders with mermaid-cli 11.16 on 2026-10-07). Post-processing a raster this way is allowed; authoring diagrams with drawing code is not. The only image-library use is adding the margin, and it is optional: Pillow if installed, otherwise ImageMagick. Reading dimensions needs neither (`destination-legibility.md` has a header-read helper).

```python
import shutil, subprocess, sys, tempfile
from pathlib import Path

SAFE = '"fontFamily": "Arial, Helvetica, sans-serif"'
NICE = '"fontFamily": "Inter, Arial, sans-serif"'   # only if installed where you render


def render(src: Path, scale: int = 2, extra=()) -> Path:
    text = src.read_text(encoding="utf-8").replace(SAFE, NICE)   # replaces both occurrences
    out = src.with_suffix(".png")
    with tempfile.TemporaryDirectory() as tmp:
        tmp_src = Path(tmp) / src.name
        tmp_src.write_text(text, encoding="utf-8")
        subprocess.run(["mmdc", "-i", str(tmp_src), "-o", str(out), "-b", "white", "-w", "2400",
                        "-s", str(scale), "-q", *extra], check=True)
    return out


def add_margin(png: Path, pad: int = 48) -> None:
    """Uniform white border: Pillow if installed, otherwise ImageMagick (`magick` v7, `convert` v6)."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        tool = shutil.which("magick") or shutil.which("convert")
        if tool is None:
            raise SystemExit("add the margin with Pillow or ImageMagick")
        subprocess.run([tool, str(png), "-bordercolor", "white", "-border", str(pad), str(png)], check=True)
        return
    ImageOps.expand(Image.open(png).convert("RGB"), border=pad, fill="white").save(png, optimize=True)


if __name__ == "__main__":
    for p in sorted(Path(sys.argv[1]).glob("*.mmd")):
        out = render(p, extra=sys.argv[2:])
        add_margin(out)
        print(out.name)
```

- `-w 2400` stops `mmdc` from shrinking wide diagrams to its 800 px page; narrow diagrams are unaffected (measured in a sandbox render with mermaid-cli 11.16, 2026-10-07: a class diagram came out 734x964 with a 48 px margin, with and without it).
- The step is idempotent (the render overwrites the PNG before the margin is added), so re-running does not stack margins. The Pillow path and the ImageMagick 6 (`convert`) path were both run and gave the same dimensions; the ImageMagick 7 `magick` spelling takes the same arguments but was not run.
- Confirm the swapped font exists where you render (`fc-list | grep -i <font>`); if it does not, the fallback is mis-measured exactly as on GitHub and labels clip in the PNG.
- When the longest side is under the 2000 px floor of the image-quality gate, render at `-s 3` (and pad 72). Legibility does not change with scale (see `destination-legibility.md`); only sharpness improves.
- In a container or as root, pass a puppeteer config through `extra` (`-p puppeteer.json` with `--no-sandbox` and, if the bundled browser is missing, `executablePath`).
- Render all publication PNGs in one environment and commit those files; hand them to an independent validator before use.
