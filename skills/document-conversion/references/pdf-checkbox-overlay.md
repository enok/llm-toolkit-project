---
title: Check boxes in exported PDFs and related export pitfalls
tags: [pdf, checkbox, acroform, google-docs, libreoffice, qpdf, export]
---

# Check boxes in exported PDFs and related export pitfalls

Use when a document exported to PDF must carry usable check boxes, when a
checklist is built inside a word-processor table, when a PDF cannot be written
because a viewer holds it open, or when a spreadsheet is recalculated headlessly.

## 1. Check boxes exported from a cloud word processor are drawings

Exporting a document to PDF draws check-box glyphs as vector curves, so the PDF
has no clickable fields. Add real form fields on top:

1. Find each box with `pdfplumber` (page curves or rects whose size and
   position match the box glyph); record page, x, y, width, height.
2. Create the overlay with `reportlab` (`acroForm.checkbox`, one unique name per
   box, a size matching the glyph) and merge it onto the original page with
   `pypdf`, keeping the original content.
3. Verify the result: each field has `/V` and `/AS` set to `/Yes` (or `/Off`) as
   intended, and a poppler render (`pdftoppm`) still shows the boxes aligned.
   Open a page image to confirm; a script-only pass is not visual proof.

## 2. Checklist items in tables

In a cloud word-processor document, a `- [ ]` item typed into a table cell is
applied by a cell-level replace; pipe-table Markdown pasted as a table does not
convert it. Replace the cell text, then re-read the cell to confirm.

## 3. A PDF held open is file-locked

A viewer that has the PDF open blocks rewriting or replacing it. Edit with a
same-length byte replacement when only a small string changes, retry after the
user closes the viewer, and finish with `qpdf --check <file>` to confirm the
file is structurally valid.

## 4. Headless spreadsheet recalculation drops external links

A LibreOffice headless recalculation can drop external-workbook links. After a
recalculation, scan the formulas and the workbook XML parts for the link targets
that existed before, and restore any that vanished before delivering the file.

See also `skills/document-conversion/SKILL.md` for the conversion toolchain.
