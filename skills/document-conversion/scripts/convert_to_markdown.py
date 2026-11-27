#!/usr/bin/env python3
"""
Document to Markdown Converter
Securely converts PDF, DOCX, PPTX, XLSX to Markdown
"""

import sys
import os
from pathlib import Path

def convert_file(input_path, output_path=None):
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
        return convert_xlsx(input_path, output_path)
    elif suffix == '.md':
        print(f"File is already Markdown: {input_path}")
        return True
    else:
        raise ValueError(f"Unsupported file format: {suffix}")

def convert_pdf(input_path, output_path):
    """Convert PDF to Markdown using PyMuPDF."""
    try:
        import fitz
        doc = fitz.open(input_path)
        text = []
        for page_num, page in enumerate(doc, 1):
            text.append(f"<!-- Page {page_num} -->")
            text.append(page.get_text())
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(text))
        doc.close()
        print(f"Converted: {input_path} -> {output_path}")
        return True
    except ImportError:
        print("PyMuPDF not installed. Run scripts/setup_document_conversion.sh", file=sys.stderr)
        return False

def convert_docx(input_path, output_path):
    """Convert DOCX to Markdown using python-docx."""
    try:
        from docx import Document
        doc = Document(input_path)
        lines = []
        for para in doc.paragraphs:
            if para.style.name.startswith('Heading'):
                level = para.style.name[-1] if para.style.name[-1].isdigit() else '1'
                lines.append(f"{'#' * int(level)} {para.text}")
            else:
                lines.append(para.text)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(lines))
        print(f"Converted: {input_path} -> {output_path}")
        return True
    except ImportError:
        print("python-docx not installed. Run scripts/setup_document_conversion.sh", file=sys.stderr)
        return False

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

def convert_xlsx(input_path, output_path):
    """Convert XLSX to Markdown using pandas."""
    try:
        import pandas as pd
        xls = pd.ExcelFile(input_path)
        with open(output_path, 'w', encoding='utf-8') as f:
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(input_path, sheet_name=sheet_name)
                f.write(f"## Sheet: {sheet_name}\n\n")
                f.write(df.to_markdown(index=False))
                f.write("\n\n---\n\n")
        print(f"Converted: {input_path} -> {output_path}")
        return True
    except ImportError:
        print("pandas not installed. Run scripts/setup_document_conversion.sh", file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_to_markdown.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    sys.exit(0 if convert_file(input_file, output_file) else 1)
