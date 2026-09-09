---
description: Orchestrate infrastructure, code, data pipeline, and notebook work for the public-compliance data-analysis project (entry point for broad technical tasks)
---

# Project Execution Main Workflow

**Purpose**: Orchestrate all infrastructure, code, data pipeline, and Jupyter notebook work for the Public Compliance Data Analysis project.

**Scope**: Bronze/Silver/Gold data pipeline, ingestion, processing, analysis notebooks, and infrastructure management.

**Trigger**: Use this workflow when implementing technical changes to the project, adding features, fixing bugs, or modifying data pipelines.

---

## Phase 0: Consult Learnings (ALWAYS-ON)

**Before any other step, scan `learnings/INDEX.md`** for entries whose tags, title, or category match the current task. If a match is found, read that learning and follow its *Solution*; avoid the approaches listed under *Failed Approaches*.

This phase is non-negotiable — it is the agent's auto-improvement loop. See `skills/error-driven-learning/SKILL.md`.

---

## Phase 1: Discovery & Planning

### Step 1: Understand the Task

**Determine what type of work is needed:**

| Task Type | Entry Point | Key Workflow |
|-----------|-------------|--------------|
| **New data source** | `data-source-ingestion.md` | Bronze ingestion |
| **Pipeline change** | `pipeline-change.md` | Bronze/Silver/Gold |
| **Bronze ingestion bug** | `data-source-ingestion.md` §Troubleshooting | IBGE/Transparency/CGU |
| **Silver transformation** | `pipeline-change.md` §Silver Layer | Normalization |
| **Gold features** | `pipeline-change.md` §Gold Layer | Feature engineering |
| **Infrastructure (AWS)** | `aws-airflow-terraform-change.md` | Terraform/S3 |
| **Analysis notebook** | `notebook-analysis.md` | EDA/Statistics/ML |
| **Bilingual notebook sync** | `bilingual-notebook-sync.md` | EN/pt-BR pairs |
| **Security incident** | `security-check-required.md` | Security response |
| **Environment issue** | `workflows/environment-diagnose.md` | Setup/debug |

### Step 2: Context Gathering

**Read required context based on task type:**

**For data/pipeline tasks:**
- [ ] `project-overview` skill — Technical scope
- [ ] `config/ibge_metadata.json` — IBGE contracts
- [ ] `config/transparency_metadata.json` — Transparency contracts
- [ ] `config/silver_schemas.json` — Silver expectations

**For infrastructure tasks:**
- [ ] `aws-airflow-terraform-project` skill — AWS/Terraform rules
- [ ] `infra/main.tf` — Current infrastructure

**For notebook tasks:**
- [ ] `notebooks/` — Existing notebooks
- [ ] `src/analysis/data_loader.py` — Data access patterns
- [ ] `usp-mba-course-map` reference — Course alignment

### Step 3: Impact Assessment

**Check cross-cutting concerns:**

- [ ] Does this affect Bronze/Silver/Gold boundaries? → See `data-pipeline-boundaries` skill
- [ ] Does this require bilingual sync? → See `bilingual-notebook-sync.md`
- [ ] Does this change data contracts? → See `data-pipeline-contracts` rule
- [ ] Does this affect thesis evidence? → See `tcc-analysis-and-writing-sync.md`

---

## Phase 2: Implementation

### Step 4: Execute by Task Type

#### Data Ingestion (Bronze)

**If adding/modifying data source:**
```
1. Read `data-source-ingestion.md`
2. Check contracts in `config/`
3. Modify `src/ingestion/<source>_client.py`
4. Update `scripts/01_bronze_ingestion.sh`
5. Add tests in `tests/ingestion/`
6. Run: ./scripts/01_bronze_ingestion.sh --validate
7. Update `docs/01_BRONZE_LAYER.md` and `01_BRONZE_LAYER.pt-BR.md`
```

#### Pipeline Transformation (Silver/Gold)

**If modifying transformations:**
```
1. Read `pipeline-change.md`
2. Identify layer: Bronze → Silver → Gold
3. Modify `src/processing/<layer>_transformer.py`
4. Update orchestration script
5. Run tests: pytest tests/processing/
6. Validate output schemas
7. Update layer documentation (EN + pt-BR)
```

#### Analysis Notebooks

**If adding/modifying notebooks:**
```
1. Read `notebook-analysis.md`
2. Check existing notebooks in `notebooks/`
3. Create/modify notebook
4. If bilingual: Read `bilingual-notebook-sync.md`
5. Sync English ↔ Portuguese versions
6. Validate execution: jupyter nbconvert --execute
7. Clear outputs before commit
```

#### Infrastructure (AWS/Terraform)

**If modifying infrastructure:**
```
1. Read `aws-airflow-terraform-change.md`
2. Read `aws-airflow-terraform-project` skill
3. Modify `infra/main.tf`
4. Run: terraform plan
5. Review changes
6. Run: terraform apply (if approved)
7. Update infrastructure docs
```

---

## Phase 3: Validation & Testing

### Step 5: Security Check (Mandatory)

**Always run before committing:**
```bash
./scripts/security_check_this_repo.sh
```

**Verify:**
- [ ] No secrets in code
- [ ] No credentials in notebooks
- [ ] Shell scripts pass shellcheck
- [ ] Python passes bandit

**If failures:**
- Fix immediately
- Re-run check
- Document any exceptions

**Reference**: `security-check-required.md`

### Step 6: Testing

**Run appropriate test suites:**

