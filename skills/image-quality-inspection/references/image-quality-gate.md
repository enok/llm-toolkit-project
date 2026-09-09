---
title: Generated and exported image quality gate
tags: [images, export, quality, screenshots, diagrams, pdf, documents, presentations, confluence]
---

# Generated and exported image quality gate

Use this gate for any image artifact an agent generates, exports, renders, attaches, or embeds. This is a blocking quality gate: sampling is not enough, and the gate is not optional.

If an exported image cannot be inspected in a real viewer or final-render context, the task is not complete. Report the exact artifact and blocker instead of claiming the image is ready.

## Scope

Inspect 100% of generated or exported image artifacts, including:

- AI-generated or AI-edited bitmap images.
- Diagram exports: PNG, JPG, SVG, PDF, WebP, GIF, and diagram images embedded in Markdown, PDFs, or wiki pages.
- Screenshots and browser captures.
- Rendered PDF pages when a PDF contains generated images, or when the page image itself is the deliverable.
- Rendered DOCX, presentation, or spreadsheet pages and slides when image output is created or embedded.
- Confluence or wiki attachments after the platform has processed the upload.
- Temporary image intermediates that feed a final artifact, such as `pdf/mermaid/*.svg`.

## Inspection methods

Use the closest real viewer to the final destination.

| Destination | Inspect with |
| --- | --- |
| Local PNG/JPG/WebP/GIF | An image-viewing tool, the OS image viewer, or a browser preview |
| SVG/PDF diagram | A browser or PDF viewer, or the final document or wiki preview |
| Markdown PDF | Render and open the final PDF page, and inspect any generated image in context |
| DOCX | Render pages to PNG or PDF and inspect pages containing images |
| PPTX | Render slides or a contact sheet and inspect every slide containing images |
| Confluence or wiki | Open or re-read the rendered page after upload |
| Web screenshot | A browser screenshot at the target viewport |

Syntax validation is not visual inspection. Vector output still needs a target-viewer check because fonts, layout, scaling, and embedding can fail after export.

For generated or exported PNG files, quality control must happen after export against the actual PNG artifact, not only against source code, renderer logs, or an intermediate SVG or PDF.

## Pass criteria

An artifact passes only when all applicable checks are true:

- It was generated from the current source or the latest accepted prompt.
- Dimensions are appropriate for the target display or print size.
- Text is readable without zooming beyond the target review size.
- The image is sharp, not pixelated, blurry, smeared, or over-compressed.
- No important content is cropped, clipped, overlapped, hidden, or distorted.
- Aspect ratio, orientation, and transparent edges are correct.
- Colors and contrast remain legible in the final viewer.
- Diagram arrows, labels, grouping, icons, and ordering are accurate.
- Embedded document, PDF, or wiki rendering matches the inspected source artifact.
- The file does not leak local paths, secrets, tokens, personal data, or unexpected metadata visible in the output.

## Mandatory fix loop

When any check fails:

1. Identify whether the failure is source quality, prompt quality, layout density, renderer settings, target-viewer scaling, or stale output.
2. Fix the upstream source, prompt, layout, renderer flags, or output format.
3. Prefer SVG or PDF for diagrams and other line art when the destination supports it.
4. For raster output, re-render from source with a higher DPI, scale, width, or height. Do not upscale a poor raster as the primary fix.
5. Re-export or re-render and inspect the fixed artifact again.
6. Repeat until acceptable, or report the exact blocker and the next concrete remediation step.

## Minimum raster defaults

Use project-specific standards when they are stricter. Otherwise:

- Use at least 2x the final display dimensions.
- Use at least 300 DPI, or renderer scale 2 or greater, for print-oriented artifacts.
- Use at least 2000 px on the longest side for small or simple diagrams.
- Use at least 3000 px on the longest side for C4 component, cloud architecture, large sequence, or dense workflow diagrams.

## Evidence to report

Before closing the task, report a compact image QA summary:

- Artifacts inspected.
- Tool or viewer used for inspection.
- Fixes or re-exports performed.
- Any artifact that could not be inspected, and why.

If no images were generated or exported, say so explicitly.

## External patterns reviewed

This guidance generalizes read-only patterns reviewed from public and local skill sources:

- `anthropics/skills`: high-resolution PDF page rendering and image extraction patterns.
- `VoltAgent/awesome-agent-skills` and `travisvn/awesome-claude-skills`: image-generation, vision, screenshot, and upscaling skill discovery patterns.
- Local document and presentation skills: render-to-PNG or contact-sheet inspection with repeat-until-clean loops.

Do not run downloaded third-party scripts or vendor opaque external content unless `skills/external-skill-intake/SKILL.md` has approved that source and license.
