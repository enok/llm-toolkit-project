---
name: document-conversion
description: |
  Create and convert between PDF, Microsoft Word (DOCX), PowerPoint (PPTX), Excel
  (XLSX), and Markdown formats. Use for thesis PDF export, converting course
  material from PDF to markdown, building defense presentations, or generating
  data tables. Prefers anthropic's dedicated skills (pdf, docx, pptx, xlsx)
  for format-specific operations.
license: MIT
---

# Document Creation & Conversion Skill

Create and convert PDF, Microsoft Word, PowerPoint, Excel, and Markdown documents for thesis writing, presentations, and data analysis.

## Purpose

This skill provides secure, vetted tools for:
1. **Creating** documents in all major formats (PDF, DOCX, PPTX, XLSX, MD)
2. **Converting** between document formats
3. **Automating** document generation for thesis deliverables

## Capabilities Summary

| Format | Create | Read | Convert To | Convert From |
|--------|--------|------|------------|--------------|
| **PDF** | ✅ Generate | ✅ Extract | Markdown, Images | Markdown, DOCX, HTML |
| **DOCX** | ✅ Generate | ✅ Extract | Markdown, PDF | Markdown, HTML |
| **PPTX** | ✅ Generate | ✅ Extract | Markdown, PDF | Markdown |
| **XLSX** | ✅ Generate | ✅ Extract | Markdown, CSV, PDF | CSV, JSON, DB |
| **Markdown** | ✅ Generate | ✅ Native | All formats | All formats |

## Security Assessment

All recommended tools have been reviewed for:
- **Source legitimacy**: Official Microsoft or established academic institutions
- **License**: Open source with permissive licenses
- **No malware**: Verified repositories with active maintenance
- **No data exfiltration**: Local processing, no cloud upload required

| Tool | Source | Security Rating | License | Capabilities |
|------|--------|-----------------|---------|--------------|
| **markitdown** | Microsoft | ✅ Verified | MIT | Convert TO Markdown |
| **python-docx** | Community | ✅ Verified | MIT | Create/Read DOCX |
| **python-pptx** | Community | ✅ Verified | MIT | Create/Read PPTX |
| **openpyxl** | Community | ✅ Verified | MIT | Create/Read XLSX |
| **pandas** | PyData | ✅ Verified | BSD | Create/Read tables |
| **reportlab** | Community | ✅ Verified | BSD | Create PDFs |
| **fpdf2** | Community | ✅ Verified | LGPL | Create PDFs |
| **pypandoc** | Community | ✅ Verified | BSD/MIT | Multi-format conversion |
| **weasyprint** | Community | ✅ Verified | BSD | HTML to PDF |
| **PyMuPDF** | Artifex | ✅ Verified | AGPL | Read/Edit PDFs |
| **MinerU** | OpenDataLab | ✅ Verified | Apache 2.0 | PDF extraction |

**⚠️ Security Best Practice**: Always use virtual environments and verify package checksums when installing.

---

## Part 1: Document Creation

### 1. Creating PDF Documents

#### Option A: ReportLab (Programmatic PDF Creation)
```python
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm

def create_pdf_thesis(output_path, title, content_sections):
    """Create a thesis-style PDF document."""
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=3*cm,
        topMargin=3*cm,
        bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=1,  # Center
        spaceAfter=30
    )
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.5*cm))
    
    # Content sections
    for section_title, section_text in content_sections:
        story.append(Paragraph(section_title, styles['Heading2']))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(section_text, styles['BodyText']))
        story.append(Spacer(1, 0.5*cm))
    
    doc.build(story)
    print(f"PDF created: {output_path}")

# Example usage
create_pdf_thesis(
    "thesis_chapter1.pdf",
    "Chapter 1: Introduction",
    [
        ("Context", "This study investigates..."),
        ("Problem Statement", "The relationship between...")
    ]
)
```

**Install**: `pip install reportlab`

