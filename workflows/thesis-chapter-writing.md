---
description: Chapter-by-chapter thesis writing guidance by chapter type (introduction, literature review, methodology, results, discussion, conclusion) - Step 4 of thesis-writing-main
---

# Thesis Chapter Writing (By Type)

Step 4 of `workflows/thesis-writing-main.md` (Phase 2: Content Development), extracted so the parent stays within the workflow size limit. Apply the chapter-type guidance below to the chapter identified in Step 1, in the language scope decided in Step 3.

## Step 4: Chapter Writing (By Type)

#### Chapter 1: Introduction (Introdução)

**Required elements:**
- Contexto (Context)
- Problema (Problem statement)
- Questão de pesquisa (Research question)
- Objetivos geral e específicos (Objectives)
- Justificativa (Justification)
- Delimitação (Scope/delimitation)

**Execute:**
```
1. Read the institution's thesis manual for the required introduction structure
2. Use 5-sentence abstract formula for problem statement
3. Cite methodology sources:
   - Gil (2010), Lakatos & Marconi (2010) — Research design
   - Domain literature that frames the problem context
4. Write in Portuguese (primary)
5. Sync to English (secondary)
6. Verify bilingual alignment
```

#### Chapter 2: Material and Methods (Material e Métodos)

**Required sections:**
- Data sources (e.g., public or institutional sources)
- Data architecture (Bronze/Silver/Gold)
- Analytical methods (Statistics, ML, Clustering)
- Software and tools

**Execute:**
```
1. Read `workflows/research-analysis-cycle.md` (method choice and baselines)
2. Map methods to references:
   - Descriptive stats → Bussab & Morettin (2017)
   - Regression → Wooldridge (2020)
   - ML → James et al. (2021)
   - Clustering → Hartigan & Wong (1979), Rousseeuw (1987)
3. Write methodology with proper citations
4. Include: Data scope, period, variables
5. Sync English version
6. Verify method names consistent across languages
```

#### Chapter 3: Results and Discussion (Resultados e Discussão)

**Required sections:**
- Descriptive analysis
- Statistical modeling results
- Machine learning results
- Clustering analysis
- Interpretation and implications

**Execute:**
```
1. Read the project's findings summary (e.g., `docs/<findings-summary>.md`) — Extract findings
2. For each finding:
   - State statistic (r, β, p, R²)
   - Cite interpretation framework
   - Cite the literature that supports the interpretation
3. Create/update tables and figures
4. Write results narrative in Portuguese
5. Translate to English (maintain identical numbers)
6. Verify: Same statistics in both versions
```

#### Chapter 4: Conclusion (Conclusão)

**Required sections:**
- Summary of findings
- Limitations
- Policy implications
- Future work

**Execute:**
```
1. Synthesize key findings from Chapter 3
2. Cite limitation literature (Wooldridge, 2020 — causality)
3. Connect to the domain literature
4. Write limitations honestly
5. Propose future work with method citations
6. Sync both languages
```

---

