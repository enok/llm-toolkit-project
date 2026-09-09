---
description: Compare the institutional TCC manual and template against ABNT NBR 14724 and document the formatting standard to follow
---

# TCC Formatting Review: ABNT Standards vs ESALQ Manual Requirements

**Purpose**: Verify whether the ESALQ TCC Manual follows ABNT NBR 14724:2011 (and updates) or has institution-specific deviations.

## Executive Summary

The **ABNT NBR 14724:2011** (and corrigendum 2020) is the official Brazilian standard for academic work presentation. However, many institutions, including **USP/ESALQ**, have specific TCC manuals that may:
1. Follow ABNT strictly
2. Add institution-specific requirements
3. Have minor deviations from ABNT

**Action Required**: Compare the `Manual de Instruções e Normas para Trabalhos de Conclusão de Curso (242).pdf` against the ABNT checklist below.

---
## ABNT NBR 14724:2011 - Core Formatting Requirements

The section-by-section checklist (page setup, pre-textual elements, textual structure, post-textual elements, citations and references, tables and figures) lives in `skills/abnt-formatting/references/abnt-nbr-14724-core-requirements.md`. Load it before Phase 2 of the comparison checklist below.

## ESALQ-Specific Requirements to Verify

Based on typical USP/ESALQ TCC manuals, check for these specific requirements:

### USP Institutional Requirements

| Element | USP System Requirement | Source |
|---------|----------------------|--------|
| **JANUS system upload** | Digital submission required | USP |
| **Repository deposition** | Biblioteca Digital USP | USP |
| **ORCID** | Recommended for authors | USP |
| **Research data** | Availability statement recommended | USP |
| **Open access** | Check if mandatory | USP/ESALQ |

### MBA Data Science Specific

| Element | Likely Requirement | Verify |
|---------|-------------------|--------|
| **Code/data availability** | May require GitHub/repo link | Check manual |
| **Notebook reproducibility** | May require documentation | Check manual |
| **Dashboard/BI tools** | May allow Power BI, Tableau | Check manual |

---

## Comparison Checklist

### Phase 1: Extract TCC Manual Requirements

From `Manual de Instruções e Normas para Trabalhos de Conclusão de Curso (242).pdf`, extract:

```
TCC Manual Requirements Summary:
=================================

1. PAGE SETUP
   - Paper size: _____
   - Margins: Left ____ Right ____ Top ____ Bottom ____
   - Font: _____ Size: _____
   - Line spacing: _____
   - Paragraph indent: _____

2. PRE-TEXTUAL ELEMENTS (Required)
   - Cover format: [ ] Follows ABNT [ ] ESALQ-specific
   - Abstract length: _____ words
   - English abstract required: [ ] Yes [ ] No
   - Keywords: _____ number required
   
3. TEXTUAL STRUCTURE
   - Introduction numbered: [ ] Yes [ ] No
   - Chapter titles: _____ (format)
   - Max section levels: _____
   
4. REFERENCES
   - Citation style: [ ] Author-date [ ] Numbered [ ] Other
   - Reference standard: _____
   
5. TABLES/FIGURES
   - Caption position table: _____
   - Caption position figure: _____
   - Source note required: [ ] Yes [ ] No
```

### Phase 2: Compare Against ABNT

For each element above, mark:
- ✅ **Follows ABNT** — No action needed
- ⚠️ **TCC Specific** — Note deviation, follow TCC manual
- ❌ **Deviates from ABNT** — Requires conscious decision

### Phase 3: Document Deviations

Create a file: `docs/thesis_formatting_exceptions.md`

```markdown
# Thesis Formatting: ABNT vs TCC Manual

## Elements Following ABNT NBR 14724:2011
- Margins: 3cm/2cm/3cm/2cm
- Font: Times New Roman 12pt
- [List all ABNT-compliant elements]

## Elements with TCC Manual Specifics
- Cover page: Uses ESALQ-specific template
- Abstract length: 250 words (TCC) vs ABNT no specific
- [List all TCC-specific requirements]

## Deviations from ABNT (If Any)
- [Document any conscious deviations]

## Justification
The formatting follows the ESALQ MBA TCC Manual requirements 
as the institution's specifications take precedence over general 
ABNT standards for thesis submission.
```

