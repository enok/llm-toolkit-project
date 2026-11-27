---
description: Orchestrate infrastructure, code, data pipeline, and notebook work for the data-analysis project (entry point for broad technical tasks)
---

# Project Execution Main Workflow

Entry point for technical changes to the data-analysis project: Bronze/Silver/Gold pipeline, ingestion, processing, analysis notebooks, and infrastructure.

## 0. Consult learnings (always-on)

Before any other step, scan `learnings/INDEX.md` for matching entries, follow their *Solution*, and avoid their *Failed Approaches* (`skills/error-driven-learning/SKILL.md`).

## 1. Route

| Work | Follow |
| --- | --- |
| New data source / Bronze bug | `workflows/data-source-ingestion.md` |
| Silver/Gold or contract change | `workflows/data-pipeline-change.md` (+ `config/<source>_metadata.json`, `config/silver_schemas.json`) |
| AWS / Terraform | `workflows/aws-airflow-terraform-change.md` and the `aws-airflow-terraform-project` skill |
| Analysis notebook | `workflows/notebook-analysis-update.md`, `skills/jupyter-notebook/SKILL.md` |
| Security incident | `workflows/security-check-required.md` |
| Environment issue | `workflows/environment-diagnose.md` |

## 2. Validate

- **Security (mandatory, before every commit):** run the repository's security script (`./scripts/security_check_this_repo.sh`); no secrets in code or notebook outputs, shellcheck and bandit clean. Fix and re-run on failure; document any exception.
- **Tests:** the suite for the touched layer (`pytest tests/<ingestion|processing|analysis>/`), `pytest tests/` before completion; Terraform changes need a reviewed `terraform plan`, and `apply` only when approved.
- **Analytical outputs changed:** confirm reproducibility, evidence traceability, the validity-threats assessment, and course-material alignment.

## 3. Docs, bilingual pairs, thesis

- Update the layer docs (`docs/0N_<LAYER>_LAYER.md`), README, and `docs/<findings-summary>.md` when findings change.
- Bilingual pairs (`notebooks/*.ipynb` ↔ `notebooks/pt-BR/*.ipynb`, `docs/*.md` ↔ `docs/*.pt-BR.md`, `README.md` ↔ `README.pt-BR.md`): change English first, mirror to pt-BR, verify both match.
- If analytical evidence changes, map it to the thesis chapter (data boundary → Introduction; preprocessing or method → Material and Methods; results and interpretation → Results and Discussion / Conclusion), update the findings summary, and regenerate presentation assets if needed.

## 4. Commit and exit

Commit per `rules/git-conventions.md`, grouped: LLM configs, docs (EN + pt-BR), pipeline/infra config, code + tests. Done when code is tested, the security check passed, docs and bilingual pairs are in sync, notebook outputs are cleared and notebooks execute, thesis impact is recorded, and there are no uncoordinated breaking changes. **Capture-learning check (always-on):** after 2+ failed approaches, a non-obvious fix, a toolchain gotcha, or a config surprise, run `workflows/capture-learning.md` before closing.
