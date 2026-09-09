# Windsurf layout (this toolkit repository)

This directory mirrors how other tools consume the same shared knowledge:

| Path | Role |
| --- | --- |
| `rules/` (repo root) | Canonical source for shared markdown rules |
| `workflows/` (repo root) | Canonical workflow steps |
| `skills/` (repo root) | Canonical on-demand skill catalog |
| `.windsurf/rules` | Symlink to the canonical shared rules |
| `.windsurf/workflows` | Symlink to the canonical shared workflows |
| `.windsurf/skills/<name>` | Per-skill compatibility symlinks into the canonical skill catalog |

**`.windsurf/` should stay thin.** Do not hand-edit through `.windsurf/`; edit `rules/`, `workflows/`, or `skills/` instead.

## Regenerate

From the repo root (Git Bash, WSL, or macOS/Linux):

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md
```

On Windows PowerShell:

```powershell
./scripts/sync-tool-configs.ps1 . -SkipAgentsMd
```

`--skip-agents-md` keeps the curated root `AGENTS.md` untouched while repairing the shared symlink surfaces and refreshing the other repo-local exports.
