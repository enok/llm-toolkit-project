---
title: Document creation recipes (PDF, DOCX, PPTX, XLSX, Markdown)
tags: [pdf, docx, pptx, xlsx, markdown, reportlab, python-docx, python-pptx, openpyxl]
---

# Document creation recipes

Companion to `skills/document-conversion/SKILL.md`. Read this when you must generate a new document from code and the dedicated format skills are not available.

## Contents

- 1. Creating PDF Documents
  - Option A: ReportLab (Programmatic PDF Creation)
  - Option B: FPDF2 (Simple PDF Creation)
  - Option C: WeasyPrint (HTML to PDF)
- 2. Creating Microsoft Word (DOCX) Documents
  - Using python-docx
- 3. Creating PowerPoint (PPTX) Presentations
  - Using python-pptx
- 4. Creating Excel (XLSX) Spreadsheets
  - Using openpyxl
- 5. Creating Markdown Documents
  - Native Python (No libraries needed)

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
        self.cell(0, 10, '<Document Title>', 0, 0, 'C')
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
    "<Document Title>",
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
        ("Context", "This research investigates a specific problem domain..."),
        ("Problem Statement", ["The main challenge is...", "Additionally, we observe..."]),
        ("Objectives", "The objectives of this study are to...")
    ],
    author="<Author Name>"
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
    slide.placeholders[1].text = "<Author Name>\n<Program>\n<Institution>"
    
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
    "Research Data Analysis",
    [
        ("Introduction", ["Context: Research background and motivation", "Problem: The research question being addressed", "Scope: Domain-specific scope"]),
        ("Methodology", ["Data architecture overview", "Statistical analysis approach", "Analysis methods"]),
        ("Results", ["Key finding 1 with supporting metric", "Key finding 2 with supporting metric", "Key finding 3 with supporting metric"]),
        ("Conclusions", ["Implications of findings", "Limitations", "Future work"])
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
    chart_data.categories = ['Group A', 'Group B', 'Group C', 'Group D']
    chart_data.add_series('Metric', (10, 20, 30, 40))
    
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
    'Region': ['Region A', 'Region B', 'Region C', 'Region D', 'Region E'],
    'Metric': [10.0, 20.0, 30.0, 40.0, 50.0],
    'Value': [100, 200, 300, 400, 500],
    'Group': [0, 0, 1, 0, 1]
})

df_clusters = pd.DataFrame({
    'Group': [0, 1, 2, 3],
    'Count': [10, 20, 30, 40],
    'Avg_Metric': [1.0, 2.0, 3.0, 4.0],
    'Avg_Value': [100, 200, 300, 400]
})

create_thesis_data_workbook(
    "thesis_data.xlsx",
    {
        "Region_Results": df_results,
        "Group_Summary": df_clusters,
        "Model_Performance": [
            ["Model", "R²", "RMSE"],
            ["Model A", "0.80", "10.0"],
            ["Model B", "0.82", "9.0"],
            ["Model C", "0.85", "8.0"]
        ]
    }
)

# Advanced: Add charts
def add_chart_to_sheet(ws, chart_type="column"):
    """Add a chart to the worksheet."""
    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = "Metric by Region"
    chart.y_axis.title = 'Metric'
    chart.x_axis.title = 'Region'
    
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
            "Context: The research domain addresses an important area...",
            ("Background", "The domain of interest has evolved over time..."),
            ("Research Gap", "Current literature lacks understanding of...")
        ]),
        ("Research Problem", "This study addresses the gap in understanding..."),
        ("Objectives", [
            "Characterize key dimensions based on domain indicators",
            "Model the relationship between relevant variables",
            "Assess patterns and variations across the domain"
        ])
    ],
    metadata={
        "title": "Research Title",
        "author": "<Author Name>",
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
    ["Region", "Metric", "Value", "Group"],
    [
        ["Region A", "10.0", "100", "0"],
        ["Region B", "20.0", "200", "0"],
        ["Region C", "30.0", "300", "1"]
    ]
)
print(table)
```
