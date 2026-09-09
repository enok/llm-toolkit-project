# Rules

Rules are short, broadly applicable constraints that agents should keep in mind across many tasks. They are `trigger: always_on` and stay generic and compact.

Use workflows for step-by-step processes and skills for specialized on-demand capability. Do not put private project context, ticket IDs, customer names, internal hostnames, or one-off commands in shared rules — those belong in the consuming repo's `AGENTS.md` or `docs/llm/`.

## Current Rules

| Rule | Scope |
| --- | --- |
| `api-contract-surface.md` | Contract changes must identify downstream consumers, gateways, and generated artifacts |
| `changed-code-quality-gate-required.md` | Blocking static-analysis gate scoped to added or modified lines during code validation |
| `ci-feedback-loop.md` | Turn CI failures into rule/workflow updates instead of one-off fixes |
| `cli-over-mcp.md` | Prefer capable authenticated CLIs over MCP servers, preserving user-selected apps and MCP-only capabilities |
| `code-rules.md` | Coding discipline, source verification, change management, and commit hygiene |
| `command-safety.md` | Review shell commands for destructive, exfiltration, or injection risk before execution |
| `cross-platform-scripts.md` | Agent-authored scripts must run on Windows, Linux, and macOS unless a wrapper is intentionally OS-specific |
| `documentation-review-required.md` | Route created or changed documentation through `documentation-reviewer` before completion |
| `error-driven-learning.md` | Capture trial-and-error wins as indexed learnings and migrate them into durable toolkit assets |
| `external-write-authorization.md` | Bind every external mutation (tickets, PR metadata, wiki, chat, email) to an explicit current instruction |
| `git-conventions.md` | Branch naming, protected-branch etiquette, semantic commits, PR lifecycle, rebase, duplicate-file gate |
| `human-comment-reply-gate.md` | Draft-and-approve gate for any human-facing review or comment reply |
| `log-analysis-safety.md` | Read-only, bounded, redacted analysis of CloudWatch and server logs |
| `multi-agent-orchestration.md` | Parallel subagent fanout, tier/validator handoff, and when to serialize work |
| `operational-doc-required.md` | Recurring operational work becomes a runbook; metric catalogs and wiki backup gates required |
| `release-safety.md` | Deploy order, verification, rollback planning, completion evidence, and rollback execution |
| `repository-context-layers.md` | How toolkit rules merge with repo-local `AGENTS.md`, `CLAUDE.md`, and thin provider surfaces |
| `request-orchestration.md` | Automatic request routing into specialists, model tiers, quality loops, and safe map-reduce execution |
| `security-check-required.md` | Minimum security gate (toolkit scan, LLM-surface injection scan, skill scanners) before PR or merge |
| `workflow-authoring.md` | 12K size limit, split conventions, single responsibility, and composition for `workflows/` |

## Examples

`rules/examples/` holds **templates**, not active rules. Copy one into a consuming repo's rules directory (or `docs/llm/`) and replace the placeholders with that project's specifics. Templates cover project overviews, Java/Python backends, AWS SAM and Python Lambda services, infrastructure and deployment, glob-triggered API references, and a fail-closed Confluence backup gate. Keep organization-specific IDs, destinations, and hostnames in the copy — never in the shared template.