#### Option B: FPDF2 (Simple PDF Creation)
```python
from fpdf import FPDF

class ThesisPDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'MBA Thesis - Data Science', 0, 0, 'C')
        self.ln(20)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')
    
    def chapter_title(self, title):
        self.set_font('Arial', 'B', 14)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)
    
    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

def create_thesis_pdf(output_path, title, chapters):
    pdf = ThesisPDF()
    pdf.add_page()
    
    for chapter_title, chapter_content in chapters:
        pdf.chapter_title(chapter_title)
        pdf.chapter_body(chapter_content)
    
    pdf.output(output_path)

# Example usage
create_thesis_pdf(
    "thesis_output.pdf",
    "Public Compliance Analysis",
    [
        ("1. Introduction", "This thesis examines..."),
        ("2. Methodology", "We employ...")
    ]
)
```

**Install**: `pip install fpdf2`

#### Option C: WeasyPrint (HTML to PDF)
```python
from weasyprint import HTML, CSS

def markdown_to_pdf(md_path, pdf_path, css_path=None):
    """Convert Markdown to PDF via HTML."""
    import markdown
    
    # Read markdown
    with open(md_path, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convert to HTML
    html_content = markdown.markdown(md_content)
    
    # Wrap in HTML template
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Thesis Document</title>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert to PDF
    if css_path:
        HTML(string=full_html).write_pdf(pdf_path, stylesheets=[CSS(filename=css_path)])
    else:
        HTML(string=full_html).write_pdf(pdf_path)
    
    print(f"PDF created: {pdf_path}")

# Example usage
markdown_to_pdf("thesis_chapter.md", "thesis_chapter.pdf")
```

**Install**: `pip install weasyprint markdown`

---

### 2. Creating Microsoft Word (DOCX) Documents

#### Using python-docx
```python
from docx import Document
from docx.shared import Inches, Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

def create_thesis_docx(output_path, title, sections, author=""):
    """Create a thesis-style Word document."""
    doc = Document()
    
    # Set margins (ABNT style: left 3cm, right 2cm, top/bottom 3cm/2cm)
    sections_doc = doc.sections[0]
    sections_doc.left_margin = Cm(3)
    sections_doc.right_margin = Cm(2)
    sections_doc.top_margin = Cm(3)
    sections_doc.bottom_margin = Cm(2)
    
    # Title
    title_para = doc.add_heading(title, level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    if author:
        author_para = doc.add_paragraph(author)
        author_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    doc.add_paragraph()  # Spacing
    
    # Content sections
    for section_title, section_content in sections:
        # Section heading
        heading = doc.add_heading(section_title, level=1)
        
        # Content
        if isinstance(section_content, list):
            for paragraph in section_content:
                doc.add_paragraph(paragraph)
        else:
            doc.add_paragraph(section_content)
        
        doc.add_paragraph()  # Spacing between sections
    
    # Save
    doc.save(output_path)
    print(f"DOCX created: {output_path}")

# Example usage
create_thesis_docx(
    "thesis_chapter1.docx",
    "Chapter 1: Introduction",
    [
        ("Context", "This research investigates the relationship between..."),
        ("Problem Statement", ["The main challenge is...", "Additionally, we observe..."]),
        ("Objectives", "The objectives of this study are to...")
    ],
    author="Enok Antônio de Jesus"
)

# Advanced: Add tables
def add_results_table(doc, table_data, headers):
    """Add a results table to the document."""
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = 'Light Grid Accent 1'
    
    # Header row
    hdr_cells = table.rows[0].cells
    for i, header in enumerate(headers):
        hdr_cells[i].text = header
    
    # Data rows
    for row_data in table_data:
        row_cells = table.add_row().cells
        for i, value in enumerate(row_data):
            row_cells[i].text = str(value)
    
    return table

# Advanced: Add figures
def add_figure(doc, image_path, caption):
    """Add a figure with caption."""
    doc.add_picture(image_path, width=Inches(5.5))
    last_paragraph = doc.paragraphs[-1]
    last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Caption
    caption_para = doc.add_paragraph(f"Figure X: {caption}")
    caption_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption_para.style = 'Caption'
```

**Install**: `pip install python-docx`

---

### 3. Creating PowerPoint (PPTX) Presentations

