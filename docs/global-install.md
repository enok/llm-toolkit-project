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
| Claude Code | `~/.claude/skills/<name>` -- one link per skill directory inside a real `~/.claude/skills` directory | `~/.claude/agents` -> `tool-subagents/` | `~/.claude/CLAUDE.md` (managed block) |
| Codex | `~/.agents/skills/<name>` -- one link per skill directory (shared with Cursor and Windsurf) | `~/.codex/agents` -> `tool-subagents/.generated/codex/` (rendered from the `.md` by the installer; a legacy link to `tool-subagents/` is re-pointed) | `~/.codex/AGENTS.md` (managed block; created if missing or empty) |
| Cursor | `~/.agents/skills/<name>` (shared; no `~/.cursor/skills` link) | `~/.cursor/agents` -> `tool-subagents/` | None -- Cursor has no global rules file. The script prints the directive text to paste into **Cursor Settings > Rules > User Rules**. |
| Windsurf | `~/.agents/skills/<name>` (shared; no `~/.codeium/windsurf/skills` link) | -- | `~/.codeium/windsurf/memories/global_rules.md` (managed block; directories created if missing) |
| Gemini CLI | `~/.gemini/skills` -> `skills/` | -- | `~/.gemini/GEMINI.md` (managed block) |
| OpenCode | `~/.config/opencode/skills` -> `skills/` | -- | -- |
| Antigravity | `~/.gemini/antigravity/skills` -> `skills/` | -- | -- |

Codex, Cursor and Windsurf share one user-level root, `~/.agents/skills`.
It gets one link per skill (`~/.agents/skills/<name>` -> `skills/<name>`)
instead of a single `skills/` link, because Codex enumerates skill
directories directly rather than following a nested link. The installer no
longer creates `~/.codex/skills`, `~/.cursor/skills` or
`~/.codeium/windsurf/skills`; it never deletes them, and prints one
`legacy skills` row per old one it finds saying it can be removed. An existing real
(non-symlink) directory with the same name as a toolkit skill is
preserved unless `--force`/`-Force` is given, and entries under
`~/.agents/skills/` that are not links into the toolkit's `skills/` are never
touched or removed; a link into the toolkit's `skills/` whose skill no longer
exists is removed.

