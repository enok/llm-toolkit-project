# Cursor layout (this toolkit repository)

This directory mirrors how other tools consume the same knowledge:

| Path | Role |
| --- | --- |
| `rules/` (repo root) | Canonical source for shared markdown rules |
| `workflows/` (repo root) | Canonical workflow steps |
| `tool-subagents/` (repo root) | Canonical source for shared project subagent prompts |
| `.cursor/rules` | Symlink to the canonical shared rules |
| `.cursor/workflows` | Symlink to the canonical shared workflows |
| `.cursor/agents` | Symlink to `../tool-subagents` |
| `.cursor/skills` | Symlink to `../.agents/skills` (catalog; consumer repos use per-skill links instead) |

**`.cursor` should stay thin.** The tool-facing folders are symlinks to the canonical sources. Do not hand-edit through `.cursor/`; edit `skills/`, `rules/`, `workflows/`, or `tool-subagents/` instead.

**Cursor Agent Skills** load from `.cursor/skills/` (and `.agents/skills/`); see root `AGENTS.md` for the skill index.

## Repair `.cursor/` and `.claude/agents`

From the repo root (Git Bash, WSL, or macOS/Linux):

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md
```

`--skip-agents-md` keeps the curated root `AGENTS.md` untouched while still repairing the shared symlink surfaces and refreshing the other repo-local exports.

## Max throughput (multiple agents)

1. Turn on **Max Mode** (or your plan’s highest-quality agent setting) in Cursor so the root agent runs at full capability and per-task tier requests can actually be honored — subagents still follow their assigned complexity tier (`light`/`standard`/`deep`), not automatic full depth.
2. In one message, ask for **parallel** work (e.g. “run CI triage, contract analysis, and doc drift in parallel”) so the agent issues multiple subagent tasks at once.
3. Use **`model: fast`** subagents for log parsing, repo mapping, and wide search; use **`model: inherit`** for security, release planning, and deep review (see [Subagents](https://cursor.com/docs/subagents)).
4. Use **`is_background: true`** on long read-only slices so the parent keeps driving the critical path.
5. Team-wide defaults also live in `rules/multi-agent-orchestration.md`.
6. `rules/request-orchestration.md` makes `agent-orchestrator` the default router for non-trivial requests, so users do not need to ask for agents explicitly; it assigns each delegated task a complexity tier (`light`/`standard`/`deep`) and shows a wave-ordered task table before fanout.

### Subagents in this repo

The maintained catalog of all shared subagents (roles, contracts, quality-loop
validators) lives in `tool-subagents/README.md`; `.cursor/agents/` is a link to
the same canonical files, so the catalog is never duplicated here.

Invoke with `/name` or natural language (“use the ci-triage subagent”).

## Claude / Codex compatibility

`setup-repo.sh` / `ensure-symlinks.sh` link the same canonical sources into `.claude/agents/` (and you may add `.codex/agents/` the same way). See `.codex/README.md` for optional Codex skill layout.
