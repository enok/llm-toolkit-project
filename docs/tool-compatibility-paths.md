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
| Claude Code | `CLAUDE.md`, `.claude/skills/`, `.claude/agents/` | `CLAUDE.md` imports `AGENTS.md` (`@AGENTS.md`); shared skills and agents are links |
| Gemini CLI | `.gemini/skills/` | Thin skill compatibility link to `.agents/skills/` |
| GitHub Copilot | `.github/copilot-instructions.md` | Concatenated repo-local export from the shared selection plus resolved LLM config docs - not a skills directory; the toolkit creates no Copilot skills link (see below) |
| OpenCode | `.opencode/skills/` | Thin skill compatibility link to `.agents/skills/` |
| Windsurf | `.windsurf/skills/`, `.windsurf/rules/`, `.windsurf/workflows/` | Thin skill link plus shared rule/workflow links |

`setup-repo.*` asks which tools a consumer repo uses and links the selected
project roots above. `ensure-symlinks.*` repairs the `.agents/`, `.agent/`,
`.claude/`, `.codex/`, `.cursor/`, `.gemini/`, `.opencode/`, and `.windsurf/`
links so new skills become visible after a clone; it does not create or
modify `.github/skills/` - the toolkit generates no Copilot skills link,
only the instructions file above. Vendor documentation read on 2026-11-24
says the Copilot agent also discovers project skills in `.github/skills/`,
`.claude/skills/`, and `.agents/skills/`, so the `.claude/skills/` and
`.agents/skills/` links above may already be visible to it. Which editor
versions honour each path is untested.

### Global (home-directory) skill paths

Most tools also support installing skills globally, outside any one repo.
`scripts/install-global-surfaces.sh` / `.ps1` (see `docs/global-install.md`)
materializes every path below as a link back to this toolkit's `skills/`,
links the agent path for Claude Code (`~/.claude/agents`), Codex
(`~/.codex/agents`), and Cursor (`~/.cursor/agents`) to `tool-subagents/`, and
writes a managed instruction block into the global instruction files of
Claude Code (`~/.claude/CLAUDE.md`), Codex (`~/.codex/AGENTS.md`), Windsurf
(`~/.codeium/windsurf/memories/global_rules.md`), and Gemini CLI
(`~/.gemini/GEMINI.md`). `.codex/sync-shared-skills.sh` is the older,
Codex-only mirror script and remains available.

| Tool | Global skill path |
|------|-------------------|
| Antigravity | `~/.gemini/antigravity/skills/` |
| Codex | `~/.codex/skills/` (per-skill links; also `.codex/sync-shared-skills.sh`) |
| Cursor | `~/.cursor/skills/` |
| Claude Code | `~/.claude/skills/` |
| Gemini CLI | `~/.gemini/skills/` |
| OpenCode | `~/.config/opencode/skills/` |
| Windsurf | `~/.codeium/windsurf/skills/` |

GitHub Copilot is not in this table because the installer does not target it
(it has no Copilot installer and creates no `~/.copilot/skills` link). Vendor
documentation read on 2026-11-24 says the Copilot command-line tool loads
personal skills from `~/.copilot/skills` and `~/.agents/skills`, and the
editor's agent mode loads them from `~/.copilot/skills`, `~/.claude/skills`,
and `~/.agents/skills`, so the `~/.claude/skills` link above may already
serve the editor agent. The command-line tool page does not list
`~/.claude/skills`. Observed once, on one machine (surface not recorded):
the toolkit skills were visible to the Copilot agent through the existing
Claude link with no installer step. Which editor versions honour each path
is untested.

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
