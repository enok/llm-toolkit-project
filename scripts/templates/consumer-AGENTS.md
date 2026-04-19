<!-- BEGIN LLM TOOLKIT -->
# LLM Dev Tools

This repo uses symlinked skills, rules, and workflows for LLM-assisted development.

## Continuous Learning (ALWAYS-ON)

**Read this first, every session, without being asked.**

Before starting any non-trivial task:

1. Open [`learnings/INDEX.md`](./learnings/INDEX.md) and scan the one-line summaries.
2. If any entry matches the current task (by tag, title, or category), read that file and follow its *Solution*. Do not repeat approaches listed under *Failed Approaches*.

While working, watch for **capture triggers**:

- 2+ failed approaches before success
- A non-obvious fix, platform/toolchain gotcha, or repeated-mistake pattern
- An API / config surprise (e.g. undocumented required parameter)

When a trigger fires, invoke `workflows/capture-learning.md` at task end. Always pause for user approval before committing the new learning.

See `skills/error-driven-learning/SKILL.md` for the full discipline. This skill is always on — the user should never have to ask for it.

## Contents

- **Skills**: `.agents/` -> toolkit `.agents/`
- **Windsurf**: `.windsurf/` -> toolkit `.windsurf/`
- **Cursor**: `.cursor/` -> toolkit `.cursor/`
- **Claude Code**: `.claude/` -> toolkit `.claude/`
- **Codex**: `.codex/` -> toolkit `.codex/`
- **Setup**: `.setup/` -> toolkit `.setup/`

## Repo-local LLM files

- `docs/llm/README.md` — local layout notes (junction target of the toolkit)
- `docs/llm/toolkit-selection.txt` — curated shared-toolkit profile
- `learnings/` — committed trial-and-error discoveries
- `.cursorignore`
- `.cursorindexingignore`

Repo-local rules and workflows no longer live under `docs/llm/rules/` or `docs/llm/workflows/`. Put repo-specific guidance in this `AGENTS.md`, in `learnings/`, or in repo-local skills under the shared toolkit.

To repair local shared-tool symlinks, re-run the repo-local setup script (for example `./_setup-llm-local.cmd` on Windows).

Ask the agent by intent (for example: "review my changes", "pre-PR check", "test plan", "update docs"). See the toolkit `README.md` for the full skill and workflow index.

---

## Project-Specific Configuration (LLM refinement)

If this repo has not been configured yet, the LLM agent should walk the developer through these steps in order:

### Step 1 - Curate shared toolkit skills and workflows
Review shared skills via `.agents/skills/` and workflows via `.windsurf/workflows/`. Keep the repo-local allowlist in `docs/llm/toolkit-selection.txt`. Do not delete files inside linked toolkit directories.

### Step 2 - Create repo-local guidance
Put repository-only guidance in this `AGENTS.md`, in committed `learnings/` entries, or in repo-local skills that extend the shared toolkit. Do not place repo-only content inside linked `.windsurf/`, `.cursor/`, `.claude/`, `.codex/`, or `.setup/` — those directories are junctions into the shared toolkit and changes there would edit the toolkit itself.

### Step 3 - Reduce IDE noise locally
When `.cursor/` is linked to the shared toolkit, keep shared `.cursor/rules/` and `.cursor/workflows/` generic. Use `.cursorignore` and `.cursorindexingignore` to hide non-selected shared files locally.

### Step 4 - Use templates
Read `.setup/examples/` for starting points, then stop using or hide it in the IDE. Do not delete linked files there.

### Step 5 - Customize repo-local workflows
The linked `.windsurf/workflows/` tree is shared. Keep repo-specific playbooks inside this `AGENTS.md`, repo-local skills, or other committed local docs instead of editing shared toolkit workflows.

### Step 6 - Update this AGENTS.md
Collapse or remove this checklist once repo-local context is written. Replace it with architecture, key services, domain terms, and conventions for this repository.
<!-- END LLM TOOLKIT -->
