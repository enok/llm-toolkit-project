---
title: Four token-saving tools reviewed - accept only a pinned, switched-off slice and record the conditions
category: security
created: 2026-11-26
tags: [intake, rtk, caveman, ponytail, context-mode, telemetry, pinning, permission-prompt, supply-chain]
---

# Problem
Four community tools that promise fewer tokens or terser output were reviewed read-only
before adoption. Each bundles more than the part that is useful (hooks, installers, a CLI,
a proxy, a stored-prompt database), and the safe slice differs per tool.

# Failed Approaches
- Trusting a config key that is documented: RTK's `[tracking] enabled = false` is parsed but
  not honoured; only the `RTK_DB_PATH` environment variable stops history storage.
- Installing from the upstream marketplace or default branch, which tracks a moving target.
- Reading a scanner BLOCK as final without opening the findings, or as ignorable without
  reading them: each high finding needs a reason.

# Solution
- RTK 1.2.1 (Windows, explicit `rtk <cmd>` only): pass with conditions. Pin exactly with
  `winget --exact` plus `winget pin add`; verify the installer SHA-256 against the release
  checksums; set `RTK_TELEMETRY_DISABLED=1`, `RTK_TEE=0`, `RTK_RECALL=0`, `RTK_DB_PATH=NUL`,
  `RTK_SUPPRESS_HOOK_WARNING=1`; config keeps `[retriever] mode = "disabled"`; never run
  `rtk init`, `trust`, `telemetry enable`, `llm-proxy`, `claude`, `pipeline add` or `plugins`;
  `rtk mvn` runs a repository's own `mvnw` script, so keep it off untrusted repositories.
  1.x links a BUSL-1.1 engine; an Apache-only build exists as a separate release asset.
  Run a smoke test (exit codes equal raw git, no database, tee or marker files).
- Caveman 4.2.0: pass with conditions for the text-only skill (copy files, pin the commit,
  keep the licence and a change note). Block the plugin, installer, CLI and proxy: the CLI
  sends usage telemetry unless switched off.
- Ponytail 5.3.3: pass with conditions as a Claude Code plugin installed from a local clone
  checked out at the reviewed commit, task ledger off, webhook empty. The scanner's three
  high findings are the same hook-path pattern, a Windows backslash normaliser that stays
  inside the plugin root: false positives, with the reason written down.
- Context Mode 2.2.4: not adopted. Its Codex route disables the approval prompt for code
  execution, and its subagent commands arrive as an encoded `node ... <base64>` line, so
  permission rules and the prompt cannot show the real command.
- Related: `skills/token-efficiency/references/rtk-reviewed-deployment.md`,
  `rules/command-safety.md`, `skills/external-skill-intake/SKILL.md`.

# Why
Value and risk sit in different parts of the same package. Adopting the smallest slice that
carries the value, pinned to the reviewed version and with every outbound or persistent
feature switched off and checked, keeps the review valid; a moved pin or a new platform
voids it.
