---
title: High-resolution diagram export standard
tags: [diagrams, export, resolution, plantuml, mermaid, svg, png, pdf]
---

# High-resolution diagram export standard

Use this reference whenever a diagram is rendered, attached, committed, exported to PDF, or uploaded to a wiki. The inspection contract lives in `skills/image-quality-inspection/references/image-quality-gate.md` and applies to 100% of generated/exported image artifacts.

Post-export quality control is mandatory. A diagram is incomplete until every exported image, including PNG outputs, has been opened in a real viewer or rendered in its final document/wiki/PDF context and accepted.

## Default output choice

- Prefer vector output (`.svg` or `.pdf`) for generated diagrams whenever the destination supports it. Vector output is the default high-resolution path.
- Use raster output (`.png` or `.jpg`) only when the target system requires it.
- Never upscale a low-resolution raster image as the primary quality fix. Re-render from source at the required size or switch to vector output.

## Raster minimum

When PNG/JPG is required:

- Render at 2x or higher than the final display size.
- Target at least 2000 px on the longest side for small/simple diagrams.
- Target at least 3000 px on the longest side for C4 component, AWS architecture, or large sequence diagrams.
- Use 300 DPI or renderer scale 2+ when the renderer supports those controls.
- Verify actual image dimensions before committing or attaching raster output.
- Check dimensions programmatically and treat output below the minimum as a failed export. Run this check before visual inspection, not as a substitute for it.
- Verify raster dimensions from the file header or an existing CLI tool (for PNG, width and height are the big-endian 32-bit integers at bytes 16-24; ImageMagick `identify` or `file` also work) instead of adding an image-library dependency for the check.
- Open and inspect the actual raster artifact after export. If it cannot be inspected, report it as a blocker.

## PlantUML

- Validate syntax first, then export.
- When a script or subprocess invokes the renderer with a changed working directory (for example `subprocess.run(..., cwd=...)`), pass only absolute source and output paths. Relative path arguments are re-interpreted against the child's working directory and fail with `No file found` (exit code 50) even though the sources exist. Resolve every path to absolute before building the command, or drop the `cwd=` change and pass `-o <absolute output dir>` instead.
- Use `-DPLANTUML_LIMIT_SIZE=32768` for wide or detailed diagrams.
- Prefer SVG for docs and wiki attachments:

```bash
java -DPLANTUML_SECURITY_PROFILE=INTERNET -DPLANTUML_LIMIT_SIZE=32768 -jar "$PLANTUML_JAR" -tsvg docs/architecture/*.puml
```

- If PNG is required, set a high DPI in source or renderer config when the project permits it:

```plantuml
skinparam dpi 300
```

- If a rendered PNG falls below the raster minimum, raise `skinparam dpi` in the source (for example 150 to 200 or 300) and re-export; never resize the undersized PNG.

## Mermaid

- Prefer Mermaid CLI SVG export for committed or PDF-bound artifacts:

```bash
mmdc -i diagram.mmd -o diagram.svg
```

- If PNG is required, render with a local renderer that exposes explicit width/scale controls, then verify dimensions.
- Kroki is acceptable for Markdown/PDF conversion, but Mermaid PNG scale options are not portable across renderers. Prefer Kroki SVG or a local Mermaid CLI export for high-resolution output.

## Wiki and PDF outputs

- For Confluence or other wikis, attach or embed SVG/PDF when the platform and security policy allow it. Otherwise upload high-resolution PNG generated from source.
- When a wiki page embeds attachments by filename (Confluence `ri:attachment ri:filename`), upgrade diagrams by uploading new attachment versions under the exact same names: every embedded render updates with zero body edits. Make the publisher fail when an expected name is absent instead of silently creating a new attachment name the body never references, and verify each attachment's version number advanced after upload.
- For Markdown-to-PDF, keep diagram source in Markdown and render image intermediates as SVG by default. Use PNG only when the PDF toolchain or destination rejects SVG.
- Re-open the final PDF/wiki page and inspect the embedded diagram, not just the intermediate file.
- When the destination enforces content gates (for example forbidden identifier patterns or stale run/version labels), read the published page or attachment back after publishing and fail the publish step on any gate violation instead of trusting the upload response.

## Completion gate

Before reporting completion:

- The source diagram validated with the repository's renderer.
- Any generated artifact was produced from current source.
- Raster artifacts meet the minimum dimensions above.
- The rendered diagram was visually inspected after export at the target documentation size; this step is not optional.
- Every generated/exported diagram image and final embedded render passed the image-quality inspection gate.
- Low-resolution, blurry, cropped, or downsampled output was re-rendered or replaced with vector output.