| Change Type | Test Command |
|-------------|--------------|
| Ingestion | `pytest tests/ingestion/ -v` |
| Processing | `pytest tests/processing/ -v` |
| Analysis | `pytest tests/analysis/ -v` |
| Full pipeline | `./scripts/01_bronze_ingestion.sh --dry-run` |
| All | `pytest tests/ -v` |

**Reference**: `workflows/run-tests.md`

### Step 7: Analysis Validation (If Applicable)

**If changes affect analytical outputs:**
```
1. Read `analysis-validation.md`
2. Verify reproducibility
3. Check evidence traceability
4. Validate validity threats assessment
5. Confirm course material alignment
```

---

## Phase 4: Documentation & Sync

### Step 8: Documentation Update

**Update all relevant docs:**

| Change Type | Documentation to Update |
|-------------|------------------------|
| Bronze | `docs/01_BRONZE_LAYER.md` + `.pt-BR.md` |
| Silver | `docs/02_SILVER_LAYER.md` + `.pt-BR.md` |
| Gold | `docs/03_GOLD_LAYER.md` + `.pt-BR.md` |
| Analysis | `docs/thesis_conclusion.md` (if findings change) |
| README | `README.md` + `README.pt-BR.md` |

**Reference**: `documentation-sync.md`

### Step 9: Bilingual Sync (If Applicable)

**If changes touch bilingual surfaces:**
```
1. Read `bilingual-notebook-sync.md`
2. Identify affected pairs:
   - Notebooks: `notebooks/*.ipynb` ↔ `notebooks/pt-BR/*.ipynb`
   - Docs: `docs/*.md` ↔ `docs/*.pt-BR.md`
   - README: `README.md` ↔ `README.pt-BR.md`
3. Apply changes to English version first
4. Mirror changes to Portuguese version
5. Verify synchronization
```

**Reference**: `workflows/bilingual-doc-sync.md`

### Step 10: Thesis Impact Check

**If analytical evidence changes:**
```
1. Read `tcc-analysis-and-writing-sync.md`
2. Map change to thesis chapter:
   - Data boundary → Introduction (scope)
   - Preprocessing → Material and Methods
   - Method change → Material and Methods
   - Results → Results and Discussion
   - Interpretation → Results/Conclusion
3. Update `docs/thesis_conclusion.md`
4. Update `docs/city_thesis_conclusion_addendum.md` (if city-level)
5. Regenerate presentation assets if needed:
   python scripts/build_thesis_presentation_assets.py
```

---

## Phase 5: Commit & Delivery

### Step 11: Pre-Commit Checklist

**Verify before committing:**

- [ ] Security check passed
- [ ] Tests pass
- [ ] Documentation updated (EN + pt-BR if applicable)
- [ ] Bilingual sync verified (if applicable)
- [ ] Thesis impact assessed
- [ ] No secrets/credentials in code
- [ ] Notebook outputs cleared

### Step 12: Commit Strategy

**Structure commits by category:**

```
TCC-XXX: Category description

1. LLM configs (if modified)
2. Documentation (EN + pt-BR)
3. Pipeline/infra config
4. Application code + tests
```

**Reference**: `rules/git-conventions.md`

### Step 13: Final Validation

**Before marking complete:**
```bash
# Run full security check
./scripts/security_check_this_repo.sh

# Run full test suite
pytest tests/ -v

# Verify bilingual sync (if applicable)
# Check notebooks run
jupyter nbconvert --execute notebooks/01_*.ipynb

# Verify thesis docs consistency
cat docs/thesis_conclusion.md | head -50
```

---

## Related Workflows & Skills

### Workflows (in execution order)
1. `data-source-ingestion.md` — Data ingestion
2. `pipeline-change.md` — Pipeline modifications
3. `aws-airflow-terraform-change.md` — Infrastructure
4. `workflows/notebook-analysis.md` — Notebook development
5. `bilingual-notebook-sync.md` — Bilingual sync
6. `analysis-validation.md` — Analysis quality
7. `security-check-required.md` — Security validation
8. `documentation-sync.md` — Documentation
9. `tcc-analysis-and-writing-sync.md` — Thesis alignment

### Skills (for context)
- `project-overview` skill — Technical scope
- `data-pipeline-boundaries` skill — Layer boundaries
- `aws-airflow-terraform-project` skill — AWS guidance
- `data-pipeline-contracts` rule — Contract governance
- `analytics-discipline` rule — Analysis hygiene

### Skills (for reusable patterns)
- `.agents/skills/research-thesis-support/SKILL.md` — Thesis patterns
- `.agents/skills/document-conversion/SKILL.md` — File conversion

---

## Quick Decision Tree

```
What are you working on?
├── Data ingestion → data-source-ingestion.md
├── Pipeline change → pipeline-change.md
├── Infrastructure → aws-airflow-terraform-change.md
├── Analysis/ML → notebook-analysis.md
├── Bilingual sync → bilingual-notebook-sync.md
├── Security issue → security-check-required.md
└── Environment → environment-diagnose.md
```

---

## Exit Criteria

**Task is complete when:**
- [ ] Code implemented and tested
- [ ] Security check passed
- [ ] Documentation updated (EN + pt-BR)
- [ ] Bilingual sync verified (if applicable)
- [ ] Thesis impact documented (if applicable)
- [ ] Committed following git conventions
- [ ] No breaking changes without coordination
- [ ] **Capture-learning check (ALWAYS-ON)**: if this task involved 2+ failed approaches, a non-obvious fix, a platform/toolchain gotcha, or an API/config surprise, run `workflows/capture-learning.md` before closing. See `skills/error-driven-learning/SKILL.md`.