#### Using python-pptx
```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor

def create_thesis_presentation(output_path, title, slides_data):
    """Create a thesis defense presentation."""
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    
    # Title slide
    title_slide_layout = prs.slide_layouts[0]  # Title slide layout
    slide = prs.slides.add_slide(title_slide_layout)
    slide.shapes.title.text = title
    slide.placeholders[1].text = "Enok Antônio de Jesus\nMBA Data Science & Analytics\nUSP/ESALQ"
    
    # Content slides
    for slide_title, slide_content in slides_data:
        bullet_slide_layout = prs.slide_layouts[1]  # Title and Content
        slide = prs.slides.add_slide(bullet_slide_layout)
        
        # Title
        slide.shapes.title.text = slide_title
        
        # Content
        body_shape = slide.placeholders[1]
        tf = body_shape.text_frame
        tf.text = slide_content[0] if isinstance(slide_content, list) else slide_content
        
        # Add bullet points if list
        if isinstance(slide_content, list) and len(slide_content) > 1:
            for point in slide_content[1:]:
                p = tf.add_paragraph()
                p.text = point
                p.level = 1
    
    prs.save(output_path)
    print(f"PPTX created: {output_path}")

# Example usage
create_thesis_presentation(
    "thesis_defense.pptx",
    "Public Compliance Data Analysis",
    [
        ("Introduction", ["Context: Public spending efficiency", "Problem: Compliance risk assessment", "Scope: 5,570 municipalities"]),
        ("Methodology", ["Bronze/Silver/Gold architecture", "Statistical analysis", "Machine Learning models"]),
        ("Results", ["Income predicts sanctions (r=0.74)", "Detection capacity > misconduct", "Regional disparities evident"]),
        ("Conclusions", ["Policy implications", "Limitations", "Future work"])
    ]
)

# Advanced: Add charts
def add_chart_slide(prs, chart_data, chart_title):
    """Add a slide with a chart."""
    from pptx.chart.data import ChartData
    from pptx.enum.chart import XL_CHART_TYPE
    
    slide_layout = prs.slide_layouts[5]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)
    
    # Add title
    title = slide.shapes.add_textbox(Inches(0.5), Inches(0.5), Inches(12), Inches(1))
    title.text_frame.text = chart_title
    
    # Chart data
    chart_data = ChartData()
    chart_data.categories = ['Cluster 1', 'Cluster 2', 'Cluster 3', 'Cluster 4']
    chart_data.add_series('Sanctions per 100k', (1.8, 5.5, 7.6, 0.4))
    
    # Add chart
    x, y, cx, cy = Inches(2), Inches(2), Inches(9), Inches(5)
    chart = slide.shapes.add_chart(
        XL_CHART_TYPE.COLUMN_CLUSTERED, x, y, cx, cy, chart_data
    ).chart
    
    return slide

# Advanced: Add images
def add_image_slide(prs, image_path, caption):
    """Add a slide with an image."""
    slide_layout = prs.slide_layouts[5]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)
    
    # Add image
    left = Inches(1)
    top = Inches(1.5)
    height = Inches(5)
    pic = slide.shapes.add_picture(image_path, left, top, height=height)
    
    # Add caption
    caption_box = slide.shapes.add_textbox(Inches(1), Inches(6.5), Inches(11), Inches(0.5))
    caption_box.text_frame.text = caption
    
    return slide
```

**Install**: `pip install python-pptx`

---

### 4. Creating Excel (XLSX) Spreadsheets

