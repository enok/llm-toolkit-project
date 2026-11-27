#!/usr/bin/env python3
"""
Document to Markdown Converter
Securely converts PDF, DOCX, PPTX, XLSX to Markdown
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

def convert_file(input_path, output_path=None, include_hidden_sheets=False):
    """Convert any supported file to Markdown."""
    input_path = Path(input_path)
    
    if not output_path:
        output_path = input_path.with_suffix('.md')
    
    suffix = input_path.suffix.lower()
    
    if suffix == '.pdf':
        return convert_pdf(input_path, output_path)
    elif suffix == '.docx':
        return convert_docx(input_path, output_path)
    elif suffix == '.pptx':
        return convert_pptx(input_path, output_path)
    elif suffix == '.xlsx':
        return convert_xlsx(input_path, output_path, include_hidden_sheets)
    elif suffix == '.md':
        print(f"File is already Markdown: {input_path}")
        return True
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def convert_pdf(input_path, output_path):
    """Convert PDF to Markdown using PyMuPDF, falling back to pdftotext."""
    try:
        import fitz
    except ImportError:
        return convert_pdf_pdftotext(input_path, output_path)
    doc = fitz.open(input_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    _write_pdf_pages(pages, output_path)
    print(f"Converted: {input_path} -> {output_path}")
    return True

def convert_pdf_pdftotext(input_path, output_path):
    """Fallback for when PyMuPDF is missing: poppler's pdftotext."""
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        print("Neither PyMuPDF nor pdftotext is installed. Run scripts/setup_document_conversion.sh "
              "or install poppler-utils", file=sys.stderr)
        return False
    result = subprocess.run([pdftotext, "-enc", "UTF-8", str(input_path), "-"],
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"pdftotext failed: {result.stderr.strip()}", file=sys.stderr)
        return False
    # pdftotext ends every page with a form feed.
    pages = result.stdout.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    _write_pdf_pages(pages, output_path)
    print(f"Converted (pdftotext fallback, PyMuPDF not installed): {input_path} -> {output_path}")
    return True

def _write_pdf_pages(pages, output_path):
    text = []
    for page_num, page_text in enumerate(pages, 1):
        text.append(f"<!-- Page {page_num} -->")
        text.append(page_text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(text))

_W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
# Text with tracked changes accepted: inserted runs (w:ins, w:moveTo) are kept,
# deleted runs (w:del, w:moveFrom) are dropped.
_ACCEPTED_TEXT_XPATH = (
    ".//w:t[not(ancestor::w:del) and not(ancestor::w:moveFrom)]"
    " | .//w:tab[not(ancestor::w:del) and not(ancestor::w:moveFrom)]"
    " | .//w:br[not(ancestor::w:del) and not(ancestor::w:moveFrom)]"
)

def _paragraph_text(p_element):
    parts = []
    for node in p_element.xpath(_ACCEPTED_TEXT_XPATH):
        tag = node.tag.rsplit('}', 1)[-1]
        if tag == 't':
            parts.append(node.text or '')
        else:
            parts.append('\t' if tag == 'tab' else '\n')
    return ''.join(parts)

def _table_markdown(tbl_element):
    rows = []
    for tr in tbl_element.iterchildren(f"{{{_W_NS}}}tr"):
        cells = []
        for tc in tr.iterchildren(f"{{{_W_NS}}}tc"):
            paras = [_paragraph_text(p) for p in tc.iterchildren(f"{{{_W_NS}}}p")]
            text = '<br>'.join(t.strip() for t in paras if t.strip())
            cells.append(text.replace('|', '\\|').replace('\n', ' '))
        rows.append(cells)
    if not rows:
        return ''
    width = max(len(r) for r in rows) or 1
    rows = [r + [''] * (width - len(r)) for r in rows]
    lines = ['| ' + ' | '.join(rows[0]) + ' |', '|' + ' --- |' * width]
    lines += ['| ' + ' | '.join(r) + ' |' for r in rows[1:]]
    return '\n'.join(lines)

def convert_docx(input_path, output_path):
    """Convert DOCX to Markdown using python-docx.

    Walks the body in document order so tables stay where they were, and
    accepts tracked changes (insertions kept, deletions dropped).
    """
    try:
        from docx import Document
        from docx.text.paragraph import Paragraph
    except ImportError:
        print("python-docx not installed. Run scripts/setup_document_conversion.sh", file=sys.stderr)
        return False
    doc = Document(input_path)
    lines = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit('}', 1)[-1]
        if tag == 'tbl':
            lines.append(_table_markdown(child))
            continue
        if tag != 'p':
            continue
        text = _paragraph_text(child)
        style = Paragraph(child, doc).style
        style_name = style.name if style is not None else ''
        if style_name.startswith('Heading'):
            level = style_name[-1] if style_name[-1].isdigit() else '1'
            lines.append(f"{'#' * int(level)} {text}")
        else:
            lines.append(text)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(lines))
    print(f"Converted: {input_path} -> {output_path}")
    return True

def convert_pptx(input_path, output_path):
    """Convert PPTX to Markdown using python-pptx."""
    try:
        from pptx import Presentation
        prs = Presentation(input_path)
        lines = []
        for i, slide in enumerate(prs.slides, 1):
            lines.append(f"## Slide {i}")
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    lines.append(shape.text)
            lines.append("")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        print(f"Converted: {input_path} -> {output_path}")
        return True
    except ImportError:
        print("python-pptx not installed. Run scripts/setup_document_conversion.sh", file=sys.stderr)
        return False

def convert_xlsx(input_path, output_path, include_hidden_sheets=False):
    """Convert XLSX to Markdown using pandas.

    Hidden sheets are skipped unless include_hidden_sheets is set; either way
    the output says which hidden sheets there were.
    """
    try:
        import pandas as pd
        from openpyxl import load_workbook
    except ImportError:
        print("pandas/openpyxl not installed. Run scripts/setup_document_conversion.sh", file=sys.stderr)
        return False
    wb = load_workbook(input_path, read_only=True)
    states = {ws.title: ws.sheet_state for ws in wb.worksheets}
    wb.close()
    hidden = [name for name, state in states.items() if state != 'visible']
    with open(output_path, 'w', encoding='utf-8') as f:
        if hidden and not include_hidden_sheets:
            f.write(f"<!-- Skipped hidden sheets: {', '.join(hidden)} "
                    "(use --include-hidden-sheets to include them) -->\n\n")
        for sheet_name in states:
            is_hidden = sheet_name in hidden
            if is_hidden and not include_hidden_sheets:
                continue
            df = pd.read_excel(input_path, sheet_name=sheet_name)
            label = " (hidden)" if is_hidden else ""
            f.write(f"## Sheet: {sheet_name}{label}\n\n")
            f.write(df.to_markdown(index=False))
            f.write("\n\n---\n\n")
    if hidden:
        action = "included" if include_hidden_sheets else "skipped (use --include-hidden-sheets)"
        print(f"Hidden sheets {action}: {', '.join(hidden)}")
    print(f"Converted: {input_path} -> {output_path}")
    return True

def main(argv=None):
    parser = argparse.ArgumentParser(description="Convert PDF, DOCX, PPTX or XLSX to Markdown.")
    parser.add_argument("input_file")
    parser.add_argument("output_file", nargs="?")
    parser.add_argument("--include-hidden-sheets", action="store_true",
                        help="XLSX: also convert hidden sheets (skipped by default)")
    args = parser.parse_args(argv)
    return 0 if convert_file(args.input_file, args.output_file, args.include_hidden_sheets) else 1

if __name__ == "__main__":
    sys.exit(main())
