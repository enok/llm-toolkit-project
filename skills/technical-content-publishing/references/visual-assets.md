---
title: Visual assets for technical content
tags: [cover-image, diagram, carousel, playwright, chromium, html-to-pdf, image-quality, privacy]
---

# Visual assets for technical content

Companion to `skills/technical-content-publishing/SKILL.md`. Covers the cover image, the hero architecture diagram, carousel slides, a portable render path, and inspection. Platform values come from `references/medium-article.md` and `references/linkedin-post-and-carousel.md` (verified 2026-10-01).

Reuse, do not duplicate:

- `skills/diagram-authoring` - diagram type, deterministic style, source-of-truth rules, SVG/PNG export.
- `skills/markdown-pdf-export` - only if a PDF of the article itself is requested.

## Asset list

| Asset | Spec | Basis |
| --- | --- | --- |
| Cover image (`visuals/cover.png`) | 1600x900 CSS px (16:9) rendered at 2x = 3200x1800 PNG; text 34 CSS px or more at 1600 px width, inside the central safe area (see Design guidance) | Medium: PNG/JPG up to 25 MB, at least 1192-1200 px wide (primary); crop and focal behaviour not specified, so keep the centre safe (toolkit choice) |
| Link-preview variant | 1200x627 (1.91:1), under 5 MB, centre-safe. Only needed when the human shares a URL whose `og:image` they control | third-party values, see LinkedIn reference |
| Hero diagram | One diagram, 9-10 nodes at most, labels of 4 words or fewer, landscape; SVG source plus PNG at 2000 px or more on the longest side (3000 px for dense diagrams) | `skills/diagram-authoring/references/diagram-export-quality.md` |
| Carousel slides | 1080x1350 px (4:5), one HTML section per slide, PDF plus PNG per slide | LinkedIn reference |
| Alt text | One sentence per image in `alt-text.md` | Medium and LinkedIn both support alt text |

Deliver PNG or JPG to Medium (WebP and SVG are not in its supported list). Keep the SVG as the diagram source.

## Design guidance

Cover image:

- Title-led: the claim or title is the picture. One accent colour plus neutrals; a high-contrast palette (body-size text at 4.5:1 or better).
- Keep all text inside the central safe area (roughly the middle 80% of width and 70% of height) so platform crops and feed thumbnails do not cut it. Medium's crop and focal behaviour is not specified, and LinkedIn center-crops link previews to 1.91:1.
- Text 34 CSS px or more at 1600 px canvas width (about 2% of the width); at most about 12 words.
- No vendor logos, trademarks, employer branding, or people.

Diagram:

- 9-10 nodes at most per image; landscape aspect so it fits an article column.
- Label height at least about 2% of the image width, so labels still read at a roughly 700 px column width (14 px at 700 px).
- If the flow needs more nodes, split it into separate diagrams (for example a control-plane view and a per-task detail view), each with its own caption, rather than shrinking text.

## Design rules

- One accent colour plus neutrals; light background for diagrams, dark or light for slides, but one theme per set.
- Fonts: system stack or fonts available locally or embedded. Do not hotlink web fonts or load remote assets; offline runs must render the same and no request should leak the author's activity.
- Type floors for slides at 1080 px wide: headline 72 px or more, body 40 px or more, code 32 px or more, footer 24 px or more; margins 96 px; body contrast at least 4.5:1; never colour alone for meaning.
- Charts: plot only fact-sheet numbers; label axes and units; start bars at zero; cite the source tag in the footer. No decorative charts.
- Code on slides: real snippets from the pinned ref, 8 lines at most, monospace, redacted of any private detail.
- Diagram nodes: each node must map to a path in the source (`skills/diagram-authoring`). If a carousel needs a simpler version, edit the diagram source and re-render with larger text; never retouch a PNG.
- No stock photos of people, trademarked logos, employer branding, real user interfaces that show names, or screenshots of private tools.
- Generative imagery is optional. Avoid text inside generated images; disclose per the target platform's policy (Medium asks for a caption note); do not strip embedded provenance metadata.

## Portable render path (HTML to PNG and PDF)

Needs only Python and a Chromium build that Playwright can launch, on Windows, macOS, or Linux; the Poppler checks later in this file are used when present and have fallbacks. If no browser is installed, use the environment's approved install route; do not guess one. A Node Playwright script follows the same steps. Prefer `pathlib` and `Path.as_uri()` for paths.

