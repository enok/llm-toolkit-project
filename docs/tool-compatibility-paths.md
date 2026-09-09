# LLM Tool Compatibility Paths

The toolkit source of truth stays in this repository:

| Asset type | Canonical source |
|------------|------------------|
| Skills | `skills/` |
| Rules | `rules/` |
| Workflows | `workflows/` |
| Tool subagents | `tool-subagents/` |
| Repo-local customization | consumer `docs/llm/`, `AGENTS.md`, and committed project docs |

Provider folders are compatibility surfaces only. In a consumer repo they
are symlinks (junctions on Windows) or generated exports that point back to
the canonical sources above. Do not copy shared skill, rule, workflow, or
subagent content into provider folders - edit the canonical source and
regenerate the surface instead.

## Skill Paths

Based in part on the multi-tool path map from
[VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills#skills-paths-for-other-ai-coding-assistants),
verified against this toolkit's own `setup-repo.*`, `ensure-symlinks.*`, and
`sync-tool-configs.*` scripts:

| Tool | Project location | Format |
|------|------------------|--------|
| Antigravity | `.agent/skills/` | Thin skill compatibility link to `.agents/skills/` |
| Codex / generic | `AGENTS.md`, `.agents/skills/`, optional `.codex/skills/`, optional `.codex/agents/` | `AGENTS.md` is primary; provider skill paths stay thin links to the shared skill catalog |
| Cursor | `.cursor/skills/`, `.cursor/rules/`, `.cursor/workflows/`, `.cursor/agents/` | Symlinked compatibility surfaces that point to the canonical shared files |
| Claude Code | `CLAUDE.md`, `.claude/skills/`, `.claude/agents/` | `CLAUDE.md` is a thin pointer to `AGENTS.md`; shared skills and agents are links |
| Gemini CLI | `.gemini/skills/` | Thin skill compatibility link to `.agents/skills/` |
| GitHub Copilot | `.github/copilot-instructions.md` | Concatenated repo-local export from the shared selection plus resolved LLM config docs - not a skills directory |
| OpenCode | `.opencode/skills/` | Thin skill compatibility link to `.agents/skills/` |
| Windsurf | `.windsurf/skills/`, `.windsurf/rules/`, `.windsurf/workflows/` | Thin skill link plus shared rule/workflow links |

`setup-repo.*` asks which tools a consumer repo uses and links the selected
project roots above. `ensure-symlinks.*` repairs the `.agents/`, `.agent/`,
`.claude/`, `.codex/`, `.cursor/`, `.gemini/`, `.opencode/`, and `.windsurf/`
links so new skills become visible after a clone; it does not create or
modify `.github/skills/` - GitHub Copilot has no supported per-skill
directory in this toolkit, only the generated instructions file above.

### Global (home-directory) skill paths

A few tools also support installing skills globally, outside any one repo.
This toolkit only materializes one such path itself - for Codex, via
`.codex/sync-shared-skills.sh`, which mirrors the shared skill catalog into
`~/.codex/skills/` for system-wide Codex sessions. The others are the
tool's own native global path, not something this toolkit's scripts create:

| Tool | Global skill path |
|------|-------------------|
| Antigravity | `~/.gemini/antigravity/skills/` |
| Codex | `~/.codex/skills/` (via `.codex/sync-shared-skills.sh`) |
| Cursor | `~/.cursor/skills/` |
| Claude Code | `~/.claude/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| OpenCode | `~/.config/opencode/skills/` |
| Windsurf | `~/.codeium/windsurf/skills/` |

GitHub Copilot has no analogous global skill path; it only reads
`.github/copilot-instructions.md` per repo.

## Rules, Workflows, And Agents

| Provider surface | Purpose | Source |
|------------------|---------|--------|
| `.windsurf/rules/` | Windsurf rule compatibility | `rules/` |
| `.windsurf/workflows/` | Windsurf workflow compatibility | `workflows/` |
| `.cursor/rules/` | Cursor rule compatibility | `rules/` |
| `.cursor/workflows/` | Cursor workflow compatibility | `workflows/` |
| `.cursor/agents/` | Cursor specialist agents | `tool-subagents/` |
| `.claude/agents/` | Claude Code specialist agents | `tool-subagents/` |
| `.codex/agents/` | Optional Codex specialist agents | `tool-subagents/` |

Generated exports such as `CLAUDE.md`, the Copilot instructions file, and
the managed `AGENTS.md` sync block should stay thin summaries or pointers.
Put reusable knowledge in the canonical source directories instead.

Regenerate every compatibility surface after changing `rules/`,
`workflows/`, `skills/`, or `tool-subagents/`:

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md
```

```powershell
.\scripts\sync-tool-configs.ps1 . -SkipAgentsMd
```
