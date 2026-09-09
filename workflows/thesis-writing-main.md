---
description: Orchestrate thesis writing, formatting, bibliography, validation, and submission following the institutional TCC specification
---

# Thesis Writing Main Workflow

**Purpose**: Orchestrate all thesis writing, formatting, bibliography, and submission tasks following USP/ESALQ TCC specifications.

**Scope**: Complete thesis document (Portuguese primary, English secondary), ABNT formatting, bibliography, plagiarism check, and submission preparation.

**Trigger**: Use this workflow when writing thesis chapters, formatting documents, adding references, checking plagiarism, or preparing for submission.

---

## Phase 0: Consult Learnings (ALWAYS-ON)

**Before any other step, scan `learnings/INDEX.md`** for entries whose tags, title, or category match the current writing task (formatting rules, citation gotchas, platform quirks, etc.). Follow prior solutions; avoid approaches already documented as failures.

This phase is non-negotiable — see `skills/error-driven-learning/SKILL.md`.

---

## Phase 1: Discovery & Planning

### Step 1: Identify Writing Task

**Determine what type of thesis work is needed:**

| Task Type | Entry Point | Key Workflow |
|-----------|-------------|--------------|
| **Writing new chapter** | `thesis-completion-guide.md` §Chapter Structure | Chapter templates |
| **Adding citations** | `thesis-bibliography-integration.md` | Bibliography map |
| **Method selection** | `tcc-method-selection.md` | Method framework |
| **Formatting check** | `tcc-formatting-abnt-review.md` | ABNT vs TCC Manual |
| **Plagiarism scan** | `thesis-plagiarism-check.md` | Originality check |
| **Bilingual sync** | `bilingual-notebook-sync.md` | EN ↔ pt-BR |
| **Analysis→Thesis sync** | `tcc-analysis-and-writing-sync.md` | Evidence flow |
| **Advisor submission** | This workflow §Phase 5 | Submission prep |
| **Final formatting** | `tcc-formatting-abnt-review.md` | ABNT compliance |

### Step 2: Load Thesis Knowledge Base

**Read required resources based on task:**

**For chapter writing:**
- [ ] `thesis-completion-guide.md` — Structure, templates, deadlines
- [ ] `.agents/skills/research-thesis-support/SKILL.md` — Chapter structure guidance
- [ ] `docs/thesis_conclusion.md` — Current findings summary
- [ ] `docs/city_thesis_conclusion_addendum.md` — Municipality analysis

**For methods/methodology:**
- [ ] `tcc-method-selection.md` — Method framework
- [ ] `.agents/skills/thesis-bibliography/SKILL.md` §1-5 — Method references
- [ ] `usp-mba-course-map` reference — Course alignment

**For formatting:**
- [ ] `tcc-formatting-abnt-review.md` — ABNT vs TCC Manual
- [ ] `tcc-deliverables` skill — Deliverable expectations

**For bibliography:**
- [ ] `.agents/skills/thesis-bibliography/SKILL.md` — Complete reference database
- [ ] `thesis-bibliography-integration.md` — Citation map

### Step 3: Determine Language Scope

**Bilingual thesis requirement check:**

| Change Type | Scope | Required Actions |
|-------------|-------|------------------|
| **Portuguese chapter** | Primary | Write pt-BR, then sync to EN |
| **English chapter** | Secondary | Write EN, then sync to pt-BR |
| **Abstract** | Both | Resumo (PT) + Abstract (EN) in both versions |
| **Figures/Tables** | Both | Same data, translated captions |
| **Bibliography** | Both | Same references, proper format |
| **Finding changes** | Both | Update both versions identically |

**Synchronization workflow:**
```
1. Write/change one language version first
2. Apply equivalent changes to other version
3. Verify: Same results, numbers, citations
4. Check: Translated captions, consistent terminology
```

---

## Phase 2: Content Development
### Step 4: Chapter Writing (By Type)

