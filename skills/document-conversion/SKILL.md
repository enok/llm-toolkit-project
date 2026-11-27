---
name: document-conversion
description: Create documents and convert between PDF, Word (DOCX), PowerPoint (PPTX), Excel (XLSX), and Markdown with local, vetted Python tools. Use when the user asks to export a thesis or report to PDF, turn course material or a PDF into Markdown for an LLM, build a slide deck or spreadsheet from code, generate a DOCX from Markdown, extract tables from a workbook, put real check boxes over an exported PDF, or fix a conversion that lost formatting or text. Prefer the dedicated pdf, docx, pptx, and xlsx skills when they are installed; use this one for the cross-format glue, offline or scripted runs, and the pitfalls below.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.1.0"
---

# Document Creation and Conversion

Pick the lightest local tool that keeps the structure the reader needs, run it in an isolated environment, and check the output against the source before reporting success.

## Choose the route

| Goal | First choice | Detail |
| --- | --- | --- |
| Any of PDF, DOCX, PPTX, XLSX to Markdown | `scripts/convert_to_markdown.py <file> [out.md]` (PyMuPDF, python-docx, python-pptx or pandas; pinned in `scripts/requirements.txt`, installed by `scripts/setup_document_conversion.sh`; exits 1 when a library is missing) | [conversion-recipes.md](references/conversion-recipes.md): read it when the script is not enough or you need Pandoc, tables, or a single format |
| Markdown to DOCX, PDF, HTML | Pandoc | [conversion-recipes.md](references/conversion-recipes.md) |
| Create a PDF, DOCX, PPTX, XLSX or Markdown file from code | ReportLab or WeasyPrint, python-docx, python-pptx, openpyxl | [creation-recipes.md](references/creation-recipes.md): read it before writing generation code; it has a table of contents |
| Scanned PDF (no text layer) | MinerU with OCR | [conversion-recipes.md](references/conversion-recipes.md) |
| Real check boxes on an exported PDF, table checklists, file-locked PDFs, recalculation pitfalls | Overlay on the exported file | [pdf-checkbox-overlay.md](references/pdf-checkbox-overlay.md): read it before editing a PDF a user exported from a document editor |

Set up the tools once with `bash scripts/setup_document_conversion.sh`; it creates `.venv-docs` and installs the packages used above. Use `python3` where `python` is missing or is a stub (some Windows machines).

## Workflow

1. Identify source and target formats and whether the dedicated format skills are installed; use them first for format-specific editing, because they cover layout details this skill does not.
2. Work in a virtual environment (`.venv-docs`). Why: conversion libraries pull many dependencies, and isolation keeps a bad install from touching the system.
3. Convert or generate with the route above. Keep output next to the source, never overwrite the source.
4. Verify against the source: page, slide, sheet, and table counts; headings and heading order; a spot check of one table and one non-ASCII passage (save and read files as UTF-8). Report a check you could not run as not run.
5. Report the result in this form:

```
Converted: <source> -> <output> using <tool>
Checks: pages/slides/sheets <n> -> <n>; headings <n>; tables <n>; non-ASCII sample ok
Lost or approximated: <images, comments, tracked changes, layout, formulas> or none
```

Worked example. Request: "turn this 40-page course PDF into Markdown for an LLM". Run `python3 scripts/convert_to_markdown.py course.pdf`, confirm 40 pages of text came through, spot-check a table, add the front matter below, and report any figures that became missing alt text.

## Make Markdown LLM-friendly

When the output feeds a model, keep structure the model can navigate: headers for hierarchy, tables as Markdown tables, alt text or a short description for images, sections short enough to chunk, and front matter naming the source:

```markdown
---
source: original_document.pdf
converted: <date>
tool: markitdown
pages: 42
---
```

## Security habits

These tools run locally and send nothing to a server; keep it that way, because the documents often hold personal or unpublished work.

- Use a dedicated virtual environment and install only the packages named in the setup script. Check unfamiliar packages with `pip-audit` before use.
- Reject any package that asks for API keys it does not need, uploads files for "cloud processing", has no public source, or wants unexpected network access: each is a path for document contents to leave the machine.
- For documents with personal data, convert in an isolated folder and delete intermediates afterwards.
- PyMuPDF is AGPL: fine for local use, but check the license before embedding it in a distributed product.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Scanned PDF returns no text | MinerU with OCR enabled |
| Complex tables broken | pandas for Excel, MinerU for PDF |
| Word formatting lost | Pandoc for DOCX |
| Garbled characters | Read and write UTF-8 explicitly |
| Missing module | Re-run the setup script; check the venv is active |

## Related

- Tool sources: MarkItDown (github.com/microsoft/markitdown, MIT), MinerU (github.com/opendatalab/MinerU, Apache 2.0), Pandoc (pandoc.org), python-docx, PyMuPDF (pymupdf.readthedocs.io).
