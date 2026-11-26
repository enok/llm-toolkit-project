---
title: Document conversion recipes (to and from Markdown)
tags: [markitdown, pandoc, pymupdf, pandas, openpyxl, conversion]
---

# Document conversion recipes

Companion to `skills/document-conversion/SKILL.md`. Read this when converting an existing PDF, DOCX, PPTX, XLSX, or Markdown file and you need the exact commands for an option the main skill names.

## Contents

- 1. PDF Documents (Read/Convert)
  - Option C: PyMuPDF (fitz) - For Python scripting
- 2. Microsoft Word (DOCX)
  - Option A: MarkItDown
  - Option B: Pandoc (Industry Standard)
  - Option C: Python (python-docx)
- 3. Microsoft PowerPoint (PPTX)
  - Option A: MarkItDown
  - Option B: Pandoc
  - Option C: Python (python-pptx)
- 4. Microsoft Excel (XLSX)
  - Option A: Pandas (Data Analysis)
  - Option B: OpenPyXL (Raw extraction)
- 5. Markdown (MD)

### 1. PDF Documents (Read/Convert)

#### Option C: PyMuPDF (fitz) - For Python scripting
```python
import fitz  # PyMuPDF

def pdf_to_markdown(pdf_path, md_path):
    doc = fitz.open(pdf_path)
    text = []
    for page in doc:
        text.append(page.get_text())
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(text))
    doc.close()
```

**Install**: `pip install PyMuPDF`

---

### 2. Microsoft Word (DOCX)

#### Option A: MarkItDown
```bash
markitdown document.docx > document.md
```

#### Option B: Pandoc (Industry Standard)
```bash
# Install pandoc (system package)
# Ubuntu/Debian: sudo apt-get install pandoc
# macOS: brew install pandoc
# Windows: choco install pandoc

# Convert
pandoc document.docx -t markdown -o document.md
```

**Pros**: Gold standard, handles formatting well  
**Cons**: Requires external binary installation  
**Best for**: Preserving document structure

#### Option C: Python (python-docx)
```python
from docx import Document

def docx_to_markdown(docx_path, md_path):
    doc = Document(docx_path)
    lines = []
    for para in doc.paragraphs:
        lines.append(para.text)
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(lines))
```

**Install**: `pip install python-docx`

---

### 3. Microsoft PowerPoint (PPTX)

#### Option A: MarkItDown
```bash
markitdown presentation.pptx > presentation.md
```

#### Option B: Pandoc
```bash
pandoc presentation.pptx -t markdown -o presentation.md
```

#### Option C: Python (python-pptx)
```python
from pptx import Presentation

def pptx_to_markdown(pptx_path, md_path):
    prs = Presentation(pptx_path)
    lines = []
    for i, slide in enumerate(prs.slides, 1):
        lines.append(f"## Slide {i}")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                lines.append(shape.text)
        lines.append("")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
```

**Install**: `pip install python-pptx`

---

### 4. Microsoft Excel (XLSX)

#### Option A: Pandas (Data Analysis)
```python
import pandas as pd

def excel_to_markdown(excel_path, md_path, sheet_name=0):
    # Read all sheets or specific sheet
    if sheet_name == 'all':
        xls = pd.ExcelFile(excel_path)
        with open(md_path, 'w', encoding='utf-8') as f:
            for sheet in xls.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet)
                f.write(f"## Sheet: {sheet}\n\n")
                f.write(df.to_markdown())
                f.write("\n\n---\n\n")
    else:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(df.to_markdown())
```

**Install**: `pip install pandas openpyxl tabulate`

#### Option B: OpenPyXL (Raw extraction)
```python
from openpyxl import load_workbook

def excel_to_markdown_simple(excel_path, md_path):
    wb = load_workbook(excel_path, data_only=True)
    with open(md_path, 'w', encoding='utf-8') as f:
        for sheet_name in wb.sheetnames:
            f.write(f"## Sheet: {sheet_name}\n\n")
            sheet = wb[sheet_name]
            for row in sheet.iter_rows(values_only=True):
                row_text = ' | '.join(str(cell) if cell else '' for cell in row)
                f.write(f"{row_text}\n")
            f.write("\n---\n\n")
```

**Install**: `pip install openpyxl`

---

### 5. Markdown (MD)

Markdown is already the optimal format for LLM processing. Just ensure:
- UTF-8 encoding
- Proper line endings (LF, not CRLF)
- Consistent header hierarchy (#, ##, ###)

**Validation**:
```python
import re

def validate_markdown(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    issues = []
    
    # Check for CRLF
    if '\r\n' in content:
        issues.append("Contains CRLF line endings (should be LF)")
    
    # Check header hierarchy
    headers = re.findall(r'^(#{1,6})', content, re.MULTILINE)
    levels = [len(h) for h in headers]
    for i in range(1, len(levels)):
        if levels[i] > levels[i-1] + 1:
            issues.append(f"Header level jump: {levels[i-1]} to {levels[i]}")
    
    return issues
```
