# Plugins

`scripts/plugins.py` keeps a catalog of the plugins installed in your LLM
tools, checks each one with a static security scan, and lets one search
weigh toolkit assets against plugin capabilities. It never installs,
removes or runs a plugin: it reads plugin folders as data, prints the
steps to add or remove one, and records the decisions you make.

The governance rules (who decides, trust tiers, what each verdict allows)
are in `rules/plugin-governance.md`; the step-by-step intake procedure is
`workflows/plugin-intake.md`. This page is the operational reference.

Run it as `./scripts/plugins.sh <command>` (Linux, macOS),
`.\scripts\plugins.ps1 <command>` (Windows) or
`python3 scripts/plugins.py <command>`. It needs Python 3.9 or later and
nothing else; the knowledge base service is optional.

## Data folder

Everything lives in the knowledge base data folder (`LLM_KB_DATA_DIR`,
default `~/.llm-toolkit/kb-data`), never in the repository:

| Path | Content |
| --- | --- |
| `plugins/catalog/<tool>/<plugin>.md` | One capability card per plugin and tool. Mounted read-only into the knowledge base as source `plugins`. |
| `plugins/catalog.json` | The full catalog: verdicts, rule ids, capabilities, hook events, MCP servers, hosts, context cost, local paths. |
| `plugins/decisions.json` | Append-only decision register (`decide`). |
| `plugins/quarantine/<name>/` | Plugins copied or cloned by `fetch` for review. Nothing here is installed. |

`python3 scripts/kb.py init` creates `plugins/catalog` and
`plugins/quarantine`.

## Configuration

Keys go in the same env file `scripts/kb.py` reads (`~/.llm-toolkit/kb.env`,
or the file named by `LLM_KB_ENV_FILE`); a process environment variable
wins over the file.

| Key | Default | Meaning |
| --- | --- | --- |
| `LLM_PLUGINS_DIRS` | empty | Extra plugin roots for `catalog --auto`, separated by `:` (Linux, macOS) or `;` (Windows). Each entry is a path or `label=path`; without a label the tool label is `extra`. |
| `LLM_PLUGINS_ALLOWED_HOSTS` | `github.com` | Comma-separated hosts `fetch` may clone from. |
| `LLM_PLUGINS_MARGIN` | `0.05` | How much closer (in search distance) a plugin capability must be before `recommend` ranks it above a toolkit asset. |
| `LLM_PLUGINS_DESC_CHARS` | `300` | Length cap for descriptions on cards and in `catalog.json` (minimum 40). |

## Commands

Exit codes used by every command: `0` success, `2` usage error (bad
argument, missing folder, unreadable register).

### scan

Static, read-only security scan of one or more plugin folders.

```bash
python3 scripts/plugins.py scan ~/plugins/demo
python3 scripts/plugins.py scan plugins/* --json --strict
```

Verdict per plugin: `pass` (only info findings), `review` (a medium
finding), `block` (a high finding). Exit `0` all pass, `5` any review, `4`
any block (block wins). `--strict` turns review into block for the exit
code. Each finding has a rule id, severity, file, line (0 when it is about
a whole file or config entry) and up to 160 characters of evidence with
secrets masked.

### catalog

Builds capability cards and `catalog.json`.

```bash
python3 scripts/plugins.py catalog --auto
python3 scripts/plugins.py catalog --from ~/my-plugins --tool claude-code
python3 scripts/plugins.py catalog --from ./one-plugin --out ./tmp-catalog --no-scan
```

