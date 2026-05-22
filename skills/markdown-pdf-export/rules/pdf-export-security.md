# Rule: Security expectations for Markdown → PDF export

**Scope:** Scripts under `scripts/` used to produce PDFs from repository Markdown.
**Audience:** Engineers generating Jira attachments or shared PDFs.

## Data leaving the workstation

| Mechanism | Data sent | Mitigation |
|-----------|-----------|------------|
| **Kroki** (`render-mermaid-in-markdown-for-pdf.ps1`, default `https://kroki.io/mermaid/png`) | Full **Mermaid diagram source** (HTTP POST) | For confidential diagrams, use **self-hosted Kroki** and pass `-KrokiUrl`. Do not put **secrets, tokens, PII, or internal-only hostnames** inside Mermaid unless the renderer is org-controlled. |
| **Public internet** (same) | Only what Kroki needs to render | Treat as **third-party processing** for compliance reviews. |

## Local-only components

- **Pandoc** reads Markdown from disk; output HTML/PDF stays local until you copy or upload.
- **Python `http.server`** serves generated HTML on **127.0.0.1** only for Chrome print (short-lived).
- **Chrome headless** writes PDF to `%TEMP%` then copies to the output path you pass.

## Artifact handling

- PDFs may be **attached to Jira**, emailed, or stored in Drive — apply the same classification as the **source Markdown** (and anything extracted from diagrams).
- Generated files include **`architecture-for-pdf.md`** and **`pdf/mermaid/*.png`** — keep out of leaks the same as source docs; prefer **not** committing binary exports unless the team explicitly version-controls them.

## Verification tool

- **`verify_pdf_content.py`** / **pypdf** extracts **text** from PDFs for gates — it does not upload PDFs. Install deps from `scripts/pdf-verify-requirements.txt`.
- For Jira/email PDFs, verify forbidden local path markers such as `file:///`,
  `C:/Users`, and `C:\Users`; browser print footers can leak the source path if
  HTML is printed directly from the filesystem.

## Review checklist

- [ ] No credentials or live keys in Markdown, Mermaid, or examples in the exported doc set.
- [ ] Kroki / diagram policy matches org policy (public vs self-hosted).
- [ ] Extracted PDF text contains no local machine paths or `file:///` source URLs.
- [ ] Final PDF distribution channel (Jira visibility) matches data class of the content.
