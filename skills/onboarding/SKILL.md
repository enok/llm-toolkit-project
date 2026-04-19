---
name: onboarding
description: Help devs get started with this LLM dev-tools toolkit in a project—whether the repo already has it or they want to add it. Use when the user is new to a repo that uses these skills, wants to "get started on this project," or asks how to run checks and reviews here.
---

# Dev-tools onboarding

Help developers onboard on a project that uses this toolkit: how to run reviews and checks (in-agent), and how to add these skills to a repo. No CLI; skills run in the IDE.

## When to Apply

- User says **"onboarding"**, **"set up dev-tools"**, or **"add skills to this repo"** — run the setup script for them (see "Adding the toolkit to a new repo" below).
- User is new to this repo and it already has the toolkit (e.g. symlinked `.agents/skills/` or reference `AGENTS.md`)
- User just added the toolkit to a project and wants to get started
- User asks "how do I run checks here?" or "how do I get started on this codebase?"
- User wants to add the toolkit to a repo that doesn't have it yet

---

## In a repo that already has the toolkit

1. **This repo is ready.** Skills are available (via symlinks or multi-root workspace). Reports from review/pre-pr-check are written to `docs/jira/<TICKET>/` when the agent writes them.

2. **Keeping integration up to date:** When helping in a consumer repo, ensure symlinks match the latest skills. If the toolkit checkout is available (e.g. sibling directory or path from `AGENTS.md`), run the ensure-symlinks script so any new skills are linked without re-running full setup:
   - From the consumer repo: `../<path-to-toolkit>/scripts/ensure-symlinks.sh .` (or on Windows PowerShell: `..\<path-to-toolkit>\scripts\ensure-symlinks.ps1 .`)
   - To fetch latest from remote first: `../<path-to-toolkit>/scripts/ensure-symlinks.sh . --pull` (PowerShell: add `-Pull`)
   This keeps the integration current so the agent always has the latest skill set.

3. **Before opening a PR:** Choose based on what you need:
   - **pre-pr-check** — Full check: the agent runs the repo's lint and tests (and optional Snyk if you want), then performs an in-agent AI review of your diff. Use for "ready for PR," "check my changes," or "pre-PR check this branch."
   - **review** — AI diff review only (no lint, no tests). Use for quick feedback on your changes or when reviewing someone else's branch/PR.
   For both skills, the diff can be staged changes or the current branch vs base; say "review this branch" / "check this PR" to use branch diff. No binary to run.

4. **Quick AI review only:** Use the **review** skill so the agent reviews your staged changes or the current branch/PR diff using the IDE's built-in LLM (no lint or tests).

5. **Other skills:** **test-plan**, **doc-delta**, and **fix** (for acting on `docs/jira/<TICKET>/review-report.json`) are available; invoke by intent.

6. **Task-starter with Jira:** If the user wants to "start a ticket" or use a Jira issue ID (e.g. `ABC-12345`), the **task-starter** skill can fetch the ticket. The **recommended** way is the **Atlassian CLI (acli)** — install and authenticate (see **integrations/jira.md**), then the agent can run `acli jira workitem view <KEY> --json --fields summary,description,comment` and parse the result. **Alternatively**, devs can use **Jira MCP** in Cursor (uses more context). Point them to **integrations/jira.md** for both options; the agent can detect whether acli is installed and help run install/auth on their behalf.

---

## Adding the toolkit to a new repo

**When the user asks to set up or add dev-tools to their repo:** run the setup script for them — do not ask them to manually add `AGENTS.md`.

1. **Locate the toolkit checkout:** It is usually a sibling of the consumer repo (e.g. `../<repo-name-you-cloned>`) or another root in the workspace. Infer the consumer repo (the repo where the user wants setup) and the path to the toolkit from the workspace roots or current directory.
2. **Run the setup script:**
   - From the **consumer repo** root: `../<path-to-toolkit>/scripts/setup-repo.sh .`
   - Or from the **toolkit** root: `./scripts/setup-repo.sh /path/to/consumer-repo`
   - **Windows PowerShell:** `..\<path-to-toolkit>\scripts\setup-repo.ps1 .` (or `scripts\setup-repo.cmd`)
3. Use the terminal to execute the command (with `run_terminal_cmd` or equivalent). The script creates symlinks, copies example templates and integration guides, writes (or appends) the reference `AGENTS.md`, and updates `.gitignore`. On Windows, prefer `setup-repo.ps1` or `setup-repo.cmd`; Git Bash/WSL can run the `.sh` scripts. If `sync-tool-configs.sh` fails, install **Git for Windows** so `bash.exe` is available (the `.ps1` script invokes it for Cursor/Claude/Copilot exports).

**If the user prefers to run the script themselves:** from the toolkit root run `./scripts/setup-repo.sh /path/to/consumer-repo`, or from the consumer repo run `../<path-to-toolkit>/scripts/setup-repo.sh .` (or the `.ps1` / `.cmd` equivalents on Windows). This creates symlinks and the reference `AGENTS.md`; no manual `AGENTS.md` editing needed.

---

## Project context

To tailor onboarding (and other skills) to this repo, the agent can use project-specific context when present:

- **CONTRIBUTING.md** — If present at the repo root, read it for project conventions, test commands, and review process.
- **docs/ai-onboarding.md** (or **docs/onboarding.md**) — If present, read it for AI-assisted development notes, custom intents, or links to standards.

Destination repos can add these committed files so onboarding and other skills stay contextualized (e.g. "how we run tests here", "where to find our style guide").

---

## Reference

- Full guidance and skill list: toolkit root `AGENTS.md`
- Skill authoring: `.agents/skills/AGENTS.md`
