# Codex

`AGENTS.md` remains the primary repository instruction surface for Codex sessions.

This `.codex/` directory is an optional companion layout for teams that want a Codex-oriented mirror next to `.agents/`, `.claude/`, `.cursor/`, and `.windsurf/`.

## What belongs here

- `README.md` for Codex-specific notes.
- `skills/` as an optional mirror of portable skills from `.agents/skills/`.
- `agents/` as an optional mirror for Codex-oriented agent prompts.
- true Codex-only additions only when they cannot live in the tool-agnostic source tree.

## Quick start

Run:

```bash
./.codex/sync-shared-skills.sh
```

Optional:

```bash
./.codex/sync-shared-skills.sh --no-global
```

`--no-global` keeps the mirror local to this repository and skips `~/.codex/skills`.

If the filesystem does not support symlinks, the script automatically falls back to copy mode.
You can also force copy mode explicitly:

```bash
./.codex/sync-shared-skills.sh --copy --no-global
```
