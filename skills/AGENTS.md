# Agent Skills

This directory contains **symlinks** to canonical skills in `../../skills/`.

## Unified Architecture

Skills are authored once in the canonical `skills/` directory at the repository root, then symlinked here for agent compatibility:

```
llm-toolkit-project/
├── skills/                  # Canonical skills (source of truth)
│   ├── best-practices/
│   ├── python-best-practices/
│   └── ...
└── .agents/
    └── skills/ -> ../../skills/   (this symlink)
```

## Specification

Skills follow the [Agent Skills specification](https://agentskills.io/specification).
Each skill is a folder containing a `SKILL.md` file and optional subdirectories.

## Directory Structure

```
skill-name/
├── SKILL.md              # Required — frontmatter + instructions
├── references/           # Optional — domain-specific reference docs
│   ├── api-reference.md
│   └── data-models.md
├── scripts/              # Optional — executable scripts
│   └── setup.sh
└── assets/               # Optional — templates, images, data files
    └── config-template.yaml
```

## SKILL.md Format

```markdown
---
name: skill-name
description:
  What this skill does and when to use it. Include specific keywords
  that help agents identify relevant tasks. 1-1024 characters.
---

# Skill Title

Brief overview of the skill's purpose.

## When to Apply

- Bullet list of situations where this skill is relevant

## Reference Files

| File                          | Description                |
| ----------------------------- | -------------------------- |
| [file.md](references/file.md) | What this reference covers |

## Quick Reference

Inline summary of the most critical information (<5000 tokens total for SKILL.md body).
```

## Frontmatter Rules

- **name** (required): 1-64 chars, lowercase alphanumeric + hyphens only, must match folder name
- **description** (required): 1-1024 chars, describe what the skill does AND when to use it
- **metadata** (optional): key-value pairs for additional metadata (not currently used)

## Progressive Disclosure

Skills use three levels of progressive disclosure:

1. **Metadata** (~100 tokens): `name` and `description` loaded at startup for all skills
2. **Instructions** (<5000 tokens recommended): Full `SKILL.md` body loaded when skill is activated
3. **Resources** (as needed): Files in `references/`, `scripts/`, `assets/` loaded only when required

Keep `SKILL.md` body concise — put detailed reference material in `references/` files.

## Reference Files

- Place in `references/` subdirectory
- Use YAML frontmatter with `title` and `tags` fields
- Link from SKILL.md using relative markdown links: `[file.md](references/file.md)`

## Symlink Convention

Skills are authored in `skills/` (root) and symlinked to agent directories:

```bash
# Canonical location
llm-toolkit-project/skills/skill-name/

# Symlinked to agent directories
llm-toolkit-project/.agents/skills/skill-name -> ../../skills/skill-name
llm-toolkit-project/.claude/skills/skill-name -> ../../skills/skill-name
```

This eliminates duplication: edit in `skills/`, all agents see the change.

If symlinks are not supported in the current filesystem, mirror by copy instead:

```bash
./.codex/sync-shared-skills.sh --copy --no-global
```

## Checklist

When creating a new skill:

1. **Create in canonical location**: `skills/skill-name/`
2. Create `SKILL.md` with required frontmatter (`name`, `description`)
3. Reference detailed rules via `> **Reference**: see rules/xxx.md`
4. Keep SKILL.md body under 5000 tokens — full rules live in `rules/`
5. Create symlinks: `cd .agents/skills && ln -s ../../skills/skill-name skill-name`
6. Verify the `name` field matches the folder name exactly

## No Duplication

- **Skills** in `skills/` reference **Rules** in `rules/`
- **Skills** reference **Workflows** in `workflows/`
- Do NOT duplicate content from rules into skills
- Use `> **Reference**: For complete rules, see rules/xxx.md` pattern
