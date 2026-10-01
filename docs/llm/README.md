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

- repository-specific data contracts and staging conventions (via `data-pipeline-boundaries` skill)
- notebook conventions that depend on this repo's folders, datasets, or outputs (via `notebook-analysis` skill)
- AWS orchestration guidance that reflects this repo's current shell-script ETL and minimal `infra/` baseline (via `aws-airflow-terraform-project` skill)
- documentation expectations tied to the thesis deliverables (via `documentation-governance` skill)
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
./scripts/security-check-toolkit.sh
```

PowerShell:

```powershell
.\scripts\security-check-toolkit.ps1
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

All workflows are now in the shared toolkit under `workflows/` and accessible via `.windsurf/workflows/` and `.cursor/workflows/` links.

## Recommended Skills (via Shared Toolkit)

Start with these skills for repository-specific support (activate via your LLM tool):

- `security-checkpoint` — Mandatory security review
- `data-pipeline-boundaries` — Bronze/Silver/Gold boundaries
- `aws-airflow-terraform-project` — Infrastructure guidance
- `documentation-governance` — Documentation and data governance

## Recommended Workflows (via Shared Toolkit)

Access via `.windsurf/workflows/`:

- `project-execution-main.md` — Primary orchestration for technical work
- `thesis-writing-main.md` — Primary orchestration for thesis writing

## Recommended References

Skill-specific references live under `.agents/skills/*/references/`. Repository-specific reference material lives in `docs/llm/references/` (see its `README.md`).

## Additional Workflows (via Shared Toolkit)

**Complete workflow list:**
- `data-source-ingestion.md` — Bronze layer data ingestion
- `pipeline-change-project.md` — Project-specific pipeline changes
- `bilingual-notebook-sync.md` — EN/pt-BR notebook synchronization
- `aws-airflow-terraform-project.md` — Project-specific infrastructure guidance
- `thesis-plagiarism-check.md` — Originality verification
