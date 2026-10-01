---
description: Orchestrate thesis writing, formatting, bibliography, validation, and submission following the institution's thesis specification
---

# Thesis Writing Main Workflow

**Purpose**: Orchestrate all thesis writing, formatting, bibliography, and submission tasks following the institution's thesis manual.

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
| **Writing new chapter** | `workflows/thesis-chapter-writing.md` | Chapter-type guidance |
| **Adding citations** | This workflow §Phase 3 | Citation integration |
| **Method selection** | `workflows/research-analysis-cycle.md` | Method framework |
| **Formatting check** | `skills/abnt-formatting/SKILL.md` | ABNT vs institutional manual |
| **Plagiarism scan** | `workflows/thesis-plagiarism-check.md` | Originality check |
| **Bilingual sync** | `workflows/bilingual-notebook-sync.md` | EN ↔ pt-BR |
| **Analysis→Thesis sync** | `workflows/research-analysis-cycle.md` | Evidence flow |
| **Advisor submission** | `workflows/thesis-submission-preparation.md` | Submission prep |
| **Final formatting** | `skills/abnt-formatting/SKILL.md` | ABNT compliance |

### Step 2: Load Thesis Knowledge Base

**Read required resources based on task:**

**For chapter writing:**
- [ ] `workflows/thesis-chapter-writing.md` — Chapter-type guidance
- [ ] The institution's thesis manual — Structure, templates, deadlines
- [ ] The project's current findings summary (e.g., `docs/<findings-summary>.md`)

**For methods/methodology:**
- [ ] `workflows/research-analysis-cycle.md` — Method framework
- [ ] The project's reference database — Method references

**For formatting:**
- [ ] `skills/abnt-formatting/SKILL.md` — ABNT vs the institution's manual
- [ ] The institution's thesis manual — Deliverable expectations

**For bibliography:**
- [ ] `skills/abnt-formatting/SKILL.md` — NBR 6023 reference format
- [ ] The project's reference database — Complete list of sources

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
1. Read the project's reference database / citation map
2. For each section, check required citations:
   - Chapter 1: Research-design and context references
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

**Reference format:** `skills/abnt-formatting/SKILL.md`

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

### Step 7: ABNT/Institutional Formatting Check

**Execute:**
```
1. Read `skills/abnt-formatting/SKILL.md` and `skills/abnt-formatting/references/abnt-nbr-14724-core-requirements.md`
2. Compare the institution's thesis manual vs ABNT NBR 14724:2011
3. Check page setup:
   - Margins: Left 3cm, Right 2cm, Top 3cm, Bottom 2cm (verify the institution's manual)
   - Font: Times New Roman or Arial 12pt (verify the institution's manual)
   - Line spacing: 1.5
4. Check pre-textual elements:
   - Cover (Capa) with the institution's requirements
   - Abstract/Resumo (both languages)
   - Table of contents
5. Check textual structure:
   - Chapter numbering
   - Section hierarchy
6. Check references:
   - ABNT NBR 6023:2023 format
   - Alphabetical order
7. Document any deviations from ABNT (the institution's manual takes precedence)
```

### Step 8: Writing Quality Check

**Execute:**
```
1. Apply Gopen & Swan principles:
   - Subject-verb proximity
   - Stress position
   - Old before new
   - Action in verbs
2. Check language-specific guidelines:
   - PT: Follow the program's Portuguese technical-writing guidance
   - EN: Follow academic writing conventions
3. Verify evidence language strength:
   - Strong evidence → "demonstrates," "shows"
   - Moderate → "suggests," "is consistent with"
   - Weak → "explores," "preliminary evidence"
4. Delete hedging: "suggests" not "may suggest"
5. Be specific: "R² = 0.62" not "performance improved"
```

---

## Phase 5: Validation & Verification

### Step 9: Plagiarism Check (Mandatory)

**Execute:**
```
1. Read `workflows/thesis-plagiarism-check.md`
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
1. Read `workflows/research-analysis-cycle.md` and `workflows/analysis-validation.md`
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
5. Regenerate presentation assets (figures, tables, slides) if needed
```

---
## Phase 6: Final Preparation & Submission

Run the **thesis-submission-preparation** workflow (`workflows/thesis-submission-preparation.md`) in full: Step 11 pre-submission checklist, Step 12 final review, Step 13 submission packaging. Do not start it until every Phase 5 validation (plagiarism check, analysis-thesis alignment) has passed.

## Related Workflows & Skills

### Workflows (in execution order)
1. `workflows/research-analysis-cycle.md` — Method framework and evidence flow
2. `workflows/thesis-chapter-writing.md` — Chapter-type guidance
3. `workflows/analysis-validation.md` — Analysis validation
4. `workflows/thesis-plagiarism-check.md` — Originality
5. `workflows/thesis-plagiarism-prevention.md` — Prevention habits
6. `workflows/thesis-submission-preparation.md` — Submission
7. `workflows/bilingual-notebook-sync.md` — Bilingual sync
8. `workflows/bilingual-doc-sync.md` — Document sync

### Skills (for guidance)
- `skills/abnt-formatting/SKILL.md` — ABNT formatting
- `skills/document-conversion/SKILL.md` — File handling

---

## Quick Decision Tree

```
What thesis task?
├── Writing chapter → workflows/thesis-chapter-writing.md
├── Adding citations → This workflow §Phase 3
├── Method selection → workflows/research-analysis-cycle.md
├── Formatting check → skills/abnt-formatting/SKILL.md
├── Plagiarism scan → workflows/thesis-plagiarism-check.md
├── Bilingual sync → bilingual-notebook-sync.md / bilingual-doc-sync.md
└── Final submission → workflows/thesis-submission-preparation.md
```

---

## Exit Criteria

**Thesis is submission-ready when:**

- [ ] Portuguese version: Complete, formatted, cited
- [ ] English version: Complete, formatted, cited
- [ ] Both versions: Synchronized, identical results
- [ ] Bibliography: Complete, ABNT formatted
- [ ] Plagiarism check: Passed (<15%), documented
- [ ] Formatting: Follows the institution's manual (or documented deviations)
- [ ] Writing quality: Meets academic standards
- [ ] Analysis alignment: Evidence supports claims
- [ ] Supporting materials: Ready (notebooks, maps, dashboard)
- [ ] Submitted: To the institution's submission portal with confirmation
- [ ] **Capture-learning check (ALWAYS-ON)**: if this task involved 2+ failed approaches, a non-obvious fix, a formatting/tool gotcha, or an undocumented requirement, run `workflows/capture-learning.md` before closing. See `skills/error-driven-learning/SKILL.md`.

---

## Critical Success Factors

1. **Bilingual synchronization**: Changes to one version must flow to the other
2. **Evidence traceability**: Every claim must map to notebook/script output
3. **Citation completeness**: Every method, every interpretation, every framework must be cited
4. **Honest limitations**: State what the analysis cannot show
5. **Format compliance**: The institution's manual takes precedence over general ABNT
6. **Plagiarism prevention**: When in doubt, cite; document self-translations
