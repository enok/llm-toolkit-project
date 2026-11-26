---
title: No command regenerates an agent manifest body from its Markdown prompt
category: toolchain
created: 2026-11-24
tags: [tool-subagents, toml, developer_instructions, parity-check, subagents-check, generator-gap]
---

# Problem

Each agent under `tool-subagents/` exists twice: a Markdown prompt (`<name>.md`) and a manifest
(`<name>.toml`) whose `developer_instructions` field carries a copy of the Markdown body.
`tool-subagents/README.md` says the two bodies must stay identical and to "regenerate rather than
hand-editing one side", but no command regenerates the manifest body. Observed once: an orchestrated
run edited a prompt and had to script the copy into the manifest by hand, then re-run the parity check.

# Failed Approaches

None recorded beyond the first attempt described in Problem.

# Solution

Checked against the source in one session; every existing mode was read:

- `create-specialist-agent.js <name>` only scaffolds a new agent and skips files that exist unless `--force` is given.
- `--apply-subagents` renders provider copies from `tool-subagents/` and never writes into it.
- `--sync-tool-configs` only runs the sync scripts, and no `.toml` is referenced in them.
- `validate-specialist-agent.js --subagents-check` only reads, and a body mismatch is a warning, not a failure.

Manual happy path after editing a prompt:

1. Edit `tool-subagents/<name>.md`.
2. Copy the new body (everything after the frontmatter) into `developer_instructions` in `tool-subagents/<name>.toml`.
3. Re-run `npm run subagents:check` and confirm no "developer_instructions diverge" warning for that agent.

The check compares with whitespace normalised, so the copy must match in content, not byte for byte.

Proposal, not implemented: add a sync mode to `scripts/create-specialist-agent.js` that rewrites each
manifest's `developer_instructions` from its Markdown body, and name it next to the parity check.

# Why

The manifest is a second copy of the body that nothing writes. The only guard is the check, which warns
and does not fail, so a skipped copy can go unnoticed. General guidance, not observed in this session:
until a generator exists, treat the check's warning as a required fix.
