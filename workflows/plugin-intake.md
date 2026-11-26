---
description: Plugin intake and pruning - inventory installed plugins, discover candidates in a marketplace, fetch to quarantine, scan, review, check overlap with toolkit assets, decide, install or remove through owner-run plans, and re-index the catalog
---

# Plugin Intake

Use this to add a plugin from a marketplace, to remove unnecessary plugins, or
to audit what is installed. Binding constraints: `rules/plugin-governance.md`
(authority, selection, trust tiers, gates) and
`rules/external-write-authorization.md`. CLI reference: `docs/plugins.md`.
Commands are shown as `python3 scripts/plugins.py` (Windows:
`py -3 scripts/plugins.py` or `scripts/plugins.ps1`).

Exit codes used below: `0` ok, `2` usage, `3` refused, `4` any `block`,
`5` any `review`, `6` git failure or KB unreachable without a catalog,
`7` nothing found.

## Phase 0 - Scope and authorization

1. Write down the request: add (which need or plugin), remove, or audit; which
   tools (for example a CLI tool, a desktop app, a hosted app).
2. List the actions that need an owner instruction naming the plugin and the
   tool: download to quarantine (`fetch`), install, remove, disable, and any
   account or marketplace setting. Without that instruction, do the read-only
   phases and report each action as `NOT RUN` with its exact command.
3. Hosted app (the agent cannot install or remove there): the agent only
   prepares; the owner acts through the app's install card or account setting.
   Prepare the plugin name, marketplace, verdict, and decision for the owner.

## Phase 1 - Inventory

1. `plugins.py catalog --auto` builds capability cards and `catalog.json` from
   every tool home found, scanning each plugin. Add `--from <root>` for a root
   discovery misses. Exit `7`: no plugin found; check `LLM_PLUGINS_DIRS`.
2. `plugins.py status` shows counts per tool, verdict counts, `listing_chars`
   per plugin, and undecided plugins. Keep this as the baseline.
3. Install-state questions (installed vs enabled, pins, sources) go to
   `skills/llm-toolchain-provisioning/SKILL.md`.

## Phase 2 - Discover

1. Candidate needs come from the request, from run records where no capability
   fit, and from `INTENTS.md` misses (asks with no route).
2. Get a local copy of the marketplace repository (for example
   `git clone --depth 1 <marketplace-url> <folder>` outside this repository;
   this download needs the owner's go-ahead like any other external action)
   and point `plugins.py marketplace <folder>` at it, with `--query "<need>"`
   or `--all`. It lists entries not yet in the catalog, with source type:
   `in-repo`, or outside the repository with or without a pinned `sha`.
3. Marketplace and directory listings are discovery inputs, not trusted
   install targets (`skills/external-skill-intake/SKILL.md`, "Plugins").

## Phase 3 - Fetch to quarantine (authorized only)

1. `plugins.py fetch <marketplace-dir> <name>` copies an in-repo plugin or
   clones an outside one into `quarantine/<name>` (https only, allowed host,
   pinned `sha` verified), then scans it. It never installs.
2. Exit `3`: refused (no pinned `sha`, host not allowed, unsafe path). Do not
   pass `--allow-unpinned` unless the owner approves that plugin by name after
   seeing the reason. Exit `6`: git failed; report it, do not retry with other
   transports. Exit `7`: name not in the marketplace.
3. Never execute, import, source, or install anything from quarantine.

## Phase 4 - Scan and review

1. `plugins.py scan <plugin-dir> --json` gives the verdict and findings
   (`4` block, `5` review, `0` pass).
2. `block`: reject. Record it in Phase 6 and stop for that plugin.
3. `review`: a read-only reviewer other than the producer reads every finding
   in context and returns accept or reject per finding, with a reason. A
   rejected finding makes the plugin a reject. Tier 3 (community or unknown
   source) also needs the owner's approval by name
   (`rules/plugin-governance.md` § 3).
4. Also run the content checks in `skills/external-skill-intake/SKILL.md`
   ("Plugins") for what the scanner cannot judge: purpose of hooks, MCP
   targets, license, and author.

## Phase 5 - Overlap check

1. `plugins.py recommend "<need>" --json` shows whether a toolkit asset or an
   installed plugin already covers the need. A toolkit asset or installed
   capability that fits makes the candidate a reject or a removal proposal.
2. When the plugin would bring knowledge into the toolkit (not only a
   capability), `python3 scripts/kb.py check` applies the intake gate of
   `rules/knowledge-base.md`.

## Phase 6 - Decide

Record every outcome, including rejects and keeps:

```bash
python3 scripts/plugins.py decide <plugin> --decision add|keep|remove|reject --reason "<why>" --tool <label>
```

`plugins.py decisions` shows the register. The decision is the evidence the
owner approves in Phase 7.

## Phase 7 - Install (owner-run or authorized)

1. `plugins.py plan add <name>[@marketplace] --marketplace-dir <dir>` prints,
   never runs, the install step for every tool detected: CLI commands for a CLI tool, an install card or
   account-setting note for a hosted app, a manual step for others.
2. Show the plan with the verdict and decision. The owner runs it, or
   authorizes the agent to run the CLI commands for named tools.
3. Exit `7`: with `--marketplace-dir`, the name is not in that marketplace
   (for remove: not in the catalog). Without `--marketplace-dir`, add assumes
   marketplace `claude-plugins-official` unless you write
   `<name>@<marketplace>`; pass the real marketplace.

## Phase 8 - Re-catalog and index

1. `plugins.py catalog --auto` again, so the new plugin has a card and its
   installed copy is scanned (the installed copy can differ from quarantine).
2. `catalog` already asks the knowledge base to rescan; if it printed
   `service unreachable`, start the service (`kb.py up`) so the next scan
   indexes the cards.

## Phase 9 - Removal proposals

1. Candidates: `block` verdicts, plugins that duplicate a toolkit asset or
   another plugin, and plugins no task selected, weighed by `listing_chars`.
2. `plugins.py plan remove <name>` prints the removal step for each tool
   whose catalog entry has the plugin. Exit `3`: the
   plugin is protective; stop. Pass `--i-understand` only on an explicit owner
   instruction naming that plugin. Exit `7`: the plugin is not in the catalog.
3. Present every removal as a proposal with its reason; the owner confirms
   each one. Record the outcome with `decide`, then re-run Phase 8.

## Phase 10 - Verify

1. `plugins.py recommend "<need>"` lists the added capability for the need it
   was added for, with its verdict, and no longer lists removed plugins.
2. `plugins.py status`: compare with the Phase 1 baseline (plugin count,
   verdicts, total `listing_chars`).

## Phase 11 - Run record

Report: plugins added, kept, removed, rejected (with reasons and verdicts),
actions left `NOT RUN` for the owner, the before and after `status`
numbers, and reusable findings as `knowledge:` lines
(`rules/knowledge-base.md`).

## Known pitfalls

- Re-scan the installed copy after install (Phase 8); a pass on the quarantine copy does not cover it, because an install can resolve a newer revision. (sig: wrong-assumption/quarantine-scan-taken-as-installed-scan)
- Keep the fetch refusal for unpinned outside entries: a marketplace entry whose source lives outside the marketplace repository can change after review unless it is pinned to a `sha`. (sig: security/unpinned-outside-source-trusted)
- Plan the owner's action; do not report an install in a hosted app as done, because the agent cannot install or remove plugins there. (sig: wrong-assumption/hosted-app-install-taken-as-agent-action)