---

## Recommended Action Plan

### Step 1: TCC Manual Extraction (30 minutes)
1. Open `Manual de Instruções e Normas para Trabalhos de Conclusão de Curso (242).pdf`
2. Locate sections: "Formato", "Apresentação", "Estrutura", "Referências"
3. Fill in the comparison checklist above

### Step 2: Template Comparison (15 minutes)
1. Open `Template Projeto de Pesquisa.docx` or `Template Resultados Preliminares_PT.docx`
2. Check actual formatting against TCC Manual requirements
3. Note any discrepancies

### Step 3: ABNT Alignment Decision (15 minutes)
| Scenario | Action |
|----------|--------|
| TCC Manual = ABNT | Follow either, document compliance |
| TCC Manual adds requirements | Follow TCC Manual (stricter wins) |
| TCC Manual differs from ABNT | Follow TCC Manual for submission |
| Unclear | Ask advisor/coordination |

### Step 4: Document the Standard (10 minutes)
Create `docs/thesis_formatting_standard.md` with:
- Which standard applies to each element
- Why (citation of TCC manual page/section)
- Any advisor-approved deviations

---

## Critical Elements to Verify

### HIGH PRIORITY (Will block submission if wrong)

1. **Citation Style**
   - ABNT: Author-date (Silva, 2020)
   - If TCC requires numbered: [1], [2] — this affects entire bibliography
   
2. **Margens**
   - ABNT has specific requirements
   - TCC may have different specs for binding
   
3. **Font and Size**
   - Must be readable for committee
   - Some fonts may not be acceptable
   
4. **Abstract Length**
   - ABNT: No specific word count
   - TCC may specify 200-250 words
   
5. **Cover Page Wording**
   - ABNT: Flexible
   - TCC: Usually exact wording required

### MEDIUM PRIORITY (May require revision)

1. **Table/Figure caption positions**
2. **Line spacing**
3. **Header/footer requirements**
4. **Page numbering start point**
5. **List of tables/figures threshold**

### LOW PRIORITY (Cosmetic)

1. **Chapter title capitalization**
2. **Section numbering depth**
3. **Dedication/acknowledgments placement**

---

## ABNT Standards Reference

For official ABNT requirements, consult:

| Standard | Title | Year |
|----------|-------|------|
| **NBR 14724:2011** | Trabalhos acadêmicos — Apresentação | 2011 (Corrigendum 2020) |
| **NBR 6023:2018/2023** | Referências — Elaboração | 2023 update |
| **NBR 6024:2012** | Numeração progressiva das seções | 2012 |
| **NBR 10520:2023** | Citações | 2023 |
| **NBR 6034:2023** | Resumo e abstract | 2023 |

**Note**: ABNT standards are periodically updated. The TCC Manual may reference an older version.

---

## Related Resources

- `thesis-completion-guide.md` — Full thesis guide
- `thesis-bibliography-integration.md` — Citation formatting
- `thesis-plagiarism-check.md` — Originality verification
- `.agents/skills/thesis-bibliography/SKILL.md` — ABNT citation formats
- `tcc-deliverables` skill — Deliverable expectations

---

## Quick Decision Matrix

| Question | Answer |
|----------|--------|
| TCC Manual says X, ABNT says Y | **Follow TCC Manual** (institutional requirements prevail) |
| TCC Manual is silent, ABNT specifies | **Follow ABNT** (national standard) |
| Both specify, but differ | **Follow TCC Manual** (stricter/more specific wins) |
| Neither specifies | **Follow ABNT** (national standard) or ask advisor |

**Bottom Line**: The TCC Manual requirements **always take precedence** over general ABNT standards for thesis submission at ESALQ.
