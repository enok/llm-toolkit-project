# Agents (portable skill catalog)

`.agents/skills/` is the provider-agnostic Agent Skills location: a thin compatibility surface next to `.claude/`, `.codex/`, `.cursor/`, and `.windsurf/`.

## What belongs here

- `README.md` for notes on this directory.
- `skills/<name>` as per-skill compatibility symlinks into the canonical `skills/<name>` catalog at the repo root.

**This directory should stay thin.** Do not hand-edit under `.agents/skills/`; edit `skills/<name>/SKILL.md` (and its `references/`, `rules/`, `scripts/`) instead.

## Regenerate

From the repo root (Git Bash, WSL, or macOS/Linux):

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md
```

On Windows PowerShell:

```powershell
./scripts/sync-tool-configs.ps1 . -SkipAgentsMd
```

`--skip-agents-md` preserves the curated root `AGENTS.md` while repairing `.agents/skills/` and the other provider links.
