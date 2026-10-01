---
name: abnt-formatting
description: |
  Apply ABNT (Associação Brasileira de Normas Técnicas) academic formatting standards
  to thesis, dissertation, and capstone documents, including citations (NBR 10520),
  references (NBR 6023), page layout (NBR 14724), and figure/table captions. Use when
  writing or reviewing thesis content, formatting references, generating LaTeX, or
  checking compliance with the institution's thesis manual.
license: MIT
---

# ABNT Formatting for Theses

Brazilian academic formatting standards for thesis work.

> **Reference**: See `references/abnt-nbr-14724-core-requirements.md` and the institution's thesis manual.

## Quick Reference

### Citations (NBR 10520)
- **Direct citation up to 3 lines**: `"text" (AUTHOR, YEAR, p. X)`
- **Direct citation >3 lines**: indented paragraph, 4cm left margin, 10pt font, single spacing
- **Indirect citation**: `(AUTHOR, YEAR)` or `Author (YEAR)`
- **Multiple authors same work**: `(AUTHOR1; AUTHOR2; AUTHOR3, YEAR)` — semicolon-separated
- **apud** (secondary source): `(AUTHOR1, YEAR1 apud AUTHOR2, YEAR2)`

### References (NBR 6023)
Format in references section:
```
SURNAME, Firstname. Title: subtitle. Edition. Place: Publisher, Year.
SURNAME, F. et al. Article title. Journal Name, v. X, n. Y, p. 10-20, Month Year.
```

- Alphabetical order by surname
- Single space within entry, double space between entries
- Left-aligned (NOT justified)
- Year in **bold** (optional; follow the institution's manual)

### Page Layout (NBR 14724)
- **Paper**: A4
- **Margins**: Left/Top 3cm, Right/Bottom 2cm
- **Font**: Arial or Times New Roman 12pt (body), 10pt (citations/footnotes)
- **Line spacing**: 1.5 (body), 1.0 (long citations, footnotes, references, captions)
- **Paragraph indent**: 1.25cm first line
- **Page numbers**: top-right, appear from introduction onwards (pre-textual pages counted but not numbered)

### Figure/Table Captions
- **Figures** (images, graphs, diagrams):
  - Caption **above**: `Figura 1 - Descrição`
  - Source **below**: `Fonte: Author (Year)` or `Fonte: Elaborada pelo autor (Year)`
- **Tables** (numeric data):
  - Caption **above**: `Tabela 1 - Descrição`
  - Source **below**: `Fonte: elaborado pelo autor (2023)`
  - Tables use **open borders** (no side vertical lines)

### Section Numbering
- Chapter titles: ALL CAPS, bold, left-aligned, 12pt
- Section 1.1: Capitalized Title, bold
- Section 1.1.1: Sentence case, bold, no periods in numbering

## When to Apply

- Writing or reviewing thesis chapters (introduction, methodology, results, conclusion)
- Formatting bibliography/references section
- Checking citation consistency across document
- Creating figures/tables with ABNT-compliant captions
- Converting informal notes to academic prose
- Reviewing a LaTeX template for institutional compliance

## Institution-Specific Rules

Institutions often add rules beyond ABNT; the institution's thesis manual takes precedence. Typical additions:
- **Pre-textual pages order**: cover → title page → approval sheet → dedication → acknowledgments → epigraph → resumo (pt-BR) → abstract (EN) → lists (figures/tables/abbreviations) → summary
- **Final document typically includes**: resumo AND abstract (Portuguese + English)
- **Keywords**: 3-5 per language, after each abstract
- **Length**: typically 30-80 pages (check the institution's limit)

## Related

- `skills/latex-notebooks/` — LaTeX math in notebooks
- `workflows/thesis-writing-main.md` — Thesis writing and formatting orchestration

## References

- [ABNT NBR 10520:2023](https://www.abntcatalogo.com.br/norma.aspx?ID=617095) — Citations
- [ABNT NBR 6023:2018](https://www.abntcatalogo.com.br/norma.aspx?ID=404154) — References
- [ABNT NBR 14724:2011](https://www.abntcatalogo.com.br/norma.aspx?ID=87878) — Academic work presentation
