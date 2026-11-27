---
name: onboarding
description: "Help devs get started with this LLM dev-tools toolkit in a project—whether the repo already has it or they want to add it. Use when the user is new to a repo that uses these skills, wants to 'get started on this project,' says 'onboarding' or 'set up dev-tools,' or asks how to run checks and reviews here."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Dev-tools onboarding

How a repo is wired to this toolkit. Skills run in the IDE; there is no CLI.

## Adding the toolkit to a repo

When the user asks to set up or add dev-tools, run the setup script for them;
do not ask them to edit `AGENTS.md` by hand. The toolkit checkout is usually a
sibling of the consumer repo or another workspace root.

- From the consumer repo: `../<path-to-toolkit>/scripts/setup-repo.sh .`
  (Windows: `..\<path-to-toolkit>\scripts\setup-repo.ps1 .` or `setup-repo.cmd`).
- From the toolkit root: `./scripts/setup-repo.sh /path/to/consumer-repo`.

The script creates symlinks, copies example templates and integration guides,
writes or appends the reference `AGENTS.md`, and updates `.gitignore`. It links
non-`.github` provider skill roots to the single shared skill catalog and does
not touch `.github/skills/` by default. On Windows the `.ps1` calls `bash.exe`
for the tool-config exports, so a failing `sync-tool-configs.sh` means Git for
Windows is missing.

## A repo that already has the toolkit

- Keep links current without a full setup:
  `../<path-to-toolkit>/scripts/ensure-symlinks.sh .` (add `--pull` to fetch
  first; PowerShell: `ensure-symlinks.ps1 .` with `-Pull`). Provider folders
  hold compatibility links only; never copy shared content into them
  (path map: `docs/tool-compatibility-paths.md`).
- Review and pre-PR reports land in `docs/jira/<TICKET>/`.
- Jira tickets: prefer the Atlassian CLI (`acli jira workitem view <KEY> --json
  --fields summary,description,comment`); Jira MCP is the alternative. Setup:
  `integrations/jira.md`.
- Repo-local context comes first when present: `CONTRIBUTING.md`,
  `docs/ai-onboarding.md` (or `docs/onboarding.md`), and `docs/llm/`.

## Known pitfall

App-level global instructions may not be visible to a CLI session; if the
toolkit is missed, copy the directive into the user-level instruction file.
(sig: spec-gap/global-instructions-not-loaded-in-session)
