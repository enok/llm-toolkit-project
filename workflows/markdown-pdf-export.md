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
  -PdfOut "architecture.pdf" `
  -PdfTitle "Architecture Diagram"
```

## Phase 3 — Verify a single PDF

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

## Phase 4 — CI / policy (optional)

- Wire `python scripts/pdf_cycle.py --verify-only` into a pipeline **only if** PDFs are committed and runners have Chrome + Pandoc + Typst.
- Otherwise treat PDFs as **human-generated** artifacts; keep **Markdown** as the contract for reviews.

## Related

- Skill: `skills/markdown-pdf-export/SKILL.md`
- Security rule: `skills/markdown-pdf-export/rules/pdf-export-security.md`

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