Run the **thesis-chapter-writing** workflow (`workflows/thesis-chapter-writing.md`) for the chapter identified in Step 1. It carries the per-chapter-type guidance (introduction, literature review, methodology, results, discussion, conclusion), the evidence-linking rules, and the bilingual drafting order.

## Phase 3: Bibliography & Citations

### Step 5: Citation Integration

**Execute:**
```
1. Read `thesis-bibliography-integration.md`
2. For each section, check required citations:
   - Chapter 1: Gil, Lakatos, Ferreira, etc.
   - Chapter 2: Method-specific references
   - Chapter 3: Interpretation references
   - Chapter 4: Limitation references
3. Insert citations using ABNT format:
   "Texto" (AUTOR, Ano, p. xx)
   Autor (Ano) observa que...
4. Ensure bilingual sync:
   - PT: "Wooldridge (2020) propõe..."
   - EN: "Wooldridge (2020) proposes..."
5. Build reference list alphabetically
```

**Reference database:** `.agents/skills/thesis-bibliography/SKILL.md`

### Step 6: Reference List Compilation

**Format per ABNT NBR 6023:2023:**
```
BUSSAB, W. O.; MORETTIN, P. A. Estatística básica. 8. ed. São Paulo: Saraiva, 2017.

JAMES, G. et al. An introduction to statistical learning. 2nd ed. New York: Springer, 2021.

WOOLDRIDGE, J. M. Introductory econometrics: a modern approach. 7th ed. Boston: Cengage, 2020.
```

**Verify:**
- [ ] Alphabetical by first author surname
- [ ] Same references in both language versions
- [ ] No orphans (cited in text, in list; in list, cited in text)
- [ ] ABNT format correct

---

## Phase 4: Formatting & Quality

### Step 7: ABNT/TCC Formatting Check

**Execute:**
```
1. Read `tcc-formatting-abnt-review.md`
2. Compare TCC Manual vs ABNT NBR 14724:2011
3. Check page setup:
   - Margins: Left 3cm, Right 2cm, Top 3cm, Bottom 2cm (verify TCC Manual)
   - Font: Times New Roman or Arial 12pt (verify TCC Manual)
   - Line spacing: 1.5
4. Check pre-textual elements:
   - Cover (Capa) with ESALQ requirements
   - Abstract/Resumo (both languages)
   - Table of contents
5. Check textual structure:
   - Chapter numbering
   - Section hierarchy
6. Check references:
   - ABNT NBR 6023:2023 format
   - Alphabetical order
7. Document any deviations from ABNT (TCC Manual takes precedence)
```

### Step 8: Writing Quality Check

**Execute:**
```
1. Read `thesis-completion-guide.md` §Writing Quality
2. Apply Gopen & Swan principles:
   - Subject-verb proximity
   - Stress position
   - Old before new
   - Action in verbs
3. Check language-specific guidelines:
   - PT: Follow `17_Fundamentos-de-redacao-tecnico-cientifica`
   - EN: Follow academic writing conventions
4. Verify evidence language strength:
   - Strong evidence → "demonstrates," "shows"
   - Moderate → "suggests," "is consistent with"
   - Weak → "explores," "preliminary evidence"
5. Delete hedging: "suggests" not "may suggest"
6. Be specific: "R² = 0.62" not "performance improved"
```

---

## Phase 5: Validation & Verification

### Step 9: Plagiarism Check (Mandatory)

**Execute:**
```
1. Read `thesis-plagiarism-check.md`
2. Self-review:
   - All direct quotes have quotation marks
   - All paraphrases have citations
   - No mosaic plagiarism
   - Self-translation documented
3. Automated scan:
   - Turnitin (if university access)
   - Grammarly Premium
   - Or: Manual Google Scholar check
4. Check both language versions separately
5. Target: <15% similarity (excluding references)
6. Document scan results
7. Fix any flagged passages
```

**Special for bilingual:**
- Self-translation is NOT plagiarism (document it)
- Translation plagiarism: Cite original source
- Cross-language plagiarism: Manual check required

