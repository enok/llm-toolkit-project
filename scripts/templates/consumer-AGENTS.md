<!-- BEGIN LLM TOOLKIT -->
# LLM Toolkit

This repo uses a shared LLM toolkit for local agent assistance. Keep generic reusable guidance in the toolkit, and keep repository-specific architecture, commands, data, and business rules in this repo.

## Always Start Here

1. Read `learnings/INDEX.md` when it exists and the task is non-trivial.
2. Use `docs/llm/toolkit-selection.txt` to understand which shared rules and workflows are prominent for this repo.
3. Read repo-local guidance under `docs/llm/`, especially `docs/llm/rules/` and `docs/llm/workflows/`, before editing shared toolkit files.

## Linked Toolkit Surfaces

- `.agents/skills` -> shared `skills/`
- `.claude/skills` -> shared `skills/`
- `.codex/skills` -> shared `skills/`
- `.windsurf/rules` -> shared `rules/`
- `.windsurf/workflows` -> shared `workflows/`
- `.cursor/rules` -> shared `rules/`
- `.cursor/workflows` -> shared `workflows/`
- `.cursor/agents` -> shared `tool-subagents/`
- `.setup` -> shared setup examples and integration guides

Do not edit through linked directories when the change is repo-specific. Put repo-only instructions in this `AGENTS.md`, `docs/llm/`, or project docs.

## Local Files

- `docs/llm/README.md` - local LLM context layout
- `docs/llm/toolkit-selection.txt` - selected shared toolkit files
- `docs/llm/rules/` - repo-only rules
- `docs/llm/workflows/` - repo-only workflows
- `.cursorignore` and `.cursorindexingignore` - local Cursor visibility filters
- `scripts/sync-llm-configs.*` - wrappers that refresh generated tool surfaces

## Refresh

After changing `docs/llm/toolkit-selection.txt`, repo-local LLM docs, or shared toolkit content, run:

```bash
scripts/sync-llm-configs.sh
```

PowerShell:

```powershell
scripts\sync-llm-configs.ps1
```

Ask by intent: "review my changes", "pre-PR check", "run the right tests", "update docs", "understand this project", or "capture this learning".
<!-- END LLM TOOLKIT -->
