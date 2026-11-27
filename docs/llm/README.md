# Repo-Local LLM Configuration

This directory contains repository-specific LLM configuration that complements the shared toolkit linked through:

- `.agents/`
- `.claude/`
- `.codex/`
- `.cursor/`
- `.windsurf/`

Do not place repo-only customizations inside those linked directories. Doing so would modify the shared toolkit checkout instead of this repository.

## Local Layout

- `docs/llm/toolkit-selection.txt`: curated shared-toolkit profile for this repo
- `learnings/`: short-lived intake for trial-and-error lessons whose owner is not yet clear (see `skills/error-driven-learning/SKILL.md`)

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

- repository-specific data contracts and staging conventions
- notebook conventions that depend on this repo's folders, datasets, or outputs
- AWS orchestration guidance that reflects this repo's current shell-script ETL and minimal `infra/` baseline (via `aws-airflow-terraform-project` skill)
- documentation expectations tied to the thesis deliverables
- mandatory local security-check gates
- trial-and-error discoveries written into the owning skill, rule or workflow for cross-session, cross-tool reuse

## Learnings

Trial-and-error discoveries are written into the skill, rule or workflow that owns them. The `learnings/` directory at the repo root is only a short-lived intake for a lesson whose owner is not yet clear; each item is migrated into its owner and deleted.

- Before starting a task, read the owning assets' known pitfalls and `learnings/INDEX.md` (pending items).
- When recovering from trial-and-error, use the `capture-learning` workflow to save the knowledge.
- See `skills/error-driven-learning/SKILL.md` for the governance rule.

## Rubrics

The shared toolkit includes a structured review rubric for architecture severity calls:

- `rubrics/architecture.md`

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

See `rules/security-check-required.md`.

## Example Templates

Templates remain available under `rules/examples/` in the shared toolkit, but they are not the source of truth for this repository. All rules, skills, and workflows are now in the shared toolkit and accessible via `.agents/skills/` and `.windsurf/workflows/`.

If the templates become noisy in the IDE, hide `rules/examples/` locally instead of deleting anything from the linked toolkit.

## Integrations

The active integrations for this repository are:

- AWS CLI
- GitHub CLI

Jira and Confluence are not used for this project. Their guides may still exist in the shared toolkit's `integrations/` directory, so hide them locally in the IDE if they are distracting.

## Workflow Customization

All workflows are now in the shared toolkit under `workflows/` and accessible via the `.windsurf/workflows/` link.

## Recommended Skills (via Shared Toolkit)

Start with these skills for repository-specific support (activate via your LLM tool):

- `aws-airflow-terraform-project` — Infrastructure guidance

## Recommended Workflows (via Shared Toolkit)

Access via `.windsurf/workflows/`:

- `project-execution-main.md` — Primary orchestration for technical work
- `thesis-writing-main.md` — Primary orchestration for thesis writing

## Recommended References

Skill-specific references live under `.agents/skills/*/references/`. Repository-specific reference material lives in `docs/llm/references/` (see its `README.md`).

## Additional Workflows (via Shared Toolkit)

**Complete workflow list:**
- `data-source-ingestion.md` — Bronze layer data ingestion
- `aws-airflow-terraform-project.md` — Project-specific infrastructure guidance
- `thesis-plagiarism-check.md` — Originality verification