Slide skeleton (`carousel/slides.html`): every page the same size, one `.slide` per page, `<title>` neutral (Chromium uses it as the PDF title). Leave the page marker as `<span class="pg">n/N</span>`; the renderer replaces it with the real `n/N`, so the footer never disagrees with the slide count.

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Neutral deck title</title>
<style>
  @page { size: 1080px 1350px; margin: 0 }
  :root { --bg:#0b1020; --fg:#f4f6fb; --muted:#aab3c8; --accent:#5eead4; }
  html, body { margin:0; background:var(--bg); }
  .slide { width:1080px; height:1350px; box-sizing:border-box; padding:96px; overflow:hidden;
           position:relative; display:flex; flex-direction:column; justify-content:center; gap:32px;
           break-after:page; page-break-after:always; color:var(--fg);
           font:40px/1.3 system-ui, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
  .slide:last-child { break-after:auto; page-break-after:auto; }
  h1 { font-size:88px; line-height:1.05; margin:0; }
  .kicker { color:var(--accent); font-size:32px; letter-spacing:.08em; text-transform:uppercase; }
  pre { font:32px/1.35 ui-monospace, Consolas, Menlo, monospace; background:#141a30; padding:32px; border-radius:16px; white-space:pre-wrap; }
  .foot { position:absolute; left:96px; right:96px; bottom:48px; color:var(--muted); font-size:24px; display:flex; justify-content:space-between; }
</style></head><body>
  <section class="slide"><div class="kicker">Topic</div><h1>The claim, in about ten words</h1><p>One-line subtitle</p><div class="foot"><span>path @ ref</span><span class="pg">n/N</span></div></section>
  <!-- one <section class="slide"> per slide; max ~35 words each -->
</body></html>
```

Renderer: `scripts/render_assets.py` (tested with Playwright for Python and Chromium; run it as a script rather than retyping it, so every run applies the same overflow check and `n/N` fill). It needs only the HTML source and an output folder:

```bash
python3 <skill-dir>/scripts/render_assets.py slides carousel/slides.html carousel <slug>   # PDF + slide-NN.png, exit 1 on overflow
python3 <skill-dir>/scripts/render_assets.py cover visuals/cover.html visuals              # cover.png at 1600x900
```

Notes from a tested run: slides at 1080x1350 produced a PDF with one identical page size per page and 2160x2700 PNGs; the footer markers became `1/N` ... `N/N`; a deliberately overflowing slide made the script exit with code 1. The cover at 1600x900 with scale 2 produced 3200x1800. 1080x1350 px at 96 dpi is nominally 810 x 1012.5 pt; Chromium rounded the height (reported as 1013.04 pt), so check that all pages are identical and within about 1 pt of nominal, not for exact equality.

Browser-CLI alternative when Python is unavailable (add `--no-sandbox` only inside containers; replace `chrome` with the local Chromium or Chrome executable). It does not run the overflow check or fill the `n/N` markers, so set those by hand and check overflow visually:

```bash
chrome --headless=new --hide-scrollbars --force-device-scale-factor=2 --window-size=1600,900 --screenshot=cover.png "file:///abs/path/cover.html"
chrome --headless=new --no-pdf-header-footer --print-to-pdf=deck.pdf "file:///abs/path/slides.html"
```

Diagram: author and compile the source with `skills/diagram-authoring`, export SVG, then either export PNG per its rules or inline the SVG into the slide HTML. Keep one source for article and carousel versions.

## Inspection and privacy gate

1. Run mechanical checks first: PNG dimensions from the file header (or `identify`/`file`); page count and uniform page size with `pdfinfo -f 1 -l <N>` when present, else the stdlib fallback below; `pdffonts` for embedded fonts and `pdftotext` for selectable text in reading order when present; file sizes under the platform limits.
2. Inspect 100% of generated images and every rendered PDF page (`pdftoppm -r 80 -png`) in a real viewer: sharp, uncropped, undistorted, legible at the destination size, current. This gate blocks. View carousel pages at phone width. Fix at the source (HTML, diagram source, export flags) and re-render; never retouch an output.
3. If a tool or viewer is unavailable, report that check as not run, with the exact blocker; never as passed. Fallbacks: without `pdftoppm`, inspect the per-slide PNGs and open the PDF in any PDF viewer; without `pdftotext`, use `pypdf` if installed.
4. Privacy sweep on the rendered artifacts: visible text, alt text, filenames, PDF properties (Title set neutrally; no author or local path), and image metadata (strip camera or location EXIF; keep provenance metadata on AI-generated images). Terminal or editor captures must not show usernames, hostnames, absolute home paths, or tokens.
5. Log in `HANDOFF.md`: artifact, dimensions, checks run, fixes made, remaining blockers.

Python-stdlib page-size fallback (reads `/MediaBox` entries; works on Chromium output, where page objects are uncompressed; if it finds no pages, use a PDF viewer or `pypdf`):

```python
import re, sys
data = open(sys.argv[1], "rb").read()
boxes = re.findall(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s*\]", data)
sizes = [(round(float(x2) - float(x1), 2), round(float(y2) - float(y1), 2)) for x1, y1, x2, y2 in boxes]
print(len(sizes), "pages;", "uniform" if len(set(sizes)) == 1 else "MIXED", sorted(set(sizes)))
```

## Related

- For a narrated video built from a storyboard (JSON scenes, one audio file per beat, rendered with captions), see [storyboard-to-video-pipeline-design-notes](../../../learnings/storyboard-to-video-pipeline-design-notes.md). Design notes only: the scripts are not in the toolkit.
