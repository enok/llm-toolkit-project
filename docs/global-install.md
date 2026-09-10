# Global Install

Installs this toolkit's skills, agents, rules, and workflows as the
**global (home-directory)** surface for every LLM tool on this machine,
so any session in any project uses the shared toolkit by default -- not
just repos that link or clone it. It also writes a managed instruction
block into each tool's global instruction file that tells the tool to
read `AGENTS.md`, route every non-trivial prompt through
`rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md`,
and route by `INTENTS.md`.

The installer scripts are `scripts/install-global-surfaces.sh` (bash --
Linux/macOS/Git Bash) and `scripts/install-global-surfaces.ps1`
(PowerShell 5.1+/7 -- Windows, and cross-platform pwsh). Canonical content
never leaves this repository; the scripts only create links back to it
and write a clearly delimited managed block, never touching the rest of
a target file.

## Quick start

Default mode is a **plan** (dry-run): it prints what would change and
touches nothing on disk.

```bash
./scripts/install-global-surfaces.sh
```

```powershell
.\scripts\install-global-surfaces.ps1
```

Once the plan looks right, apply it:

```bash
./scripts/install-global-surfaces.sh --apply
```

```powershell
.\scripts\install-global-surfaces.ps1 -Apply
```

Both scripts print a summary table (`tool | surface | action`) where
`action` is one of `created`, `updated`, `unchanged`, `blocked`, or
`skipped`. Running apply again after a clean run reports everything
`unchanged` -- the scripts are idempotent.

## Options

| bash | PowerShell | Meaning |
| --- | --- | --- |
| `--apply` | `-Apply` | Make the changes. Omit for a dry-run plan. |
| `--tools <list>` | `-Tools <list>` | Comma-separated: `claude,codex,cursor,windsurf,gemini,opencode,antigravity`, or `all`. Default `auto`: only tools whose home directory already exists (see detection paths below). |
| `--force` | `-Force` | Replace a blocking non-link path (a real file or directory already at the link location) after backing it up to `<path>.bak-<yyyyMMddHHmmss>`. Without it, a blocking path is reported `blocked` and left untouched. |
| `--toolkit-root <path>` | `-ToolkitRoot <path>` | Toolkit repository root. Default: the repo root containing the script. |
| `--home <path>` | `-Home <path>` (alias for `-HomeDir`) | Home directory to install into. Default: the current user's home directory. Mainly for testing against a scratch directory. |

`auto` detection checks: `~/.claude`, `~/.codex`, `~/.cursor`,
`~/.codeium/windsurf`, `~/.gemini`, `~/.config/opencode`, and
`~/.gemini/antigravity`. A tool with no home directory yet is skipped
under `auto` -- pass `--tools all` (or name it explicitly) to install for
a tool before you've ever run it.

**Exit status:** non-zero only when `-Apply`/`--apply` hits at least one
`blocked` path. A plan run always exits `0`, so it is safe to run for
inspection at any time (for example in a script or CI step).

## What gets installed, per tool

| Tool | Skills | Agents | Global instruction file |
| --- | --- | --- | --- |
| Claude Code | `~/.claude/skills` -> `skills/` | `~/.claude/agents` -> `tool-subagents/` | `~/.claude/CLAUDE.md` (managed block) |
| Codex | `~/.codex/skills/<name>` -- one link per skill directory | `~/.codex/agents` -> `tool-subagents/` | `~/.codex/AGENTS.md` (managed block; created if missing or empty) |
| Cursor | `~/.cursor/skills` -> `skills/` | `~/.cursor/agents` -> `tool-subagents/` | None -- Cursor has no global rules file. The script prints the directive text to paste into **Cursor Settings > Rules > User Rules**. |
| Windsurf | `~/.codeium/windsurf/skills` -> `skills/` | -- | `~/.codeium/windsurf/memories/global_rules.md` (managed block; directories created if missing) |
| Gemini CLI | `~/.gemini/skills` -> `skills/` | -- | `~/.gemini/GEMINI.md` (managed block) |
| OpenCode | `~/.config/opencode/skills` -> `skills/` | -- | -- |
| Antigravity | `~/.gemini/antigravity/skills` -> `skills/` | -- | -- |

Codex enumerates skill directories directly rather than following a
nested link, so it gets one link per skill (`~/.codex/skills/<name>` ->
`skills/<name>`) instead of a single `skills/` link. An existing real
(non-symlink) directory with the same name as a toolkit skill is
preserved unless `--force`/`-Force` is given, and entries under
`~/.codex/skills/` that don't match a toolkit skill are never touched or
removed.

On Windows, a link is a directory junction (`New-Item -ItemType
Junction`) -- no admin rights or Developer Mode required. On non-Windows
PowerShell and in the bash script, it's a directory symbolic link
(`New-Item -ItemType SymbolicLink` / `ln -sfn`).

