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
| Antigravity | `.agent/skills/` | Skill root with the same catalog as `.agents/skills/` (see the layout note below) |
| Codex / generic | `AGENTS.md`, `.agents/skills/`, optional `.codex/agents/` | `AGENTS.md` is primary; `.agents/skills/` is the shared skill root (Codex also reads it) |
| Cursor | `.agents/skills/`, `.cursor/rules/`, `.cursor/agents/` | Skills come from the shared `.agents/skills/` root; agents are links to the canonical shared files; `.cursor/rules/*.mdc` is generated from `rules/` (git-ignored through a generated `.cursor/rules/.gitignore` that lists only the generated files; hand-made rules there stay visible to git): `always_on` becomes `alwaysApply: true`, `model_decision` becomes `alwaysApply: false` with its description, `glob` becomes `globs:`, `manual` sets neither |
| Claude Code | `CLAUDE.md`, `.claude/skills/`, `.claude/agents/` | `CLAUDE.md` imports `AGENTS.md` (`@AGENTS.md`); skills and agents come from the toolkit (see the layout note below) |
| Gemini CLI | `.gemini/skills/` | Skill root with the same catalog as `.agents/skills/` (see the layout note below) |
| GitHub Copilot | `.github/copilot-instructions.md` | Concatenated repo-local export from the shared selection plus resolved LLM config docs - not a skills directory; the toolkit creates no Copilot skills link (see below) |
| OpenCode | `.opencode/skills/` | Skill root with the same catalog as `.agents/skills/` (see the layout note below) |
| Windsurf | `.agents/skills/`, `.windsurf/rules/`, `.windsurf/workflows/` | Skills come from the shared `.agents/skills/` root; rule/workflow links are shared |

Layout, by where it runs. In a consumer repo (`setup-repo.*`,
`ensure-symlinks.*`) every skill root (`.agents/skills`, `.agent/skills`,
`.claude/skills`, `.gemini/skills`, `.opencode/skills`) is a real directory
holding one `<name>` link per skill into the toolkit's `skills/<name>`, so local
skills can sit beside them. In the toolkit root itself (`sync-tool-configs.*`)
the roots are single catalog links: `.agents/skills -> ../skills` and the
others `-> ../.agents/skills`.

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

Skill roots (C6): sync creates project skill links only under `.agents/skills`
(read by Codex, Cursor, Windsurf and Copilot) and `.claude/skills` (Claude
Code), plus the `.agent`, `.gemini` and `.opencode` roots not reviewed yet.
It no longer creates `.codex/skills`, `.cursor/skills` or `.windsurf/skills`.
Existing ones are never deleted; sync prints one line per old link it finds
saying it can be removed.

### Upgrade note (one-time step)

After updating the toolkit, run the sync or installer once so the Codex agents link is re-pointed to `tool-subagents/.generated/codex/`: an existing `.codex/agents` or `~/.codex/agents` link that still targets `tool-subagents/` shows no `.toml` (the committed copies are gone) until then. Project level: `./scripts/sync-tool-configs.sh . --skip-agents-md --skip-github` (in the toolkit) or `../llm-toolkit-project/scripts/setup-repo.sh .` / `ensure-symlinks.sh .` (in a consumer); Windows: `.\scripts\sync-tool-configs.ps1 . -SkipAgentsMd` or `..\llm-toolkit-project\scripts\setup-repo.ps1 .`. User level: `./scripts/install-global-surfaces.sh --apply` or `.\scripts\install-global-surfaces.ps1 -Apply`. The scripts and `npm run subagents:check` print a WARNING while the old link is still in place.

### Global (home-directory) skill paths

Most tools also support installing skills globally, outside any one repo.
`scripts/install-global-surfaces.sh` / `.ps1` (see `docs/global-install.md`)
materializes every path below as a link back to this toolkit's `skills/`
(Codex, Cursor and Windsurf share one `~/.agents/skills/<name>` link per skill;
the installer no longer creates `~/.codex/skills`, `~/.cursor/skills` or
`~/.codeium/windsurf/skills`, never deletes old ones, and prints one line per
old link it finds saying it can be removed),
links the agent path for Claude Code (`~/.claude/agents`), Codex
and Cursor (`~/.cursor/agents`) to `tool-subagents/` (Codex, `~/.codex/agents`, is linked to the generated `tool-subagents/.generated/codex/`), and
writes a managed instruction block into the global instruction files of
Claude Code (`~/.claude/CLAUDE.md`), Codex (`~/.codex/AGENTS.md`), Windsurf
(`~/.codeium/windsurf/memories/global_rules.md`), and Gemini CLI
(`~/.gemini/GEMINI.md`). `.codex/sync-shared-skills.sh` is not part of the
global install: it only repairs the toolkit root's `.agents/skills` and
`.claude/skills` catalog links and writes nothing under the home directory.

