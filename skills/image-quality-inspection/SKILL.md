---
name: image-quality-inspection
description: Inspect every generated or exported image artifact and force a fix-and-rerender loop until quality is acceptable. Use for AI image generation or edits, diagram exports, screenshots, PDF page renders, document or slide renders, wiki attachments, and any PNG/JPG/SVG/PDF/WebP/GIF created or exported by an agent.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Image Quality Inspection

## Non-negotiable rule

100% of generated or exported images must pass quality inspection before completion.

This includes preview images, final assets, diagram exports, rendered document or page images, slide contact sheets, screenshots, wiki attachments, and image intermediates used to build PDFs.

If an image is blurry, cropped, distorted, unreadable, low-resolution, stale, incorrectly transparent, visually misleading, or inconsistent with the request, fix the source, prompt, layout, or export settings and regenerate or re-export. Repeat until acceptable. If a renderer or viewer is unavailable, do not claim the image passed; report the exact blocker and what was structurally checked.

## When to Use

- An agent generated or edited an image, diagram, chart, or screenshot.
- A diagram was exported to PNG, SVG, or PDF for a doc, wiki page, or PR.
- A Markdown, DOCX, or presentation export produced pages or slides containing images.
- A UI verification or design comparison screenshot will be used as review evidence.
- Any image artifact is about to be attached, embedded, published, or declared done.

## Process

1. Inventory every generated or exported image artifact, including intermediates and final embedded renders.
2. Inspect each artifact with a real render path: an image viewer, a browser screenshot, a PDF page render, a document or page render, a slide render, or the target wiki or page preview.
3. Verify source fidelity: current source, request match, no stale output, no accidental prompt drift.
4. Verify visual quality: dimensions, sharpness, crop, text readability, contrast, layout, aspect ratio, alpha and transparent edges, compression, and rendering in the target viewer.
5. Fix failed artifacts by editing the source, prompt, layout, export flags, DPI or scale, or output format. Prefer vector output or a higher DPI or scale when possible.
6. Re-export or re-render every fixed artifact and inspect it again.
7. Report inspection evidence: artifacts checked, fixes made, remaining blockers, and whether any image could not be visually inspected.

## Required references

- Use `references/image-quality-gate.md` for the detailed pass/fail gate.
- For diagram-specific export rules, use `skills/diagram-authoring/references/diagram-export-quality.md`.
- For Markdown-to-PDF image intermediates and final PDF checks, use `workflows/markdown-pdf-export.md`.

## Related skills

| Skill | When |
|-------|------|
| `diagram-authoring` | The artifact is a diagram; author and export it there, then gate it here |
| `diagram-creation-specialist` | A read-only specialist review of diagram content and export quality is needed |
| `documentation-reviewer` | The image is evidence inside documentation that is being reviewed |
| `ui-verify` / `figma-compare` | Browser screenshots that become report or wiki evidence |
| `markdown-pdf-export` | PDF pipelines where image intermediates feed the final document |
