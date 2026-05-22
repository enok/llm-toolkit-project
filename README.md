# LLM Toolkit for Data Science Projects

This repository centralizes local LLM-assisted development assets: rules, workflows, skills, rubrics, setup scripts, and compatibility surfaces for tools such as Codex, Cursor, Claude Code, Windsurf, Copilot, and generic agents.

The toolkit is designed to be reused without copying private project context. Keep generic guidance here; keep repository-specific details in the consumer project's own `AGENTS.md`, `docs/llm/`, or project docs.

## What Is Included

| Area | Path | Purpose |
| --- | --- | --- |
| Rules | `rules/` | Short, broad guidance for code, git, security, release, workflow authoring, and context layering |
| Workflows | `workflows/` | Step-by-step procedures for review, testing, docs, CI, release, toolkit maintenance, and thesis/data work |
| Skills | `skills/` | On-demand capabilities with progressive disclosure through `SKILL.md`, `rules/`, `references/`, and optional agents |
| Tool subagents | `tool-subagents/` | Shared subagent definitions for parallel review, CI triage, docs, security, release, and verification lanes |
| Rubrics | `rubrics/` | Architecture, security, and holistic code-review checklists |
| Integrations | `integrations/` | Generic guides for Jira, Confluence, GitHub, and AWS CLI usage |
| Learnings | `learnings/` | Local trial-and-error discoveries that prevent repeated mistakes |
| Scripts | `scripts/` | Setup, link repair, sync, security checks, index validation, and Markdown-to-PDF helpers |

## Architecture

Canonical content lives in one place:

```text
rules/             broad always-relevant guidance
workflows/         manually invoked procedures
skills/            on-demand capabilities
tool-subagents/    reusable subagent prompts
rubrics/           review scoring/checklists
```

Provider directories are thin compatibility surfaces:

```text
.agents/skills      -> skills/
.claude/skills      -> skills/
.codex/skills       -> skills/
.windsurf/rules     -> rules/
.windsurf/workflows -> workflows/
.cursor/rules       -> rules/
.cursor/workflows   -> workflows/
```

Use `scripts/sync-tool-configs.sh . --skip-agents-md` or `scripts/sync-tool-configs.ps1` to repair generated/symlinked surfaces after changing rules, workflows, skills, or subagents.

## Quick Start

Clone this toolkit next to a consumer project, then run the setup script from the consumer repo:

```bash
../llm-toolkit-project/scripts/setup-repo.sh .
```

Windows PowerShell:

```powershell
..\llm-toolkit-project\scripts\setup-repo.ps1 .
```

The setup scripts create or repair toolkit links, scaffold `docs/llm/`, generate local sync wrappers, update `.gitignore`, and add an `AGENTS.md` toolkit block when needed.

If scripted setup is blocked by local permissions, use `docs/repo-setup-prompt.md` as an LLM-guided repair prompt.

## Selecting Context

Consumer repos should curate shared context in `docs/llm/toolkit-selection.txt`:

```text
rules/code-rules.md
rules/security-check-required.md
workflows/pre-pr-check.md
workflows/run-tests.md
```

Then refresh generated exports from the consumer repo with the generated `scripts/sync-llm-configs.sh` wrapper:

```bash
scripts/sync-llm-configs.sh
```

PowerShell wrapper:

```powershell
scripts\sync-llm-configs.ps1
```

## Useful Entry Points

- `AGENTS.md` - agent guidance for this toolkit repository
- `INTENTS.md` - phrase-to-skill/workflow map
- `workflows/README.md` - workflow catalog
- `skills/ARCHITECTURE.md` - skill structure and progressive loading notes
- `rules/examples/` - templates for consumer-specific rules
- `integrations/README.md` - external tool setup guide index

## Validation

Before committing toolkit changes, run:

```powershell
.\scripts\validate-toolkit-indexes.ps1
.\scripts\security-check-toolkit.ps1
```

Git Bash:

```bash
./scripts/validate-toolkit-indexes.sh
./scripts/security-check-toolkit.sh
```

The validation gate checks skill frontmatter, referenced paths, duplicate cloud-sync files, and optional project-specific leak patterns through `FORBIDDEN_PROJECT_PATTERNS`.

## Safety

- Do not commit secrets, credentials, private hostnames, ticket-specific content, or copied consumer payloads.
- Do not commit cloud-sync duplicates such as `file (1).md`.
- Keep generated consumer exports local unless they are intentionally part of this toolkit.
- Prefer links and generated compatibility surfaces over duplicated tool-specific copies.
