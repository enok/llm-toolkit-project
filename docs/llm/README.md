# Repo-Local LLM Configuration

This directory contains repository-specific LLM configuration that complements the shared toolkit linked through:

- `.agents/`
- `.claude/`
- `.codex/`
- `.cursor/`
- `.windsurf/`
- `.setup/`

Do not place repo-only customizations inside those linked directories. Doing so would modify the shared toolkit checkout instead of this repository.

## Local Layout

- `docs/llm/toolkit-selection.txt`: curated shared-toolkit profile for this repo
- `docs/llm/scripts/`: helper scripts that build or refresh local analytical references
- `learnings/`: committed trial-and-error knowledge (see `skills/error-driven-learning/SKILL.md`)

## Shared Toolkit Selection

This repository keeps generic reusable guidance in the shared toolkit and narrows local usage with:

- `docs/llm/toolkit-selection.txt`
- `.cursorignore`
- `.cursorindexingignore`

`docs/llm/toolkit-selection.txt` is the source of truth for which shared rules and workflows this repository wants to prioritize. Update that file when the thesis project changes scope, and then refresh generated exports from the repo root with:

```powershell
.\scripts\sync-llm-configs.ps1
```

Or, in Git Bash:

```bash
./scripts/sync-llm-configs.sh
```

## Repo-Local Guidance

Keep generic guidance in the shared toolkit. Add repo-only guidance here when it would be incorrect or too specific for other projects, for example:

- domain vocabulary for Brazilian public procurement and compliance data (via `municipal-compliance-analysis` skill)
- repository-specific data contracts and staging conventions (via `data-pipeline-boundaries` skill)
- notebook conventions that depend on this repo's folders, datasets, or outputs (via `notebook-analysis` skill)
- AWS orchestration guidance that reflects this repo's current shell-script ETL and minimal `infra/` baseline (via `aws-airflow-terraform-project` skill)
- documentation expectations tied to the thesis deliverables (via `documentation-governance` skill)
- USP MBA course-to-method mapping that only applies to this thesis project (via `course-material-grounding` and `usp-mba-course-context` skills)
- mandatory local security-check gates (via `security-checkpoint` skill)
- trial-and-error discoveries captured as committed learnings for cross-session, cross-tool reuse

## Learnings

The `learnings/` directory at the repo root captures trial-and-error discoveries as committed markdown files. Any LLM tool can read these files to skip directly to the correct solution.

- Before starting a task, check `learnings/` for relevant prior discoveries.
- When recovering from trial-and-error, use the `capture-learning` workflow to save the knowledge.
- See `skills/error-driven-learning/SKILL.md` for the governance rule.

## Rubrics

The shared toolkit includes structured review rubrics for architecture, security, and holistic code review. These are referenced by the `review` and `review-and-fix` workflows:

- `rubrics/architecture.md`
- `rubrics/code-review-checklist.md`
- `rubrics/security.md`

## Mandatory Security Gate

Security review is mandatory for every new or modified code path, script, workflow, rule, skill, or operational document in this repository.

Run:

```bash
./scripts/security_check_this_repo.sh
```

For related work in `dev-tools`, use:

```bash
./scripts/security_check_dev_tools.sh /path/to/dev-tools
```

See:

- `security-checkpoint` skill — Repository-specific security requirements

## Example Templates

Templates remain available under `.setup/examples/`, but they are not the source of truth for this repository. All rules, skills, and workflows are now in the shared toolkit and accessible via `.agents/skills/` and `.windsurf/workflows/`.

If the templates become noisy in the IDE, hide `.setup/examples/` locally instead of deleting anything from the linked toolkit.

## Integrations

The active integrations for this repository are:

- AWS CLI
- GitHub CLI

Jira and Confluence are not used for this project. Their guides may still exist in `.setup/integrations/` because that directory is linked from the shared toolkit, so hide them locally in the IDE if they are distracting.

## Workflow Customization

All workflows are now in the shared toolkit under `workflows/` and accessible via `.windsurf/workflows/` junction.

## Recommended Skills (via Shared Toolkit)

Start with these skills for thesis-specific support (activate via your LLM tool):

- `project-overview` — Repository structure and scope
- `course-material-grounding` — USP MBA course corpus alignment
- `usp-mba-course-context` — Method selection and writing guidance
- `tcc-deliverables` — Thesis deliverable expectations
- `security-checkpoint` — Mandatory security review
- `data-pipeline-boundaries` — Bronze/Silver/Gold boundaries
- `aws-airflow-terraform-project` — Infrastructure guidance
- `documentation-governance` — Documentation and data governance

## Recommended Workflows (via Shared Toolkit)

Access via `.windsurf/workflows/`:

- `project-execution-main.md` — Primary orchestration for technical work
- `thesis-writing-main.md` — Primary orchestration for thesis writing
- `course-material-grounding.md` — Course material alignment workflow
- `tcc-method-selection.md` — Method selection guidance
- `tcc-analysis-and-writing-sync.md` — Analysis-writing alignment
- `refresh-usp-mba-course-context.md` — Course context refresh

## Recommended References (via Shared Toolkit)

Access via `.agents/skills/*/references/`:

- `usp-mba-course-map.md` — Curated USP MBA course mapping
- `usp-mba-course-inventory.generated.md` — Full course inventory
- `usp-mba-tcc-examples.md` — TCC examples and templates

## Additional Workflows (via Shared Toolkit)

**Complete workflow list:**
- `data-source-ingestion.md` — Bronze layer data ingestion
- `pipeline-change-project.md` — Project-specific pipeline changes
- `bilingual-notebook-sync.md` — EN/pt-BR notebook synchronization
- `aws-airflow-terraform-project.md` — Project-specific infrastructure guidance
- `thesis-completion-guide.md` — Chapter structure and completion
- `thesis-bibliography-integration.md` — Citation management
- `thesis-plagiarism-check.md` — Originality verification
- `tcc-formatting-abnt-review.md` — ABNT formatting compliance