### Step 10: Analysis-Thesis Alignment Check

**Execute:**
```
1. Read `tcc-analysis-and-writing-sync.md`
2. Verify evidence traceability:
   - Every claim → notebook/script reference
   - Every statistic → source data
   - Every figure → generation code
3. Check validity:
   - No data leakage claims
   - Causality not overstated
   - Limitations acknowledged
4. Verify bilingual sync:
   - Same numbers in PT and EN
   - Same interpretations
   - Equivalent phrasing
5. Regenerate presentation assets if needed:
   python scripts/build_thesis_presentation_assets.py
```

---
## Phase 6: Final Preparation & Submission

Run the **thesis-submission-preparation** workflow (`workflows/thesis-submission-preparation.md`) in full: Step 11 pre-submission checklist, Step 12 final review, Step 13 submission packaging. Do not start it until every Phase 5 validation (plagiarism check, analysis-thesis alignment) has passed.

## Related Workflows & Skills

### Workflows (in execution order)
1. `thesis-completion-guide.md` — Structure and timeline
2. `tcc-method-selection.md` — Methodology framework
3. `tcc-analysis-and-writing-sync.md` — Evidence flow
4. `thesis-bibliography-integration.md` — Citations
5. `.agents/skills/thesis-bibliography/SKILL.md` — Reference database
6. `tcc-formatting-abnt-review.md` — Formatting
7. `thesis-plagiarism-check.md` — Originality
8. `bilingual-notebook-sync.md` — Bilingual sync
9. `workflows/bilingual-doc-sync.md` — Document sync

### Skills (for guidance)
- `tcc-deliverables` skill — Deliverable expectations
- `usp-mba-course-context` skill — USP MBA guidance
- `course-material-grounding` skill — Course alignment

### Skills (for reusable patterns)
- `.agents/skills/research-thesis-support/SKILL.md` — Chapter structure
- `.agents/skills/thesis-bibliography/SKILL.md` — 60+ references
- `.agents/skills/document-conversion/SKILL.md` — File handling

---

## Quick Decision Tree

```
What thesis task?
├── Writing chapter → thesis-completion-guide.md
├── Adding citations → thesis-bibliography-integration.md + bibliography/SKILL.md
├── Method selection → tcc-method-selection.md
├── Formatting check → tcc-formatting-abnt-review.md
├── Plagiarism scan → thesis-plagiarism-check.md
├── Bilingual sync → bilingual-notebook-sync.md / bilingual-doc-sync.md
└── Final submission → This workflow §Phase 6
```

---

## Exit Criteria

**Thesis is submission-ready when:**

- [ ] Portuguese version: Complete, formatted, cited
- [ ] English version: Complete, formatted, cited
- [ ] Both versions: Synchronized, identical results
- [ ] Bibliography: Complete, ABNT formatted
- [ ] Plagiarism check: Passed (<15%), documented
- [ ] Formatting: Follows TCC Manual (or documented deviations)
- [ ] Writing quality: Meets academic standards
- [ ] Analysis alignment: Evidence supports claims
- [ ] Supporting materials: Ready (notebooks, maps, dashboard)
- [ ] Submitted: To USP/ESALQ portal with confirmation
- [ ] **Capture-learning check (ALWAYS-ON)**: if this task involved 2+ failed approaches, a non-obvious fix, a formatting/tool gotcha, or an undocumented requirement, run `workflows/capture-learning.md` before closing. See `skills/error-driven-learning/SKILL.md`.

---

## Critical Success Factors

1. **Bilingual synchronization**: Changes to one version must flow to the other
2. **Evidence traceability**: Every claim must map to notebook/script output
3. **Citation completeness**: Every method, every interpretation, every framework must be cited
4. **Honest limitations**: State what the analysis cannot show
5. **Format compliance**: TCC Manual requirements take precedence over general ABNT
6. **Plagiarism prevention**: When in doubt, cite; document self-translations