#### Using openpyxl
```python
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils.dataframe import dataframe_to_rows
from openpyxl.chart import BarChart, Reference
import pandas as pd

def create_thesis_data_workbook(output_path, sheet_data_dict):
    """Create an Excel workbook with multiple data sheets."""
    wb = Workbook()
    
    # Remove default sheet
    wb.remove(wb.active)
    
    for sheet_name, data in sheet_data_dict.items():
        ws = wb.create_sheet(title=sheet_name)
        
        if isinstance(data, pd.DataFrame):
            # Write DataFrame
            for r_idx, row in enumerate(dataframe_to_rows(data, index=False, header=True), 1):
                for c_idx, value in enumerate(row, 1):
                    cell = ws.cell(row=r_idx, column=c_idx, value=value)
                    
                    # Style header
                    if r_idx == 1:
                        cell.font = Font(bold=True, color="FFFFFF")
                        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                        cell.alignment = Alignment(horizontal="center")
        
        else:
            # Write list of lists
            for row_idx, row_data in enumerate(data, 1):
                for col_idx, value in enumerate(row_data, 1):
                    ws.cell(row=row_idx, column=col_idx, value=value)
        
        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    wb.save(output_path)
    print(f"XLSX created: {output_path}")

# Example usage
import pandas as pd

# Create sample data
df_results = pd.DataFrame({
    'State': ['SP', 'RJ', 'MG', 'RS', 'BA'],
    'Sanctions_per_100k': [25.3, 18.7, 12.4, 15.2, 8.9],
    'Avg_Income': [2850, 2650, 1950, 2100, 1450],
    'Cluster': [0, 0, 1, 0, 1]
})

df_clusters = pd.DataFrame({
    'Cluster': [0, 1, 2, 3],
    'Count': [821, 2158, 2584, 2],
    'Avg_Sanctions': [5.51, 1.85, 7.58, 0.37],
    'Avg_Transfers': [114117, 2264, 1172, 4298407]
})

create_thesis_data_workbook(
    "thesis_data.xlsx",
    {
        "State_Results": df_results,
        "Cluster_Summary": df_clusters,
        "Model_Performance": [
            ["Model", "R²", "RMSE"],
            ["OLS", "0.835", "8.42"],
            ["ElasticNet", "0.842", "8.15"],
            ["Random Forest", "0.851", "7.93"]
        ]
    }
)

# Advanced: Add charts
def add_chart_to_sheet(ws, chart_type="column"):
    """Add a chart to the worksheet."""
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Sanctions by State"
    chart.y_axis.title = 'Sanctions per 100k'
    chart.x_axis.title = 'State'
    
    data = Reference(ws, min_col=2, min_row=1, max_row=6, max_col=2)
    cats = Reference(ws, min_col=1, min_row=2, max_row=6)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.shape = 4
    
    ws.add_chart(chart, "E2")
```

**Install**: `pip install openpyxl pandas`

---

### 5. Creating Markdown Documents

#### Native Python (No libraries needed)
```python
def create_markdown_document(output_path, title, sections, metadata=None):
    """Create a structured Markdown document."""
    lines = []
    
    # YAML frontmatter (optional)
    if metadata:
        lines.append("---")
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")
        lines.append("---")
        lines.append("")
    
    # Title
    lines.append(f"# {title}")
    lines.append("")
    
    # Sections
    for section_title, section_content in sections:
        lines.append(f"## {section_title}")
        lines.append("")
        
        if isinstance(section_content, list):
            for item in section_content:
                if isinstance(item, tuple):
                    # Subsection
                    lines.append(f"### {item[0]}")
                    lines.append("")
                    lines.append(item[1])
                else:
                    # Bullet point
                    lines.append(f"- {item}")
        else:
            lines.append(section_content)
        
        lines.append("")
    
    # Write file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"Markdown created: {output_path}")

# Example usage
create_markdown_document(
    "thesis_chapter1.md",
    "Chapter 1: Introduction",
    [
        ("Context", [
            "Public spending efficiency is a critical concern...",
            ("Federal Transfers", "The Brazilian government transfers..."),
            ("Compliance Risk", "Sanctions data from CGU...")
        ]),
        ("Research Problem", "This study addresses the gap in understanding..."),
        ("Objectives", [
            "Characterize municipality clusters based on socioeconomic indicators",
            "Model the relationship between federal transfers and sanctions",
            "Assess regional disparities in compliance patterns"
        ])
    ],
    metadata={
        "title": "Public Compliance Data Analysis",
        "author": "Enok Antônio de Jesus",
        "date": "2026-02-01",
        "language": "en"
    }
)

# Advanced: Create tables in Markdown
def markdown_table(headers, rows):
    """Generate a Markdown table."""
    lines = []
    
    # Header
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("|" + "|".join([" --- " for _ in headers]) + "|")
    
    # Rows
    for row in rows:
        lines.append("| " + " | ".join(str(cell) for cell in row) + " |")
    
    return '\n'.join(lines)

# Example table
table = markdown_table(
    ["State", "Sanctions/100k", "Income", "Cluster"],
    [
        ["SP", "25.3", "2850", "0"],
        ["RJ", "18.7", "2650", "0"],
        ["MG", "12.4", "1950", "1"]
    ]
)
print(table)
```

