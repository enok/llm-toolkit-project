---
name: onboarding
description: "Help devs get started with this LLM dev-tools toolkit in a project—whether the repo already has it or they want to add it. Use when the user is new to a repo that uses these skills, wants to 'get started on this project,' says 'onboarding' or 'set up dev-tools,' or asks how to run checks and reviews here."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Dev-tools onboarding

Help developers onboard on a project that uses this toolkit: how to run reviews and checks (in-agent), and how to add these skills to a repo. No CLI; skills run in the IDE.

## When to Apply

- User says **"onboarding"**, **"set up dev-tools"**, or **"add skills to this repo"** — run the setup script for them (see "Adding the toolkit to a new repo" below).
- User is new to this repo and it already has the toolkit (e.g. canonical `skills/`, symlinked `.agents/skills/`, or reference `AGENTS.md`)
- User just added the toolkit to a project and wants to get started
- User asks "how do I run checks here?" or "how do I get started on this codebase?"
- User wants to add the toolkit to a repo that doesn't have it yet

---

## In a repo that already has the toolkit

1. **This repo is ready.** Skills are available (via symlinks or multi-root workspace). Reports from review/pre-pr-check are written to `docs/jira/<TICKET>/` when the agent writes local artifacts.

2. **Keeping integration up to date:** When helping in a consumer repo, ensure symlinks match the latest skills. If the toolkit checkout is available (e.g. sibling directory or path from `AGENTS.md`), run the ensure-symlinks script so any new skills are linked without re-running full setup:
   - From the consumer repo: `../<path-to-toolkit>/scripts/ensure-symlinks.sh .` (or on Windows PowerShell: `..\<path-to-toolkit>\scripts\ensure-symlinks.ps1 .`)
   - To fetch latest from remote first: `../<path-to-toolkit>/scripts/ensure-symlinks.sh . --pull` (PowerShell: add `-Pull`)
   This keeps the integration current so the agent always has the latest skill set. Provider paths are compatibility links; the shared source of truth remains the toolkit `skills/`, `rules/`, `workflows/`, and `tool-subagents/` directories. Use toolkit `docs/tool-compatibility-paths.md` as the path map and do not copy shared content into provider folders.

3. **Before opening a PR:** Choose based on what you need:
   - **pre-pr-check** — Full check: the agent runs the repo's lint and tests (and optional Snyk if you want), the changed-code quality gate, then performs an in-agent AI review of your diff. Use for "ready for PR," "check my changes," or "pre-PR check this branch."
   - **ticket-review** (or **review**) — AI diff review only (no lint, no tests). Use for quick feedback on your changes or when reviewing someone else's branch/PR.
   For both skills, the diff can be staged changes or the current branch vs base; say "review this branch" / "check this PR" to use branch diff. No binary to run.

4. **Quick AI review only:** Use the **ticket-review** (or **review**) skill so the agent reviews your staged changes or the current branch/PR diff using the IDE's built-in LLM (no lint or tests).

5. **Other skills:** **test-plan**, **doc-delta**, **ui-verify**, **figma-compare**, and **fix** (for acting on `docs/jira/<TICKET>/review-report.json`) are available; invoke by intent. For front-end work, ask the agent to **ui-verify** before considering a task done; use **figma-compare** when the story includes a Figma mockup. **ui-verify** uses any browser MCP — configure **Playwright MCP** (`@playwright/mcp`) in non-Cursor hosts; see `skills/ui-verify/references/browser-mcp-providers.md`.

6. **Task-starter with Jira:** If the user wants to "start a ticket" or use a Jira issue ID (e.g. `ABC-12345`), the **task-starter** skill can fetch the ticket. The **recommended** way is the **Atlassian CLI (acli)** — install and authenticate (see **integrations/jira.md**), then the agent can run `acli jira workitem view <KEY> --json --fields summary,description,comment` and parse the result. **Alternatively**, devs can use **Jira MCP** in Cursor (uses more context). Point them to **integrations/jira.md** for both options; the agent can detect whether acli is installed and help run install/auth on their behalf.

---

## Adding the toolkit to a new repo

**When the user asks to set up or add dev-tools to their repo:** run the setup script for them — do not ask them to manually add `AGENTS.md`.

1. **Locate the toolkit checkout:** It is usually a sibling of the consumer repo (e.g. `../<repo-name-you-cloned>`) or another root in the workspace. Infer the consumer repo (the repo where the user wants setup) and the path to the toolkit from the workspace roots or current directory.
2. **Run the setup script:**
   - From the **consumer repo** root: `../<path-to-toolkit>/scripts/setup-repo.sh .`
   - Or from the **toolkit** root: `./scripts/setup-repo.sh /path/to/consumer-repo`
   - **Windows PowerShell:** `..\<path-to-toolkit>\scripts\setup-repo.ps1 .` (or `scripts\setup-repo.cmd`)
3. Use the terminal to execute the command (with `run_terminal_cmd` or equivalent). The script creates symlinks, copies example templates and integration guides, writes (or appends) the reference `AGENTS.md`, and updates `.gitignore`. It links selected non-`.github` provider skill roots back to the single shared skill catalog; it does not create or modify `.github/skills/` by default. On Windows, prefer `setup-repo.ps1` or `setup-repo.cmd`; Git Bash/WSL can run the `.sh` scripts. If `sync-tool-configs.sh` fails, install **Git for Windows** so `bash.exe` is available (the `.ps1` script invokes it for Cursor/Claude/Copilot exports).

**If the user prefers to run the script themselves:** from the toolkit root run `./scripts/setup-repo.sh /path/to/consumer-repo`, or from the consumer repo run `../<path-to-toolkit>/scripts/setup-repo.sh .` (or the `.ps1` / `.cmd` equivalents on Windows). This creates symlinks and the reference `AGENTS.md`; no manual `AGENTS.md` editing needed.

---

## Project context

To tailor onboarding (and other skills) to this repo, the agent can use project-specific context when present:

- **CONTRIBUTING.md** — If present at the repo root, read it for project conventions, test commands, and review process.
- **docs/ai-onboarding.md** (or **docs/onboarding.md**) — If present, read it for AI-assisted development notes, custom intents, or links to standards.
- **docs/llm/** — If present, read it for repo-local LLM context (architecture notes, conventions, notification routes) before applying generic toolkit defaults.

Destination repos can add these committed files so onboarding and other skills stay contextualized (e.g. "how we run tests here", "where to find our style guide").

---

## Reference

- Full guidance and skill list: toolkit root `AGENTS.md`
- Skill authoring: follow `skills/<name>/SKILL.md` frontmatter/body conventions and validate with `scripts/validate-toolkit-indexes.sh`.
