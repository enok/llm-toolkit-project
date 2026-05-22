---
description: Maintain the shared LLM toolkit — mine feedback, de-duplicate guidance, add generic skills/workflows, validate indexes, and sync clients
---

# Toolkit Maintenance Workflow

Use this when improving the shared toolkit from PR reviews, CI failures, Confluence/wiki learnings, public LLM-tool docs, or repeated project work.

## Phase 1 — Evidence collection

1. Search recent PRs and CI/review comments for repeated failures, blocked merges, and automation findings.
2. Search internal docs for repeated procedures, architecture analysis patterns, diagram requirements, and operational gotchas.
3. Search official/public LLM-tool docs for provider behavior changes that affect `AGENTS.md`, skills, workflows, MCP, rules, or memory.
4. Record only transferable patterns; keep project-specific details in the source project or in a learning marked as evidence.

## Phase 2 — Classification

Classify each finding:

| Finding type | Destination |
| --- | --- |
| Always-on behavioral constraint | `rules/` |
| Repeatable multi-step process that should be manually invoked | `workflows/` |
| Procedure the agent should select automatically, especially with references/templates/scripts | `skills/` |
| Trial-and-error or environment gotcha | `learnings/` |
| Consumer-specific command/path/product detail | Consumer repo `docs/llm/` or project docs |

Prefer skills/workflows over rules when the knowledge is specialized. Keep root `AGENTS.md`, `README.md`, and `INTENTS.md` as indexes, not full playbooks.

## Phase 3 — Genericity and de-duplication

1. Remove branch names, ticket IDs, customer/project names, hostnames, and one-off paths from shared guidance.
2. If a project-specific artifact is useful, turn it into a generic template and move concrete examples to the consumer repo.
3. Remove duplicate instructions across tool-specific surfaces; keep provider files as thin compatibility layers to canonical content.
4. Keep skill names aligned with folder names and descriptions concise enough for automatic matching.
5. For skills, scripts, and CLI helpers, require a Windows, Linux, and macOS run path by default. Prefer portable primary scripts or binaries with OS-specific wrappers only as conveniences.

## Phase 4 — Index and client sync

Update all relevant indexes:

- `AGENTS.md`
- `README.md`
- `INTENTS.md`
- `workflows/README.md`
- Skill `SKILL.md` frontmatter and cross-links
- Sync/generated tool surfaces via `scripts/sync-tool-configs.sh . --skip-agents-md`

For consumer repos, run their `scripts/sync-llm-configs.sh` or `scripts/sync-llm-configs.ps1` only after confirming they use this toolkit.

## Phase 5 — Validation

Run, at minimum:

```bash
./scripts/validate-toolkit-indexes.sh
./scripts/security-check-toolkit.sh
```

On Windows PowerShell, use the Git Bash wrappers:

```powershell
./scripts/validate-toolkit-indexes.ps1
./scripts/security-check-toolkit.ps1
```

Then verify:

- No missing path references from indexes.
- No project-specific names in shared rules, workflows, skills, README, or AGENTS surfaces.
- New or modified scripts and skill examples have a portable Windows/Linux/macOS execution path, or the OS-specific limit is explicit and justified.
- All executable shell scripts have executable mode.
- All workflow files are below the repository size limit.
- `git status` contains only intentional changes.

## Phase 6 — Commit and PR safety

1. Commit changes in the repository's category order.
2. Rebase onto the base branch before push.
3. Run the duplicate-file gate before push.
4. Push only after the user explicitly approves remote updates.
5. Open or update a draft PR; never merge directly to a parent branch.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
