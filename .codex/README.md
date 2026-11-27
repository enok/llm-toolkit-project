# Codex

`AGENTS.md` remains the primary repository instruction surface for Codex sessions.

This `.codex/` directory is a thin Codex compatibility surface next to `.agents/`, `.claude/`, `.cursor/`, and `.windsurf/`.

## What belongs here

- `README.md` for Codex-specific notes.
- `skills/` as a compatibility symlink to the shared skill catalog.
- `agents/` as a link to `tool-subagents/.generated/codex/`, the Codex TOML rendered from the shared `tool-subagents/*.md` catalog (`npm run subagents:render`). Not committed (gitignored except this README); regenerate locally, do not hand-edit.
- Codex-only additions only when they cannot live in the tool-agnostic source tree.

## Quick start

Materialize or repair the `skills/` symlink and other provider links with:

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md
```

On Windows PowerShell:

```powershell
./scripts/sync-tool-configs.ps1 . -SkipAgentsMd
```

`--skip-agents-md` preserves the curated root `AGENTS.md` while repairing provider links.

Re-render the generated Codex TOML separately with:

```bash
npm run subagents:render
```

(`npm run subagents:apply -- all .` also refreshes `.cursor/agents/` and `.claude/agents/` renders; sync, setup, and global-install run the render before linking.)

`sync-shared-skills.sh` remains available for the additional workflow of mirroring the shared skill catalog into a global `~/.codex/skills/` for system-wide Codex sessions. It refuses to replace non-symlink provider directories:

```bash
./.codex/sync-shared-skills.sh             # local repair + global mirror
./.codex/sync-shared-skills.sh --no-global # local repair only
```
