---
description: Maintain the shared LLM toolkit — mine feedback, de-duplicate guidance, add generic skills/workflows, validate indexes, and sync clients
---

# Toolkit Maintenance Workflow

Use this when improving the shared toolkit from PR reviews, CI failures, Confluence/wiki learnings, chat or memory evidence, public LLM-tool docs, or repeated project work.

## Phase 1 — Evidence collection

1. Search recent PRs and CI/review comments for repeated failures, blocked merges, and automation findings.
2. Review orchestrator and subagent outputs for judged misses, contradictions, weak evidence, missing specialists, complexity-tier misassignments, repeated validation gaps, and reusable execution shortcuts.
3. Search internal docs for repeated procedures, architecture analysis patterns, diagram requirements, and operational gotchas.
4. Search official/public LLM-tool docs for provider behavior changes that affect `AGENTS.md`, skills, workflows, MCP, rules, or memory.
5. When the input is chat/history/memory-heavy, use `workflows/chat-knowledge-curation.md` and `skills/chat-knowledge-curation/SKILL.md` to mine evidence into durable assets instead of copying raw chat into shared guidance.
6. Review external skill repositories through `skills/external-skill-intake/SKILL.md`; use them for discovery and generic adaptation only after source, license, SkillSpector, Snyk Agent Scan, and Gen Agent Trust Hub URL review where applicable.
7. For agent self-improvement, eval, trace, and orchestration patterns, include the curated starting points in `skills/external-skill-intake/references/agent-evolution-sources.md` and add reliable community repos only after source and license review.
8. Record only transferable patterns; keep project-specific details in the source project or in a learning marked as evidence.

## Phase 2 — Classification

Classify each finding:

| Finding type | Destination |
| --- | --- |
| Always-on behavioral constraint | `rules/` |
| Repeatable multi-step process that should be manually invoked | `workflows/` |
| Procedure the agent should select automatically, especially with references/templates/scripts | `skills/` |
| Trial-and-error or environment gotcha | `learnings/` (indexed in `learnings/INDEX.md`); promote repeated lessons into the most specific durable asset |
| Consumer-specific command/path/product detail | Consumer repo `docs/llm/` or project docs |
| Reusable LLM/tooling config found in an application repo | Move it into this toolkit; leave only repo-local context or thin synced pointers in the application repo |

Prefer skills/workflows over rules when the knowledge is specialized. Keep root `AGENTS.md`, `README.md`, and `INTENTS.md` as indexes, not full playbooks.

Treat a consumer repo's own committed `docs/llm/` notes as durable repo-local
knowledge, not a transient learning inbox. Treat git-ignored `docs/*` outputs as
local review artifacts unless the user explicitly asks to promote them into a
tracked documentation surface.

For `learnings/`, process at most 5 files per maintenance run. Choose the oldest or highest-signal actionable files first and convert each selected lesson into durable toolkit assets (a rule, workflow step, skill reference, script check, or template). Learnings stay committed: after promotion, mark the learning's `learnings/INDEX.md` row as promoted (`~~strikethrough~~` plus a pointer to the durable asset) and add a `promoted_to:` line to its frontmatter instead of deleting the file. Leave remaining files for later runs.

Every maintenance report must summarize learning processing:

- processed-learning count;
- each selected learning file and the durable asset path or blocker it became;
- remaining-learning count pending for later processing.

## Phase 3 — Genericity and de-duplication

1. Remove branch names, ticket IDs, customer/project names, hostnames, and one-off paths from shared guidance.
2. If a project-specific artifact is useful, turn it into a generic template and move concrete examples to the consumer repo.
3. Remove duplicate instructions across tool-specific surfaces; keep provider files as thin compatibility layers to canonical content.
4. Keep skill names aligned with folder names and descriptions concise enough for automatic matching.
5. For skills, scripts, and CLI helpers, require a Windows, Linux, and macOS run path by default. Prefer portable primary scripts or binaries with OS-specific wrappers only as conveniences.
6. When changing shared scripts, keep flag names, defaults, exit semantics, dry-run behavior, and examples aligned across the canonical implementation and all shell wrappers.
7. When changing setup or sync repair logic, preserve healthy symlinks, junctions, and generated surfaces until a verified replacement is ready.

## Phase 4 — Index and client sync

Update all relevant indexes:

- `AGENTS.md`
- `README.md`
- `INTENTS.md`
- `workflows/README.md`
- `skills/README.md`
- `learnings/INDEX.md`
- Skill `SKILL.md` frontmatter and cross-links
- Sync/generated tool surfaces via `scripts/sync-tool-configs.sh . --skip-agents-md --skip-github` when `.github` is out of scope.

For consumer repos, run their `scripts/sync-llm-configs.sh` or `scripts/sync-llm-configs.ps1` only after confirming they use this toolkit. When this maintenance run added or renamed skills, run `scripts/ensure-symlinks.sh <consumer>` (or `.ps1`) instead: consumer `sync-llm-configs` refreshes generated exports but does not create per-skill links for new skills.

## Phase 5 — Validation

Run, at minimum:

```bash
./scripts/validate-toolkit-indexes.sh
./scripts/security-check-toolkit.sh
./scripts/validate-skills-with-skillspector.sh
if ./scripts/check-new-skill-security.sh --has-work; then
  ./scripts/check-new-skill-security.sh
fi
```

On Windows PowerShell, use the Git Bash wrappers:

```powershell
./scripts/validate-toolkit-indexes.ps1
./scripts/security-check-toolkit.ps1
./scripts/validate-skills-with-skillspector.ps1
bash scripts/check-new-skill-security.sh --has-work
if ($LASTEXITCODE -eq 0) {
  bash scripts/check-new-skill-security.sh
} elseif ($LASTEXITCODE -ne 1) {
  exit $LASTEXITCODE
}
```

Then verify:

- No missing path references from indexes.
- No project-specific names in shared rules, workflows, skills, README, or AGENTS surfaces.
- New or modified scripts and skill examples have a portable Windows/Linux/macOS execution path, or the OS-specific limit is explicit and justified.
- New or modified skills were scanned by SkillSpector and Snyk Agent Scan, and external skill URLs were checked with Gen Agent Trust Hub when applicable. Full skill audits use `scripts/validate-skills-with-skillspector.sh` (or `.ps1`) over every skill. Missing `SNYK_TOKEN` or required Trust Hub inputs is a blocking validation gap unless the user explicitly approves a documented local-only exception.
- All executable shell scripts have executable mode.
- All workflow files are below the repository size limit.
- `git status` contains only intentional changes.

## Phase 6 — Commit and PR safety

1. If unrelated dirty or staged files exist, preserve them and isolate owned
   maintenance edits with explicit path-scoped `git add` and validation.
   Unrelated dirty files are a reason to avoid broad staging or rewrites, not a
   reason to skip a safe, evidence-backed toolkit improvement.
2. Commit changes in the repository's category order.
3. Rebase onto the base branch before push.
4. Run the duplicate-file gate before push.
5. Push only after the user explicitly approves remote updates or the active
   automation prompt already authorizes push after validation.
6. Before opening or updating a draft PR, reconcile the mandatory per-file
   **File changes** table against the live base-to-head diff as required by
   `rules/git-conventions.md § PR File Change Table`.
7. Open or update a draft PR, read the body back to verify the table, and never
   merge directly to a parent branch.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
