# Client Overlays

Client overlays are generated or linked surfaces that let IDEs and LLM tools
consume the canonical toolkit content without duplicating source files.

Canonical sources stay in:

- `rules/`
- `workflows/`
- `skills/`
- `tool-subagents/`

Provider-facing overlays include `.codex/`, `.cursor/`, `.claude/`,
`.windsurf/`, `.agents/`, `.agent/`, `.gemini/`, `.opencode/`, and generated
files such as `.github/copilot-instructions.md`. The full path map for each
provider lives in `docs/tool-compatibility-paths.md`.

## Sync Commands

Refresh generated tool configs:

```bash
npm run tool-configs:sync
```

This is the npm wrapper for the same `scripts/sync-tool-configs.sh` /
`scripts/sync-tool-configs.ps1` documented at the repository root - use
whichever form is convenient; both repair the same overlays.

Apply shared subagents to a provider overlay:

```bash
npm run subagents:apply -- codex .
```

Other provider names supported by the local helper are `cursor`, `claude`,
and `all`.

When a new specialist must be available across every local provider
surface, run `npm run subagents:apply -- all .` after the canonical prompt
files are complete. Use provider-specific apply only when the task
intentionally targets a single client.

## Specialist Agent Updates

When adding a specialist agent, update canonical assets first, then sync
provider overlays:

1. `tool-subagents/<agent>.md`
2. `tool-subagents/<agent>.toml`
3. `workflows/<agent>-validation.md`
4. `workflows/<agent>-evolution.md`
5. `skills/<agent>/SKILL.md`
6. `INTENTS.md`, `AGENTS.md`, `README.md`, and `workflows/README.md`
7. `npm run tool-configs:sync`
8. `npm run subagents:apply -- codex .`

Documentation created or changed by provider sync, agent output, chat
output, or generated client files must pass `documentation-reviewer` before
final reporting.

Commit generated client files only when the repository should work out of
the box for those clients.

For a new workstation or LLM client, use [`infra.md`](infra.md) and the
repository-root `INFRA.sh` / `INFRA.ps1` plan-first bootstrap.
