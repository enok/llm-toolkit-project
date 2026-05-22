---
name: llm-context-engineering
description: Design lean, provider-agnostic LLM context surfaces. Use when editing AGENTS.md, rules, workflows, skills, memories, MCP/tool docs, or when reducing prompt bloat and moving knowledge to on-demand loading.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# LLM Context Engineering

## Core model

Use progressive disclosure:

1. **Root instructions** — small, always-loaded operating rules and indexes.
2. **Rules** — short behavioral constraints that apply broadly.
3. **Workflows** — manually invoked step-by-step procedures.
4. **Skills** — automatically matched capabilities with optional references/templates/scripts.
5. **Learnings** — searchable evidence from trial-and-error; read only when relevant.

## Decisions

| Need | Prefer |
| --- | --- |
| Always applies to every task | Rule or short AGENTS entry |
| Specialized repeatable task | Skill |
| Human-triggered runbook | Workflow |
| One-off project detail | Consumer repo docs or `docs/llm/` |
| Failed attempts and happy path | Learning |
| Provider-specific discovery | Thin compatibility pointer or symlink |

## Checklist

- Keep `AGENTS.md`, `README.md`, and `INTENTS.md` as indexes, not full manuals.
- Put provider-specific content behind thin compatibility layers: `.cursor/`, `.windsurf/`, `.claude/`, `.codex/`.
- Use generic names and descriptions; avoid customer, branch, ticket, environment, or repo-specific names in shared toolkit files.
- Ensure skill folder name equals `SKILL.md` frontmatter `name`.
- Front-load trigger words in skill descriptions so tools can match them from metadata alone.
- Keep supporting references out of the always-loaded surface.
- If a skill includes scripts, make the primary executable path work on Windows, Linux, and macOS. Prefer portable Python/Node/compiled CLIs; keep OS-specific shell or PowerShell files as wrappers only.
- Include cross-platform usage examples in skill references when path syntax, quoting, or interpreter names differ.
- Validate indexes after adding, renaming, or deleting rules/workflows/skills.

## When not to use shared toolkit files

If guidance contains real internal hostnames, Jira ticket IDs, customer data, repo-specific commands, or product-specific business rules, place it in the consumer repository or in a learning with enough context to remain evidence rather than policy.
