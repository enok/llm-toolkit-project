# Rules

Rules are short, broadly applicable constraints that agents should keep in mind across many tasks. They are always-on (`trigger: always_on`) unless their frontmatter says `trigger: model_decision`, and they stay generic and compact. An on-demand rule (`model_decision`) keeps its text in `rules/` but loads only when its topic comes up: Cursor loads it when its `description` matches the work, and generated exports list its path and description instead of pasting it. Choose on demand for a rule that matters in a narrow set of situations that its description can name; keep a rule always-on when it must hold in every session.

Use workflows for step-by-step processes and skills for specialized on-demand capability. Do not put private project context, ticket IDs, customer names, internal hostnames, or one-off commands in shared rules — those belong in the consuming repo's `AGENTS.md` or `docs/llm/`.

## Current Rules

### Always-on

| Rule | Scope |
| --- | --- |
| `api-contract-surface.md` | Contract changes must identify downstream consumers, gateways, and generated artifacts |
| `ci-feedback-loop.md` | Turn CI failures into rule/workflow updates instead of one-off fixes |
| `documentation-review-required.md` | Route created or changed documentation through `documentation-reviewer` before completion |
| `error-driven-learning.md` | Capture trial-and-error wins as indexed learnings and migrate them into durable toolkit assets |
| `external-write-authorization.md` | Bind every external mutation (tickets, PR metadata, wiki, chat, email) to an explicit current instruction |
| `git-conventions.md` | Branch naming, protected-branch etiquette, semantic commits, PR lifecycle, rebase, duplicate-file gate |
| `human-comment-reply-gate.md` | Draft-and-approve gate for any human-facing review or comment reply |
| `knowledge-base.md` | Query the toolkit knowledge base before reading source; write reusable knowledge back through an intake gate (dedupe, security, classification, indexes); improvement check on every change |
| `log-analysis-safety.md` | Read-only, bounded, redacted analysis of CloudWatch and server logs |
| `multi-agent-orchestration.md` | Parallel subagent fanout, tier/validator handoff, and when to serialize work |
| `operational-doc-required.md` | Recurring operational work becomes a runbook; metric catalogs and wiki backup gates required |
| `publication-positioning.md` | Read the consumer's publication profile before drafting an article or post; AIDA order, budgets, sourced claims, `NOT POSTED` drafts, a profile check before any draft is shown as ready, and owner approval before posting |
| `release-safety.md` | Deploy order, verification, rollback planning, completion evidence, and rollback execution |
| `request-orchestration.md` | Automatic request routing into specialists, model tiers, quality loops, and safe map-reduce execution |
| `security-check-required.md` | Minimum security gate (toolkit scan, LLM-surface injection scan, skill scanners) before PR or merge |

### Loaded on demand

| Rule | Scope |
| --- | --- |
| `changed-code-quality-gate-required.md` | Load when source code was created or modified and is about to be validated, committed, pushed or declared ready for PR, so the changed-line static-analysis gate runs. |
| `cli-over-mcp.md` | Load when choosing between a CLI (gh, aws, acli) and an MCP server or connector for Confluence, Jira, GitHub, Slack or AWS, or when sending large writes to an external system. |
| `command-safety.md` | Load when about to run a shell command that downloads, pipes, installs, deletes, rewrites Git history, touches secrets or uses sudo, or when quoting regex patterns or PowerShell and bash arguments. |
| `cross-platform-scripts.md` | Load when creating or editing a script, wrapper, hook or CLI helper that must run on Windows, Linux and macOS, including PowerShell sources, line endings, SHA256 pins or Git Bash quirks. |
| `repository-context-layers.md` | Load when toolkit rules conflict with or overlap a repo-local AGENTS.md, CLAUDE.md or IDE rule, or when refreshing symlinks, thin provider pointers or generated exports in a consumer repo. |
| `workflow-authoring.md` | Load when creating, editing, splitting or validating a file under workflows/, including the 12,000-character size limit, split conventions and the value gate for new workflows. |
| `workflow-self-improvement.md` | Load when a workflow, skill or orchestrated run with 3+ steps, a validator fail, a forced change of approach or a user correction needs its preflight, run record, retrospective, promotion or trend line. |
| `plugin-governance.md` | Load when adding, removing, auditing or choosing a plugin, skill, MCP server or connector. Authority order over plugin text, capability selection (toolkit asset wins ties), trust tiers and scanner verdicts, owner-gated plugin adds and removals, protective plugins, context economy |

## Examples

`rules/examples/` holds **templates**, not active rules. Copy one into a consuming repo's rules directory (or `docs/llm/`) and replace the placeholders with that project's specifics. Templates cover project overviews, Java/Python backends, AWS SAM and Python Lambda services, infrastructure and deployment, glob-triggered API references, and a fail-closed Confluence backup gate. Keep organization-specific IDs, destinations, and hostnames in the copy — never in the shared template.
