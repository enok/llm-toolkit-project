---
description: Generate and verify Jira-ready PDFs from Markdown source files
---

# Markdown → PDF Export Workflow

**Goal:** Convert Markdown documents to PDFs and verify they contain the expected content.

## Preconditions

- **Pandoc** installed and on PATH
- **Typst** on PATH (for architecture/diagram PDFs with Mermaid pre-render)
- **Google Chrome** available for headless HTML-to-PDF printing
- **Python 3** on PATH (for verification scripts)
- Use the reusable helper scripts from the toolkit `scripts/` directory. Do not
  commit copied helper scripts into a consumer repo unless that repo explicitly
  owns a local wrapper or checks config.

## Phase 1 — Full automated cycle

1. Open terminal at repo root.
2. Run the project's PDF cycle script (e.g., `python scripts/pdf_cycle.py`).
3. Optional: `--verify-only` to check existing PDFs without rebuilding.

**Success:** Process exits `0` and reports all checks passed.

**Failure:** Note the failing artifact; fix source Markdown, tooling, or verification thresholds in the checks config, then re-run.

## Phase 2 — Manual single-document builds (when debugging)

**Table-heavy docs (non-Mermaid):**

```powershell
<toolkit>\scripts\md-to-pdf-via-html.ps1 `
  -MarkdownPath ".\path\to\source.md" `
  -PdfOut ".\path\to\output.pdf" `
  -Title "Document Title"
```

Add `-Portrait` for portrait-orientation output.
Do not print `file:///` HTML directly with Chrome. Use this helper so HTML is
served from `127.0.0.1` and Chrome runs with `--no-pdf-header-footer`; otherwise
browser print footers can leak the local machine path into Jira-facing PDFs.

**Architecture / diagram docs (Mermaid):**

```powershell
<toolkit>\scripts\render-mermaid-in-markdown-for-pdf.ps1 `
  -MarkdownPath ".\path\to\architecture.md" `
  -OutputMarkdownPath ".\path\to\architecture-for-pdf.md" `
  -ImageFormat svg `
  -PdfOut "architecture.pdf" `
  -PdfTitle "Architecture Diagram"
```

Use SVG intermediates by default. Use `-ImageFormat png` only when the target toolchain rejects SVG, then verify the PNG dimensions and inspect the actual exported PNG before sharing.

## Phase 3 — Image/render quality gate

When the build creates or embeds images, apply `skills/image-quality-inspection/references/image-quality-gate.md` before sharing. This phase is mandatory, not optional:

1. Inspect 100% of generated SVG/PNG/JPG/WebP intermediates.
2. Open or render the final PDF pages that contain generated images.
3. Verify sharpness, crop, text readability, scaling, and source freshness in the final PDF context.
4. If any image or page render is unacceptable, fix Markdown, diagram source, layout, or export settings, then rebuild and inspect again.
5. If any image or page render cannot be inspected, stop and report the artifact as a blocker.

**Success:** Every generated/exported image and final PDF page containing it is acceptable.

**Failure:** Report the exact artifact, quality issue, and next remediation step. Do not claim the PDF is ready.

## Phase 4 — Verify a single PDF

```bash
python <toolkit>/scripts/verify_pdf_content.py path/to/file.pdf \
  --min-bytes 100000 \
  --min-pages 1 \
  --min-text-chars 500 \
  --must-contain "Expected phrase" \
  --must-not-contain "file:///" "C:/Users" "C:\\Users"
```

Thresholds are defined in the project's PDF checks config (e.g., `scripts/pdf-checks.json`).
For Jira/email artifacts, always include forbidden local-path markers in the
verification gate, not only required business-content phrases.
Keep Jira descriptions and comments repo-relative; do not paste workstation
paths beside the attached PDF.

## Phase 5 — Jira attachment replacement

When replacing a Jira-facing PDF, do not leave stale copies with the same name:

1. List current attachments.
2. Upload the regenerated PDF.
3. Delete stale attachment IDs after confirming the new file is present.
4. List attachments again and verify exactly the intended current PDF remains.
5. Verify the Jira description and comments do not contain `file:///`,
   `C:/Users`, `C:\Users`, or other workstation paths.

## Phase 6 — CI / policy (optional)

- Wire `python scripts/pdf_cycle.py --verify-only` into a pipeline **only if** PDFs are committed and runners have Chrome + Pandoc + Typst.
- Otherwise treat PDFs as **human-generated** artifacts; keep **Markdown** as the contract for reviews.

## Related

- Skill: `skills/markdown-pdf-export/SKILL.md`
- Security rule: `skills/markdown-pdf-export/rules/pdf-export-security.md`

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
