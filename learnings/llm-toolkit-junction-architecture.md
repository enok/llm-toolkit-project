---
title: Multi-repo LLM tooling via Windows junctions — zero duplication, zero git traces
category: architecture
created: 2026-04-19
tags: [llm-toolkit, junctions, gitignore, multi-repo, windows, zero-duplication]
---

# Problem

Two repos (`llm-toolkit-project` + a consuming project) need to share LLM rules, skills, workflows, and rubrics. Committing LLM content to both repos causes duplication, stale copies, and security risk (auto-generated files like `copilot-instructions.md` may embed sensitive paths).

# Failed Approaches

1. **Committing LLM content to both repos** — files drift out of sync, history bloats, secrets can leak via auto-generated files.
2. **Using bare `workflows/` in `.gitignore`** — accidentally gitignores `docs/llm/workflows/` (committed project workflows), causing them to become untracked silently.
3. **Not ignoring agent-side skill junctions in the toolkit repo** — Git traverses junctions on Windows and duplicates all skill content into the index.

# Solution

Single source of truth in `llm-toolkit-project`. Consuming repos link via Windows junctions at setup time. Every junction path is gitignored — zero LLM traces in git history.

### `_setup-llm-local.cmd` skeleton
```cmd
set TOOLKIT=..\llm-toolkit-project
for %%D in (.agents .claude .codex .cursor .windsurf .setup rubrics skills workflows) do (
    if exist "%%D" rmdir "%%D" 2>nul
    mklink /J "%%D" "%TOOLKIT%\%%D"
)
if exist "docs\llm" rmdir "docs\llm" 2>nul
if not exist "docs" mkdir "docs"
mklink /J "docs\llm" "%TOOLKIT%\docs\llm"
```

### `.gitignore` in consuming repo — anchor ALL junction paths with `/`
```gitignore
/.windsurf/
/.cursor/
/.agents/
/.claude/
/.codex/
/.setup/
/rubrics/
/skills/
/workflows/
docs/llm/
.github/copilot-instructions.md
AGENTS.md
CLAUDE.md
.cursorignore
.cursorindexingignore
```

### `.gitignore` in `llm-toolkit-project` — block junction traversal
```gitignore
.agents/skills/
.claude/skills/
.codex/skills/
.cursor/skills/
.windsurf/workflows/
```

# Why

Windows Git traverses junctions as real directories. Without explicit gitignore rules, all junctioned content appears as tracked files in both repos. Anchoring patterns with `/` prevents rules like `workflows/` from matching `docs/llm/workflows/` at any depth.