The managed instruction block is delimited by
`<!-- BEGIN LLM-TOOLKIT GLOBAL -->` and `<!-- END LLM-TOOLKIT GLOBAL -->`
markers. Its content is rendered from
`scripts/templates/global-agent-directive.md`
(`{{TOOLKIT_ROOT}}` substituted with this repo's absolute path). A
re-run replaces only the text between the markers -- any of your own
notes above or below the block are left exactly as they were.

## Refreshing after `git pull`

The links point at paths inside this repository, not at specific file
contents, so pulling toolkit updates (new skills, an updated
`tool-subagents/agent-orchestrator.md`, and so on) is visible to every
tool immediately -- no re-run needed for the linked skills/agents
directories.

Re-run with `--apply`/`-Apply` when:

- A new tool's home directory now exists and you want it picked up
  (`auto` mode only re-scans on each run).
- A Codex skill was added or removed, since Codex needs one link per
  skill directory refreshed.
- `scripts/templates/global-agent-directive.md` changed and you want the
  managed block in each global instruction file to reflect it.

Both cases are idempotent: re-running is always safe, and anything
already correct reports `unchanged`.

## Uninstalling

There is no built-in uninstall subcommand; remove the links and the
managed block manually. Only remove a link if it's a symlink/junction --
never `rm -rf` in case a real directory landed at that path.

**Links** (bash):

```bash
rm -f ~/.claude/skills ~/.claude/agents \
      ~/.codex/agents ~/.cursor/skills ~/.cursor/agents \
      ~/.codeium/windsurf/skills ~/.gemini/skills \
      ~/.config/opencode/skills ~/.gemini/antigravity/skills
find ~/.codex/skills -maxdepth 1 -type l -delete   # per-skill Codex links
```

**Links** (PowerShell): a junction/symlink is safe to remove with
`Remove-Item` as long as you don't add `-Recurse` (which would otherwise
recurse into -- and delete -- the link's target on older PowerShell
versions):

```powershell
Remove-Item ~/.claude/skills, ~/.claude/agents, ~/.codex/agents, `
    ~/.cursor/skills, ~/.cursor/agents, ~/.codeium/windsurf/skills, `
    ~/.gemini/skills, ~/.config/opencode/skills, `
    ~/.gemini/antigravity/skills -Force
Get-ChildItem ~/.codex/skills | Where-Object LinkType | Remove-Item -Force
```

**Managed instruction blocks** -- strip the block from each file the
installer touched (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`,
`~/.codeium/windsurf/memories/global_rules.md`, `~/.gemini/GEMINI.md`);
this preserves any other content in the file:

```bash
for f in ~/.claude/CLAUDE.md ~/.codex/AGENTS.md \
         ~/.codeium/windsurf/memories/global_rules.md ~/.gemini/GEMINI.md; do
  [ -f "$f" ] || continue
  awk '/<!-- BEGIN LLM-TOOLKIT GLOBAL -->/{skip=1} /<!-- END LLM-TOOLKIT GLOBAL -->/{skip=0; next} !skip' \
    "$f" > "$f.tmp" && mv "$f.tmp" "$f"
done
```

Cursor has no file to clean up -- remove the pasted text from **Cursor
Settings > Rules > User Rules** by hand.

## Cursor's manual step

Cursor has no global rules file, so it can't get a managed block the way
the other tools do. Whenever Cursor is in the selected `--tools`/`-Tools`
list, the script prints the rendered directive text after the summary
table -- copy it into **Cursor Settings > Rules > User Rules**. Re-run
the script (in either mode) any time you want the current text to copy
again, for example after `scripts/templates/global-agent-directive.md`
changes.

## Cowork / Claude.ai note

Cowork and Claude.ai sessions run in their own environment and only see
this repository's files when a folder containing it is linked to the
session, or the repo itself is cloned/checked out into it -- there is no
home directory on this machine for them to read a global instruction
file from. For those surfaces, the standing "route through the
orchestrator" directive instead lives in the user's Claude memory
(a saved preference) and in the relevant Claude Projects' project docs,
so it travels with the user across chats rather than with a machine.

## Optional: provider-rendered agent copies

The installer links `~/.claude/agents` and `~/.cursor/agents` straight to
`tool-subagents/`, so updates are live. If you prefer provider-rendered copies
instead (light-tier agents get `model: haiku` for Claude Code and `model: fast`
for Cursor, and the `tier:`/`readonly:` keys are stripped), remove the link and
render explicitly; re-run after every toolkit update:

```bash
node scripts/create-specialist-agent.js --apply-subagents claude --target ~/.claude/agents
node scripts/create-specialist-agent.js --apply-subagents cursor --target ~/.cursor/agents
```

