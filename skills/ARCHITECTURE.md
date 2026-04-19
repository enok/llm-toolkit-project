# Skills Architecture

## Single Source of Truth

Skills and workflows live in exactly ONE place each:

```
llm-toolkit-project/
├── skills/                   # CANONICAL skills (source of truth)
│   ├── best-practices/
│   │   ├── SKILL.md          # Summary (loaded when skill activates, ~5K tokens)
│   │   ├── AGENTS.md         # Full compiled doc (optional, legacy)
│   │   ├── metadata.json     # Version, abstract
│   │   ├── rules/            # Fine-grained rules (on-demand, ~500 tokens each)
│   │   │   ├── solid-single-responsibility.md
│   │   │   └── arch-layered.md
│   │   └── references/       # Deep reference material (on-demand)
│   │       └── rules.md
│   └── ... (49 skills total)
├── workflows/                # CANONICAL workflows (source of truth)
│   ├── review.md
│   ├── ticket-research.md
│   └── ... (34 workflows)
```

## Agent Directories Are Junctions

All agent-specific directories are **Windows junctions** (or symlinks on Linux/macOS) pointing to the canonical locations:

```
.agents/skills    -> skills/       (junction)
.claude/skills    -> skills/       (junction)
.codex/skills     -> skills/       (junction)
.windsurf/workflows -> workflows/  (junction)
```

**No duplicate content.** Edit a file in `skills/xxx/` and all agents immediately see the change.

## Progressive Disclosure (Less Tokens)

Each skill uses three levels of progressive disclosure:

| Level | Content | When Loaded | Approx Tokens |
|-------|---------|-------------|---------------|
| 1 | `name` + `description` in frontmatter | Startup (all skills) | ~100 per skill |
| 2 | `SKILL.md` body | When skill activates | <5000 per skill |
| 3 | `rules/*.md`, `references/*.md` | When specifically needed | ~500-3000 each |

**Goal:** Only the metadata of all skills lives in context. Full content loads on-demand.

## Rules → Skills Migration

The old `.windsurf/rules/` directory (with `trigger: always_on`) has been **dissolved** into skills:

- Rules that matched a skill name → merged into `skills/<name>/references/rules.md`
- Orphan rules → merged into the most relevant skill's `references/`
- All content now loads **on-demand**, not always

## Creating a New Skill

1. Create directory: `skills/new-skill-name/`
2. Add `SKILL.md` with frontmatter (`name`, `description`)
3. Add optional subdirectories:
   - `rules/` for fine-grained prefixed rules (e.g., `error-classification-code.md`)
   - `references/` for deep reference material
4. The skill is **automatically visible** to all agents (via junctions)

## Regenerating Junctions

If you clone fresh and junctions are missing:

```cmd
scripts\_create-junctions.cmd
```

Or for consumers:

```cmd
..\llm-toolkit\scripts\setup-repo.cmd .
```

## Validation

Check no duplicates exist:

```bash
# Canonical only
find skills/ -name SKILL.md | wc -l   # 49 (or current count)
find workflows/ -name "*.md" | wc -l  # 34 (or current count)

# Agent dirs must be junctions
ls -la .agents/skills .claude/skills .codex/skills .windsurf/workflows
# Should all show "->" indicating link/junction
```