| Tool | Global skill path |
|------|-------------------|
| Antigravity | `~/.gemini/antigravity/skills/` |
| Codex | `~/.agents/skills/` (per-skill links) |
| Cursor | `~/.agents/skills/` |
| Claude Code | `~/.claude/skills/` (per-skill links inside a real directory) |
| Gemini CLI | `~/.gemini/skills/` |
| OpenCode | `~/.config/opencode/skills/` |
| Windsurf | `~/.agents/skills/` |

Gemini CLI, OpenCode and Antigravity still use one directory link to the whole
`skills/` folder (not yet changed to per-skill links). `~/.claude/skills` and
`~/.agents/skills` are real directories, so a file another tool writes there
lands in the home directory and not in the toolkit checkout; an old directory
link at `~/.claude/skills` is replaced by the installer (only the link is
removed), and an existing real directory keeps its contents.

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
| `.cursor/rules/*.mdc` | Cursor rules (generated by the sync, not links; generated files carry the `generated-by: sync-tool-configs` marker and are listed in a generated `.cursor/rules/.gitignore`; files without the marker are hand-made and never deleted or ignored) | `rules/` |
| `.cursor/workflows/` | No longer created (not a Cursor surface); an existing link keeps working and can be removed | `workflows/` |
| `.cursor/agents/` | Cursor specialist agents | `tool-subagents/` |
| `.claude/agents/` | Claude Code specialist agents | `tool-subagents/` |
| `.codex/agents/` | Optional Codex specialist agents | `tool-subagents/.generated/codex/` (TOML rendered from `tool-subagents/*.md`; gitignored). A consumer's own hand-written agent TOML lives in its `tool-subagents/` and is linked as before (`.codex/agents -> ../tool-subagents`) |

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

`--skip-agents-md` preserves the curated root `AGENTS.md` while repairing the
provider links and refreshing the other repo-local exports. On a fresh clone
where links are missing, run the same command from the toolkit root (add
`--skip-github` / `-SkipGithub` to leave `.github/` alone), or for a consumer
repo run `../llm-toolkit/scripts/setup-repo.cmd .`. `.agent`, `.agents`,
`.claude`, `.cursor` and `.windsurf` surfaces are links or real directories of
links, as described under the layout note above (junctions on Windows);
`.cursor/rules/*.mdc` is generated and gitignored. If the
filesystem has no symlinks the toolkit has no copy mode; use a checkout on a
filesystem that supports links. Check the links with
`ls -la .windsurf/rules .windsurf/workflows .cursor/rules`
(each should show `->`, except the generated `.cursor/rules` files) and, in the
toolkit root, `ls -la .agents/skills .claude/skills` (each shows `->`); in a
consumer repo `ls -la .agents/skills/` shows one `->` link per skill.

## Provider Notes

Each provider folder (`.agents`, `.claude`, `.codex`, `.cursor`, `.windsurf`)
holds a one-line `README.md` pointing here. Keep these folders thin: do not
hand-edit anything reached through them; edit `skills/`, `rules/`,
`workflows/` or `tool-subagents/` and regenerate.

- `.agents/skills/`: the provider-agnostic skill root (one per-skill link into
  `skills/<name>` in a consumer repo; a catalog link to `skills/` in the toolkit
  root). Edit `skills/<name>/SKILL.md` (and its `references/`,
  `rules/`, `scripts/`), never the link.
- `.claude/agents`: link to `tool-subagents/`; add or edit files there, not
  through `.claude/agents`.
- `.codex/`: `AGENTS.md` stays the primary Codex instruction surface.
  `.codex/agents/` links to the generated `tool-subagents/.generated/codex/`
  (not committed, gitignored except the README; do not hand-edit). Re-render
  the TOML with `npm run subagents:render`; `npm run subagents:apply -- all .`
  also refreshes the `.cursor/agents/` and `.claude/agents/` renders (sync,
  setup and global-install run the render before linking). Codex-only
  additions belong in `.codex/` only when they cannot live in the
  tool-agnostic source tree. `.codex/sync-shared-skills.sh` repairs only the
  toolkit root's `.agents/skills` and `.claude/skills` catalog links (it no
  longer creates `.codex/skills` or `.windsurf/skills` or mirrors into
  `~/.codex/skills`; `--no-global` is accepted and ignored). Neither it nor the
  installer deletes old links; an existing `~/.codex/skills` can be removed
  (Codex reads `~/.agents/skills`). It refuses to replace non-symlink provider
  directories.