`~/.claude/skills` works the same way (one link per skill in a real
directory), so a tool or skill that writes into `~/.claude/skills` writes into
your home directory and not into the toolkit checkout. An older install left
`~/.claude/skills` as one directory link to `skills/`: the installer replaces
that link with a real directory plus per-skill links (only the link is
removed; the toolkit's `skills/` is untouched). An existing real
`~/.claude/skills` directory keeps all its contents and only gains the links.
Gemini CLI, OpenCode and Antigravity still use one directory link to
`skills/`.

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

## Knowledge base (recommended)

After the surfaces are installed, set up the local knowledge base so agents
can query the toolkit instead of re-reading it. It needs Docker with
compose, Python 3 and git. Details, configuration and troubleshooting are
in `docs/knowledge-base.md`.

```bash
./scripts/kb.sh init
./scripts/kb.sh up --build
./scripts/kb.sh index
./scripts/kb.sh schedule install
```

```powershell
.\scripts\kb.ps1 init
.\scripts\kb.ps1 up --build
.\scripts\kb.ps1 index
.\scripts\kb.ps1 schedule install
```

Pass `--data-dir <data-folder>` to `init` to keep the index outside the
default `~/.llm-toolkit/kb-data`. Run these once per machine. To remove it
later, run `schedule remove`, `hook remove` and `down` (see
`docs/knowledge-base.md`).

If a CLI session does not see the app-level global instructions, copy the
directive into the user-level instruction file.

## Refreshing after `git pull`

The links point at paths inside this repository, not at specific file
contents, so pulling toolkit updates (new skills, an updated
`tool-subagents/agent-orchestrator.md`, and so on) is visible to every
tool immediately for the linked agents directories and for edits to an
existing skill. A skill added or removed in the toolkit is NOT visible to
Claude Code, Codex, Cursor or Windsurf until the installer runs again,
because `~/.claude/skills` and `~/.agents/skills` hold one link per skill:
run `scripts/install-global-surfaces.sh --apply` (PowerShell:
`scripts/install-global-surfaces.ps1 -Apply`).

Re-run with `--apply`/`-Apply` when:

- A new tool's home directory now exists and you want it picked up
  (`auto` mode only re-scans on each run).
- A skill was added or removed in the toolkit (the user-level roots
  `~/.claude/skills` and `~/.agents/skills` need one link per skill).
- `scripts/templates/global-agent-directive.md` changed and you want the
  managed block in each global instruction file to reflect it.

Both cases are idempotent: re-running is always safe, and anything
already correct reports `unchanged`.

To make this automatic, set `LLM_KB_REFRESH_SURFACES=1` in the knowledge
base configuration (`docs/knowledge-base.md`): the scheduled index refresh
then re-runs this installer in apply mode, never forced, whenever the
checkout's HEAD changed. `python3 scripts/kb.py surfaces refresh` does the
same on demand; blocked paths are reported and left alone.

## Uninstalling

There is no built-in uninstall subcommand; remove the links and the
managed block manually. Only remove a link if it's a symlink/junction --
never `rm -rf` in case a real directory landed at that path.

Skill roots such as `~/.agents/skills` and `~/.claude/skills` are shared with
other tools, so delete only the links that point into this toolkit's
`skills/` folder, never every link in the root. In both blocks replace
`<toolkit-root>` with the absolute path of this checkout.

**Links** (bash):

```bash
TK=<toolkit-root>
for p in ~/.claude/agents ~/.codex/agents ~/.cursor/agents; do
  find "$p" -maxdepth 0 -type l -lname "$TK/*" -delete 2>/dev/null
done
for d in ~/.claude/skills ~/.agents/skills ~/.codex/skills ~/.cursor/skills \
         ~/.codeium/windsurf/skills ~/.gemini/skills ~/.config/opencode/skills \
         ~/.gemini/antigravity/skills; do
  # older install: the root itself is one directory link into the toolkit
  find "$d" -maxdepth 0 -type l -lname "$TK/*" -delete 2>/dev/null
  # per-skill links into the toolkit (the root and other tools' entries stay)
  find "$d" -mindepth 1 -maxdepth 1 -type l -lname "$TK/skills/*" -delete 2>/dev/null
done
```

**Links** (PowerShell): a junction/symlink is safe to remove with
`[IO.Directory]::Delete($path, $false)` (never `Remove-Item -Recurse`, which
on older PowerShell versions recurses into -- and deletes -- the link's
target). The helper removes a path only when it is a link whose target is
inside the toolkit (the trailing separator keeps a sibling folder such as
`<toolkit-root>-other` from matching):

```powershell
$toolkit = '<toolkit-root>'.TrimEnd('\', '/') + [IO.Path]::DirectorySeparatorChar
function Remove-ToolkitLink([string]$Path) {
    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if ($item -and $item.LinkType) {
        $target = [string]($item.Target | Select-Object -First 1)
        $target = $target.Replace('/', [IO.Path]::DirectorySeparatorChar)
        if ($target.StartsWith($toolkit, [System.StringComparison]::OrdinalIgnoreCase)) {
            if ($item.PSIsContainer) { [IO.Directory]::Delete($Path, $false) }
            else { Remove-Item -LiteralPath $Path -Force }
        }
    }
}
foreach ($rel in '.claude\agents', '.codex\agents', '.cursor\agents') {
    Remove-ToolkitLink (Join-Path $HOME $rel)
}
foreach ($rel in '.claude\skills', '.agents\skills', '.codex\skills', '.cursor\skills',
                 '.codeium\windsurf\skills', '.gemini\skills', '.config\opencode\skills',
                 '.gemini\antigravity\skills') {
    $root = Join-Path $HOME $rel
    Remove-ToolkitLink $root   # older install: the root itself was one link
    Get-ChildItem -LiteralPath $root -Force -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-ToolkitLink $_.FullName }
}
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