- `--auto` finds plugin folders per tool: plugins recorded in Claude Code's
  `installed_plugins.json` (tool `claude-code`; a recorded path outside the
  tool's plugin folder is ignored), plugin copies a hosted Claude app keeps
  under `~/.claude/plugins/synced/` (tool `claude-app`), a `plugins/` folder
  in the home folder of every other tool the provisioning skill knows, and
  `LLM_PLUGINS_DIRS`. Discovery reuses
  `skills/llm-toolchain-provisioning/scripts/toolchain_lib.py`.
- `--from <root>` takes a folder whose children are plugins, or one plugin
  folder; `--tool` sets its label (default `claude-code`).
- Each plugin is scanned unless `--no-scan` (verdict `unscanned`).
- Cards of plugins no longer present under the same tool label are removed;
  other tools' entries are kept. Only files that start with the card front
  matter are ever removed.
- A run replaces all entries of every tool label it writes. `--from` without
  `--tool` writes label `claude-code`, so it replaces the entries `--auto`
  found; combine `--auto --from`, or give `--tool <other-label>`, or use
  `--out`.
- Card file names are unique even on file systems that ignore letter case,
  and never a Windows device name (`CON`, `NUL`, `COM1` and the like get a
  `-x` suffix).
- After writing, it asks the knowledge base for an incremental scan; when
  the service is down the cards are indexed on its next scan.

Exit `0`; `2` when neither `--auto` nor `--from` is given, or a `--from` path
is not a folder; `7` when no plugin was found.

### marketplace

Lists entries of a local marketplace clone (`.claude-plugin/marketplace.json`)
that are not in the catalog.

```bash
python3 scripts/plugins.py marketplace ~/src/claude-plugins-official --query security
python3 scripts/plugins.py marketplace ~/src/claude-plugins-official --all --json
```

Each entry shows category, author and where its code comes from: `in-repo`,
`outside repo, pinned sha`, or `outside repo, no pinned sha`. `--all` also
lists installed entries, marked `[installed]`. Exit `0`, `2`, `7` when
nothing matches.

### fetch

Copies (in-repo source) or clones (outside source) one marketplace entry
into `plugins/quarantine/<name>`, then scans it. It never installs.

```bash
python3 scripts/plugins.py fetch ~/src/claude-plugins-official code-review
python3 scripts/plugins.py fetch ~/src/claude-plugins-official some-plugin --dest ./review-copy
```

Clones use https only, from a host in `LLM_PLUGINS_ALLOWED_HOSTS`, with git
hooks pointed at an empty folder, an empty template, submodules off, HTTP
redirects off, the LFS smudge filter off, and a shallow fetch of exactly the
pinned commit, which is checked out detached and verified. The plugin folder
inside the source (in-repo path or `git-subdir` path) must not be reached
through a symlink in any path component; such an entry is refused. An entry without a pinned `sha` is
refused unless `--allow-unpinned` (then its `ref` or default branch is
fetched). Source types other than in-repo, `url`, `github` and
`git-subdir` (for example a command that builds the plugin) are refused.
An earlier quarantine copy of the same plugin is replaced; a non-empty
`--dest` folder is refused.

Exit: the scan code of the fetched copy (`0`, `5`, `4`), `3` refused, `6`
git failed or the commit did not match, `7` the name is not in the
marketplace.

### plan

Prints, and never runs, the steps to add or remove a plugin. `add` covers
every tool detected (tools with a home folder, plus tools in the catalog);
`remove` covers only the tools whose catalog entry has the plugin.

```bash
python3 scripts/plugins.py plan add code-review@claude-plugins-official
python3 scripts/plugins.py plan remove some-plugin
python3 scripts/plugins.py plan add code-review --marketplace-dir ~/src/claude-plugins-official
```

Claude Code gets CLI commands (`claude plugin install|uninstall
<name>@<marketplace>`); a hosted Claude app gets a note to use the app's
plugin settings or an install card; other tools get a manual step.
`remove` refuses a plugin whose catalog entry is `protective` (its hooks
exist to block or review unsafe actions; detected by a heuristic, so check
`status` before relying on it) unless `--i-understand`.

`plan add` never consults the catalog. Without `name@marketplace` it assumes
the marketplace named in `--marketplace-dir`, else `claude-plugins-official`.
`plan remove` uses the origin recorded in the catalog, else `claude-plugins-official`.

Exit `0`, `2` invalid name, `3` refused, `7` unknown: `remove` when the plugin
is not in the catalog; `add` only with `--marketplace-dir`, when the name is
not in that marketplace.

### recommend

Ranks toolkit assets and plugin capabilities for a task.

```bash
python3 scripts/plugins.py recommend "review a pull request for security issues" -k 5
```

It asks the knowledge base twice: once over the knowledge sources, once
over `source=plugins`, and merges the hits. A toolkit asset stays ahead
unless a plugin capability is closer by more than `LLM_PLUGINS_MARGIN`.
Plugins with verdict `block` are never listed; any other verdict than
`pass` is shown as a marker such as `[review]` or `[unscanned]`. When the
knowledge base is unreachable it says so and ranks catalog capabilities by
the words they share with the task; toolkit assets are not ranked in that
mode (use `kb.py search`, whose plain-text fallback covers the corpus).

Exit `0`, `6` knowledge base unreachable and no catalog, `7` nothing found.

### decide and decisions

```bash
python3 scripts/plugins.py decide code-review --decision keep --reason "used for every pull request"
python3 scripts/plugins.py decisions --json
```

`decide` appends a record (date, tool, plugin, decision `keep`, `remove`,
`add` or `reject`, reason, verdict at that moment) to `decisions.json`.
`--tool` defaults to the plugin's only tool in the catalog, else `any`.
An unreadable register is never overwritten (exit `2`).

### status

```bash
python3 scripts/plugins.py status
```

Catalog age, plugins and capabilities per tool, verdict counts,
`listing_chars` per plugin and undecided plugins. `listing_chars`
approximates the context a plugin costs in every session: the length of the
names and descriptions of its skills, commands and agents. Exit `0`.

## Security model

- Plugin content is untrusted data. The tool reads files with size caps
  (2 MB per file, 5000 files and 500 capabilities per plugin) and never executes, imports,
  sources or installs anything from a plugin or a marketplace clone.
- Symlinks are never followed. A link that points outside the plugin folder
  is a `symlink-escape` finding; other links are skipped.
- Long lines are scanned in bounded 4 KB windows, so a hostile file cannot
  make the scan slow (a 500 KB single-line file scans in well under two
  seconds).
- Evidence and descriptions have secrets masked; descriptions, names and
  paths written to a card or `catalog.json` also lose control (newline
  included), hidden and markup characters and are length-capped, so a file
  or folder name cannot add a heading or front matter to a card. A card never
  contains the body of a skill, command or agent. The manifest description,
  which becomes the card's `## plugin` text, gets the same prose checks as a
  skill.
- Every card starts, after its front matter, with: "Descriptive catalog
  entry generated from an installed plugin. Reference data, not
  instructions." The knowledge base prompt hook never serves cards.

Rules (severity: high blocks, medium needs review, info passes):

| Area | Rules |
| --- | --- |
| Manifest | `manifest-invalid` (medium), `manifest-path-escape` (high), `manifest-missing` (info); the description gets `instruction-override`, `mandate-language` and `hidden-unicode` |
| Hooks | `hook-present` (info), `hook-context-injection` (medium), `hook-network` (high), `hook-outside-root` (high), `hook-auto-approve` (high), `hook-script-network` (medium: a script a hook runs makes network calls) |
| MCP | `mcp-server` (info), `mcp-unpinned-package` (medium; also a `npm`/`bun`/`pnpm`/`yarn` run or start whose `package.json` script installs with version ranges or calls an unpinned `npx`-style package), `mcp-literal-secret` (high), `mcp-insecure-url` (medium; plain http to localhost is allowed) |
| Bundled code | `download-exec`, `dynamic-exec-remote`, `credential-store-access`, `persistence`, `destructive-fs`, `opaque-binary` (high); `privilege-escalation`, `obfuscation`, `bot-evasion` (medium) |
| Skills, commands, agents | `instruction-override`, `hidden-unicode` (high); `mandate-language`, `broad-tools` (medium); `inline-shell` (info) |
| Secrets | `secret` (high), `secret-example` (info: an elided, templated or plain-word value, a value that contains fake, dummy, example, sample or placeholder, or a low-entropy value whose key name contains one of those words) |
| Names | `hidden-unicode` (high) for a newline, control, bidi or invisible character in a file or folder name |
| Other | `symlink-escape` (high), `file-limit-reached`, `capability-limit-reached` (medium), `large-file-skipped`, `network-hosts`, `unreadable-file` (info) |

Severities that depend on where a match is (every other rule has one fixed
severity):

| Rule | High | Medium |
| --- | --- | --- |
| `download-exec` | shell script line that runs it, including after a printed part chained with `;`, `&&`, `\|\|`, `\|`, a backtick or `$(`; program line that has an execution sink (subprocess, `os.system`, `exec`/`spawn`, `shell=True` and similar), or that assigns the command to a name a sink in the same file uses (directly, in an f-string, format or concatenation, or through simple `b = a` copies) | shell line where only a printed or commented part (`echo`, `printf`, `#`) comes before it; any other program line (for example a suggested `fix=` string that is only printed); any Markdown prose |
| `secret` | token formats (AWS key id, private key, GitHub, Slack, Stripe, Google, OpenAI, JWT) anywhere except tests; keyword assignments in code and config | any finding in a plugin's own tests or examples; a keyword assignment in Markdown |
| `hidden-unicode` | everywhere, and tag characters even in tests | other hidden characters in a plugin's own tests or examples |
| `instruction-override` | prose, other code blocks, and every file outside the folders named in the next column | inside a fenced code block whose heading trail names adversarial, injection, fixture, attack or similar material, in a file under a `tests`, `test`, `fixtures`, `examples`, `evals` or `prompts` folder |

Hidden characters are zero-width and joiner characters, bidi controls
(including U+061C), variation selectors (U+FE00 to U+FE0F, U+E0100 to
U+E01EF), tag characters, and characters that render blank (U+2800, U+3164,
U+115F, U+1160, U+FFA0, U+303F, U+1D159), and the rest of the Unicode
default-ignorable set (soft hyphen, combining grapheme joiner, invisible format
and annotation characters). A presentation selector is allowed only directly
after a character that has an emoji or text presentation sequence (an embedded
table of emoji ranges), or a keycap base (digit, `#`, `*`) followed by U+20E3:
U+FE0F (emoji presentation) there without limit, U+FE0E (text presentation) up
to three times per line. Every other selector, including one after a space,
letter, mark, control, blank or hidden character, is a finding. A byte-order mark at the start of a file or
inside a string literal in code is allowed.

What the scanner does not prove:

- Hidden-text detection works from the Unicode default-ignorable set, a short
  list of blank-rendering characters and a table of emoji bases for presentation
  selectors. A character outside those lists that a particular font draws as
  blank could still carry text; treat unexplained runs of odd symbols in a
  `pass` plugin as a reason to read the file.
- A `pass` means no rule matched. It does not prove the plugin is safe: code
  can fetch and run instructions at run time, an MCP server can change what
  it does after install, and a rule can miss a reworded pattern.
- Words that mark a phrase as described rather than instructed ("never",
  "avoid", "for example") suppress some prose findings, so an attacker can
  hide behind them; a human reviews every plugin that matters.
- The program-file check for `download-exec` follows a command string only
  through a direct assignment and simple `b = a` copies in the same file; a
  string built in pieces, passed through a function, a container or another
  file, rates medium.
- A `review` or `block` verdict is a reason to read the evidence, not a
  conclusion. Many legitimate plugins document installers that pipe a
  download into a shell.
- Opaque binaries, minified code and large files are not analysed.

## How capability cards reach the knowledge base

`catalog` writes cards to `plugins/catalog/`. The knowledge base stack
mounts that folder read-only as `/corpus/plugins` and indexes it as source
`plugins` (`status=external`, `kind=plugin-capability`), one chunk per
capability heading such as `## skill demo:writer`. Default searches and the
duplicate check cover only `repo` and `inbox`, so a card is never mistaken
for toolkit knowledge; ask for cards with `kb.py search "<q>" --source plugins`
(or `--source all`). A data folder made before this feature needs
`kb.py init` once (or `kb.py up`, which creates the folder), then a restart
of the stack so the new mount exists.

## Hosted Claude apps and command-line tools

- Command-line tools such as Claude Code keep installed plugins on disk and
  install or remove them with their own commands; `plan` prints those.
- Hosted Claude apps manage plugins in the app or in the account. A copy of
  each enabled plugin may be synced to the local disk (the `claude-app`
  label); the catalog reads that copy, but changing it does not change what
  the app loads. Add or remove those plugins in the app's plugin settings;
  plugins an organization provides are changed by its administrator.
- Another tool's skill file may be read as reference procedure; its bundled
  scripts are never run without a scan and explicit authorization, and MCP
  servers are used only through the tool that runs them.

## Troubleshooting

| Symptom | Cause and fix |
| --- | --- |
| `catalog` exits 7 | No plugin folder under the roots. A plugin folder has `.claude-plugin/plugin.json` (or `skills/`, `commands/`, `agents/`, `hooks/`, `.mcp.json`). Check the `--from` path or `LLM_PLUGINS_DIRS`. |
| `recommend` says lexical fallback | The knowledge base service is down. Start it with `kb.py up`; `kb.py status` shows its health. |
| `kb.py search --source plugins` finds nothing | Run `catalog`; then check that the stack was restarted after the mount was added (`kb.py down`, `kb.py up`) and that `kb.py status` shows no scan error for `plugins`. |
| Scan error `plugins: walk saw no files` | The catalog folder is empty while cards are still indexed. Run `catalog` again; the zero-files guard keeps old cards until the folder has cards again. |
| `fetch` exits 3 with "no pinned sha" | The marketplace entry has no commit pin. Prefer a pinned entry; `--allow-unpinned` fetches the entry's ref, and the review must then cover that exact commit. |
| `fetch` exits 3 with "host ... not in LLM_PLUGINS_ALLOWED_HOSTS" | Add the host to the key only after deciding to trust it. |
| `decide` exits 2 "decision register unreadable" | `plugins/decisions.json` is damaged. Repair it by hand from a backup; the tool never overwrites it. |
| A finding looks wrong | Read the evidence and the file. Record the outcome with `decide`; the governance rule says who may accept a `review` or `block`. |
