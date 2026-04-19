
# LLM Dev Tools

This repo uses symlinked skills, rules, and workflows for LLM-assisted development.

## Contents

- **Skills**: `.agents/` -> toolkit `.agents/`
- **Windsurf**: `.windsurf/` -> toolkit `.windsurf/`
- **Cursor**: `.cursor/` -> toolkit `.cursor/`
- **Claude Code**: `.claude/` -> toolkit `.claude/`
- **Codex**: `.codex/` -> toolkit `.codex/`
- **Setup**: `.setup/` -> toolkit `.setup/`

## Repo-local LLM files

- `docs/llm/README.md`
- `docs/llm/toolkit-selection.txt`
- `docs/llm/rules/`
- `docs/llm/workflows/`
- `.cursorignore`
- `.cursorindexingignore`

To repair local shared-tool symlinks and refresh local exports from this consumer repo, run `scripts/sync-llm-configs.ps1` or `scripts/sync-llm-configs.sh`.

Ask the agent by intent (for example: "review my changes", "pre-PR check", "test plan", "update docs"). See the dev-tools toolkit `AGENTS.md` for the full skill and workflow index.

---

## Project-Specific Configuration (LLM refinement)

If this repo has not been configured yet, the LLM agent should walk the developer through these steps in order:

### Step 1 - Curate shared toolkit rules and workflows
Review shared rules via `.windsurf/rules/` and workflows via `.windsurf/workflows/`. Keep the repo-local allowlist in `docs/llm/toolkit-selection.txt`. Do not delete files inside linked toolkit directories.

### Step 2 - Create repo-local rules and workflows
Put repository-only guidance in committed local files such as `docs/llm/rules/` and `docs/llm/workflows/`. Do not place repo-only content inside linked `.windsurf/`, `.cursor/`, `.claude/`, `.codex/`, or `.setup/`.

### Step 3 - Reduce IDE noise locally
When `.cursor/` is linked to the shared toolkit, keep shared `.cursor/rules/` and `.cursor/workflows/` generic. Use `.cursorignore` and `.cursorindexingignore` to hide non-selected shared files locally.

### Step 4 - Use templates
Read `.setup/examples/` for starting points, then stop using or hide it in the IDE. Do not delete linked files there.

### Step 5 - Customize repo-local workflows
The linked `.windsurf/workflows/` tree is shared. Keep repo-specific playbooks in `docs/llm/workflows/` or other committed local docs instead of editing shared toolkit workflows.

### Step 6 - Update this AGENTS.md
Collapse or remove this checklist once repo-local context is written. Replace it with architecture, key services, domain terms, and conventions for this repository.