---

## Part 2: Document Conversion

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

---

## Unified Python Converter

Create a single script for all conversions:

```python
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
        print("PyMuPDF not installed. Run: pip install PyMuPDF")
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
        print("python-docx not installed. Run: pip install python-docx")
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
        print("python-pptx not installed. Run: pip install python-pptx")
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
        print("pandas not installed. Run: pip install pandas openpyxl tabulate")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python convert_to_markdown.py <input_file> [output_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    convert_file(input_file, output_file)
```

---

## Installation Script

Create `scripts/setup_document_conversion.sh`:

```bash
#!/bin/bash
# Setup script for document conversion tools

set -e

echo "Setting up document conversion tools..."

# Create virtual environment (recommended)
if [ ! -d ".venv-docs" ]; then
    python3 -m venv .venv-docs
fi

source .venv-docs/bin/activate

# Install secure, vetted packages
echo "Installing packages..."
pip install --upgrade pip

# Core conversion libraries
pip install PyMuPDF        # PDF handling
pip install python-docx    # Word documents
pip install python-pptx    # PowerPoint
pip install pandas         # Excel/data
pip install openpyxl       # Excel engine
pip install tabulate       # Markdown tables
pip install markitdown     # Microsoft tool (optional)

echo "Setup complete!"
echo "Activate environment: source .venv-docs/bin/activate"
echo "Usage: python convert_to_markdown.py <file>"
```

---

## Security Best Practices

### 1. Virtual Environment Isolation
```bash
# Always use a dedicated virtual environment
python3 -m venv .venv-docs
source .venv-docs/bin/activate
pip install <packages>
```

### 2. Verify Package Integrity
```bash
# Check package checksums
pip install --require-hashes <package>  # If available

# Or verify via pip-audit
pip install pip-audit
pip-audit
```

### 3. No Cloud Upload
All recommended tools process documents **locally**. No data is sent to external servers.

### 4. Handle Sensitive Documents
For documents containing PII or sensitive data:
- Process in isolated environment
- Delete converted files after use
- Use `shred` for secure deletion:
  ```bash
  shred -u -z -n 35 converted_file.md
  ```

### 5. Red Flags (Avoid These)
| Warning Sign | Action |
|--------------|--------|
| Package asks for API keys unnecessarily | Reject |
| Package uploads files to "cloud processing" | Reject |
| Package has no GitHub/source available | Reject |
| Package has <100 downloads | Investigate |
| Package requests network access unexpectedly | Reject |

---

## LLM-Specific Optimization

When converting for LLM processing:

1. **Preserve Structure**: Use headers (#, ##, ###) for hierarchy
2. **Extract Tables**: Convert to Markdown tables
3. **Describe Images**: Add alt text or descriptions
4. **Chunking**: Split long documents by sections
5. **Metadata**: Add frontmatter with source info

```markdown
---
source: original_document.pdf
converted: 2024-01-15
tool: markitdown
pages: 42
---

# Document Content...
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Scanned PDF not OCR'd | Use MinerU with OCR enabled |
| Complex tables broken | Use pandas for Excel, MinerU for PDF |
| Formatting lost | Use pandoc for Word docs |
| Encoding issues | Always use UTF-8 encoding |
| Missing dependencies | Run setup script, check imports |

---

## Related Skills

- `.agents/skills/thesis-bibliography/SKILL.md` — Handle academic documents
- `docs/llm/workflows/thesis-completion-guide.md` — Thesis document management
- `docs/llm/workflows/bilingual-notebook-sync.md` — Multi-language documents

---

## References

- **MarkItDown**: https://github.com/microsoft/markitdown (Microsoft, MIT License)
- **MinerU**: https://github.com/opendatalab/MinerU (Apache 2.0 License)
- **Pandoc**: https://pandoc.org (GPL License)
- **python-docx**: https://python-docx.readthedocs.io (MIT License)
- **PyMuPDF**: https://pymupdf.readthedocs.io (AGPL/Commercial License)
