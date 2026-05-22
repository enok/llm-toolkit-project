# Skills

Skills are on-demand capabilities. Each skill lives in `skills/<skill-name>/SKILL.md` and may include optional `rules/`, `references/`, `scripts/`, or `agents/`.

## Conventions

- Folder name must match the `name:` field in `SKILL.md`.
- Keep the frontmatter description short and trigger-rich so agents can select the skill from metadata.
- Put broad always-on behavior in `rules/`; put specialized procedures and examples inside the relevant skill.
- Keep project-specific details out of shared skills unless they are explicitly scoped to this toolkit's data-science/thesis context.

## Validation

Run from the repository root:

```bash
./scripts/validate-toolkit-indexes.sh
```

PowerShell:

```powershell
.\scripts\validate-toolkit-indexes.ps1
```

See `skills/ARCHITECTURE.md` for the full structure.
