---
name: markdown-pdf-export
description: >-
  Generate and verify Jira-ready PDFs from Markdown:
  HTML+headless Chrome for table-heavy docs; Kroki+Mermaid PNG + Pandoc+Typst for architecture;
  automated verify loop with pypdf. Use for PDF export, Jira attachments, or when Markdown preview is unavailable.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Markdown → PDF export

## When to use

- Producing **PDF attachments** for Jira or email when Markdown is not rendered in the tracker.
- Regenerating PDF artifacts from source Markdown after editing.
- Running a **build + content verification** loop until all checks pass.

## Pipelines (two patterns)

| Kind | Toolchain | Notes |
|------|-----------|-------|
| Table-heavy docs | Pandoc → HTML + embedded CSS → **Chrome** headless `--print-to-pdf` | Landscape CSS for wide tables; serve HTML on `127.0.0.1` and use `--no-pdf-header-footer`; never print a `file:///` URL directly for Jira artifacts |
| Diagrams (Mermaid) | Mermaid blocks → **PNG via Kroki** POST → **Pandoc + Typst** PDF | Kroki sends diagram source off-host — see security rule |

## Source of truth

- **Markdown** files are the authoritative format.
- **PDFs** are export artifacts for sharing; never treat them as the primary record.

## Security and privacy

Follow **`rules/pdf-export-security.md`** in this skill: Kroki sends diagram **source** off-host unless you use a self-hosted instance; do not embed secrets, tokens, or internal-only hostnames in Mermaid or body text.

For Jira-facing PDFs, run text extraction verification with forbidden local-path
markers such as `file:///`, `C:/Users`, and `C:\Users`. Chrome print footers can
otherwise expose the source machine path even when the body content looks clean.
