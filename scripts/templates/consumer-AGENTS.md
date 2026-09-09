# LLM Dev Tools

This repo uses symlinked skills, rules, and workflows for LLM-assisted development.

## Contents

- **Canonical source**: shared skills, rules, workflows, and subagents stay in the toolkit; provider paths are thin compatibility links, not copies
- **Skills**: `.agents/skills/<name>` -> toolkit `skills/<name>`; selected provider roots such as `.agent/skills/`, `.claude/skills/`, `.cursor/skills/`, `.gemini/skills/`, `.opencode/skills/`, and `.windsurf/skills/` link back to the same catalog
- **Claude Code**: `.claude/skills/<name>` and `.claude/agents/` -> shared toolkit content
- **Codex (optional)**: `.codex/skills/<name>` and optional `.codex/agents/`; `AGENTS.md` stays primary
- **Windsurf**: `.windsurf/rules/`, `.windsurf/workflows/`, and optional `.windsurf/skills/<name>` -> shared toolkit content
- **Cursor**: `.cursor/skills/`, `.cursor/rules/`, `.cursor/workflows/`, and `.cursor/agents/` stay symlinked to canonical shared files

## Repo-local LLM files

- `docs/llm/README.md`
- `docs/llm/toolkit-selection.txt`
- `docs/llm/rules/`
- `docs/llm/workflows/`
- `.cursorignore`
- `.cursorindexingignore`

To repair local shared-tool symlinks and refresh local exports from this consumer repo, run `scripts/sync-llm-configs.ps1` or `scripts/sync-llm-configs.sh`.

The generated Shared Toolkit Rules block in `AGENTS.md` carries the clone bootstrap commands and default orchestration contract. If that block is missing or stale, rerun the local sync script before relying on shared rules, workflows, skills, or agents.

Ask the agent by intent (for example: "review my changes", "pre-PR check", "validate solved Jira ticket", "PR validator", "monitor ticket PR", "test plan", "update docs", "Confluence specialist", "diagram specialist", "system architecture specialist", "start ticket ABC-123", "understand this project", "analyze CloudWatch logs", "inspect generated images"). The toolkit `INTENTS.md` is the canonical request-to-capability router; the toolkit `AGENTS.md` carries the quick index and includes the mandatory 100% post-export image-quality inspection gate for generated/exported images.

The shared rules also enforce independent PR-review judgment, minimum necessary ticket-scoped code changes, single-purpose skills/rules/workflows/agents, and mandatory 12,000-character workflow validation. Oversized workflows must be split into reusable workflows and called by path instead of deleting useful detail.

---

## Project-Specific Configuration (LLM refinement)

If this repo has not been configured yet, the LLM agent should walk the developer through these steps in order:

### Step 1 - Curate shared toolkit rules and workflows
Review shared rules via `.windsurf/rules/` and workflows via `.windsurf/workflows/`. Keep the repo-local allowlist in `docs/llm/toolkit-selection.txt`. Do not delete files inside linked toolkit directories.

### Step 2 - Create repo-local rules and workflows
Put repository-only guidance in committed local files such as `docs/llm/rules/`, `docs/llm/workflows/`, or project-specific skill directories that are not toolkit-managed links. Do not place repo-only content inside linked shared-toolkit paths.

### Step 3 - Reduce IDE noise locally
When `.cursor/` is linked to the shared toolkit, keep shared `.cursor/rules/` and `.cursor/workflows/` generic. Use `.cursorignore` and `.cursorindexingignore` to hide non-selected shared files locally.

### Step 4 - Use examples
Read toolkit `rules/examples/` for starting points, then adapt the useful parts into repo-local files.

### Step 5 - Set up integrations
Read toolkit `integrations/` (Jira, Confluence, GitHub, AWS CLI). Ask which integrations the developer actually uses and configure only those.

### Step 6 - Customize repo-local workflows
The linked `.windsurf/workflows/` tree is shared. Keep repo-specific playbooks in `docs/llm/workflows/` or other committed local docs instead of editing shared toolkit workflows.

### Step 7 - Update this AGENTS.md
Collapse or remove this checklist once repo-local context is written. Replace it with architecture, key services, domain terms, and conventions for this repository.

---

## Mandatory agent orchestration (all LLM assistants)

Standing directive for every LLM session in this repository; it composes with
the shared toolkit rules (`rules/request-orchestration.md`) and does not replace them:

1. **100% of prompts go through `agent-orchestrator` evaluation.** The
   orchestrator decides what is handled inline vs delegated; it owns
   capability-first routing, safe parallel splitting, bounded quality loops,
   and result judging. Working a multi-step task inline on the session model
   without routing through it is a rule violation, not a shortcut. Trivial
   exceptions only: single-file lookups, one-line answers, conversational
   turns; when unsure, route it.
2. **Model selection is part of the split.** Run `model-selector` at split
   time so every delegated task gets a complexity tier, a concrete model,
   and a reasoning-effort tier. Cheapest capable tier wins; the session
   model is NOT the default for delegated work.
3. **Tasks tables record what actually ran.** The Model/Effort column must
   show the real model + effort per task; a table showing one uniform
   expensive model is the signal that this step was skipped.