- `.cursor/`: rule conversion is described in the skill-paths table above;
  `manual` emits no `description` (Cursor would treat it as agent-requested)
  and `globs` is written unquoted. Generated files carry the marker
  `generated-by: sync-tool-configs`; the sync writes `.cursor/rules/.gitignore`
  listing exactly those files, so hand-made rules there stay visible to git and
  are never touched or deleted (in this repo the root `.gitignore` covers the
  whole directory). An older `.cursor/rules` directory link is replaced only
  with `--force`, and only when it points at the toolkit `rules/` (any other
  link is left alone); stale generated `.mdc` files are removed on the next sync. `.cursor/workflows` is
  not a Cursor surface and is no longer created. Cursor skills load from
  `.agents/skills/` (see `skills/README.md` for the catalog). The catalog of
  shared subagents is `tool-subagents/README.md`; `.cursor/agents/` links to
  the same files. Invoke a subagent with `/name` or natural language.
- `.windsurf/`: `rules` and `workflows` are links to `rules/` and
  `workflows/`; Windsurf reads skills from `.agents/skills/`.
  `.windsurf/skills/<name>` links are legacy and can be removed.

### Cursor Max Throughput (Multiple Agents)

1. Turn on Max Mode (or the plan's highest-quality agent setting) so the root
   agent runs at full capability and per-task tier requests can be honored;
   subagents still follow their assigned complexity tier
   (`light`/`standard`/`deep`), not automatic full depth.
2. In one message, ask for parallel work (for example "run CI triage,
   contract analysis, and doc drift in parallel") so the agent issues
   several subagent tasks at once.
3. Use `model: fast` subagents for log parsing, repo mapping and wide search;
   use `model: inherit` for security, release planning and deep review (see
   [Subagents](https://cursor.com/docs/subagents)).
4. Use `is_background: true` on long read-only slices so the parent keeps
   driving the critical path.
5. Team-wide defaults also live in `rules/multi-agent-orchestration.md`.
6. `rules/request-orchestration.md` makes `agent-orchestrator` the default
   router for non-trivial requests, so users do not need to ask for agents
   explicitly; it assigns each delegated task a complexity tier and shows a
   wave-ordered task table before fanout.

## Client Overlays And Sync Commands

Client overlays are generated or linked surfaces that let IDEs and LLM tools
consume the canonical toolkit content without duplicating source files.
Provider-facing overlays are `.codex/`, `.cursor/`, `.claude/`, `.windsurf/`,
`.agents/`, `.agent/`, `.gemini/`, `.opencode/`, and generated files such as
`.github/copilot-instructions.md`.

- Refresh generated tool configs with `npm run tool-configs:sync`: the npm
  wrapper for the same `scripts/sync-tool-configs.sh` /
  `scripts/sync-tool-configs.ps1` documented at the repository root; both
  repair the same overlays.
- Apply shared subagents to one provider overlay with
  `npm run subagents:apply -- codex .` (other names: `cursor`, `claude`,
  `all`). When a new specialist must be available across every local
  provider surface, run `npm run subagents:apply -- all .` after the canonical
  prompt files are complete; use a provider-specific apply only when the task
  targets a single client.
- Adding a specialist agent: update canonical assets first, then sync:
  1. `tool-subagents/<agent>.md` (Codex TOML is generated from the `.md`)
  2. `workflows/<agent>-validation.md`
  3. `workflows/<agent>-evolution.md`
  4. `skills/<agent>/SKILL.md`
  5. `INTENTS.md`, `AGENTS.md`, `README.md`, and `docs/catalog/workflows.md`
  6. `npm run tool-configs:sync`, then `npm run subagents:apply -- codex .`
- Documentation created or changed by provider sync, agent output, chat
  output, or generated client files must pass `documentation-reviewer`
  before final reporting.
- Commit generated client files only when the repository should work out of
  the box for those clients.
- For a new workstation or LLM client, use [`../clients/infra.md`](../clients/infra.md)
  and the repository-root `INFRA.sh` / `INFRA.ps1` plan-first bootstrap.
