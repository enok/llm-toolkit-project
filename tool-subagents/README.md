# Tool Subagents

This directory is the canonical source for shared subagent prompts rendered into provider compatibility surfaces such as `.cursor/agents/`, `.claude/agents/`, and optional `.codex/agents/`. Codex primarily uses `AGENTS.md` plus direct file paths; `.codex/agents/` is optional when the local setup supports it.

Every agent is a pair: `<name>.md` (YAML frontmatter — `name`, `description`, `model`, and a `readonly` / `is_background` contract — plus the prompt body) and `<name>.toml` (`description`, `developer_instructions`, `name`) for tools that consume the TOML form. The `.toml` body must stay identical to the `.md` body; regenerate rather than hand-editing one side.

`agent-orchestrator` is the default coordinator for non-trivial requests. It classifies the request, chooses specialists, splits safe parallel work, scores each delegated task's complexity tier (`light`/`standard`/`deep`), runs every delegated task as a bounded produce->validate->refine quality loop (max 5 iterations, see `workflows/task-quality-loop.md`), presents the fanout as a wave-ordered task table with validators, loop counters, rough ETAs, and live status, and reduces child findings. In normal mode the root then edits, validates, commits, or answers. Explicit LOA (letter-of-authorization) mode changes this only when requested: the parent reconciles final results while the coordinator dispatches separately owned authorized async execution, maintains an excluded state checkpoint, and reports auditable SLA/milestones.

## Catalog

| Agent | Role |
| --- | --- |
| `agent-orchestrator` | Automatic request router and map-reduce coordinator with per-task complexity tiering, bounded quality loops, and explicit LOA mode for authorized async execution, state checkpoints, and SLA rollups |
| `model-selector` | Read-only per-task model selection and overspend auditor: assigns tier, model, effort, and token band at split time and flags tasks that ran above their cheapest capable tier |
| `task-quality-judge` | Per-task quality-loop validator: judges one delegated task's output against its acceptance criteria and returns a pass/fail verdict with a targeted defect list |
| `parallel-explorer` | Fast codebase reconnaissance |
| `cross-repo-analyst` | Multi-repo impact map |
| `code-reviewer` | Implementation risk and regression review |
| `test-runner` | Test selection and failure triage |
| `contract-analyzer` | API, schema, event, and downstream impact |
| `java-change-validator` | Read-only Java change validation across code, tests, wiring, docs, build evidence, and reviewer drafts |
| `pr-validator` | Read-only live-head PR/ticket readiness, comments, CI, docs, and approve/block validation |
| `security-auditor` | Security-focused review |
| `owasp-security-auditor` | OWASP-style audit lane |
| `ci-triage` | CI log analysis |
| `log-analyst` | Read-only operational log evidence reduction |
| `aws-alarm-investigator` | Read-only AWS CloudWatch alarm root-cause investigator with confidence-rated hypotheses and reviewable possible fixes |
| `terraform-specialist` | Read-only Terraform module/root, plan safety, state/import lifecycle, multi-env, secrets/metadata hygiene, and drift-codification validation — mandatory for all Terraform requests |
| `dag-glue-specialist` | Read-only Airflow DAG, MWAA, AWS Glue job, crawler, Data Catalog, and ETL pipeline validation |
| `system-architecture-specialist` | Read-only application architecture, service boundary, data-flow, integration, and quality-attribute review |
| `diagram-creation-specialist` | Read-only source-grounded diagram planning, notation, export, and image-quality validation |
| `documentation-sync` | Docs and changelog drift |
| `documentation-reviewer` | Read-only review for documentation created or changed by agents, chats, automations, scripts, or humans |
| `confluence-documentation-specialist` | Read-only Confluence page, hierarchy, attachment, comment, and source-to-wiki validation |
| `prod-doc-promoter` | Read-only production documentation promotion planning for deployed-ticket wiki cleanup and canonical doc updates |
| `release-coordinator` | Release order, verification, and rollback |
| `verifier` | Final skeptical completion check and in-loop quality-loop validator |

## Delegation contract

- Parent agents pass objective, scope, constraints, relevant paths, allowed tools, write ownership, expected output, acceptance criteria, a validator assignment, a loop budget (max 5; 1 for deterministic `light` tasks), and a complexity tier (`light`/`standard`/`deep`, see `tool-subagents/agent-orchestrator.md` and `workflows/task-quality-loop.md`).
- Child agents return evidence, touched paths, findings, risks, validation commands, and recommended next steps; a delegated task is done only when its assigned validator returns `pass`.
- In normal mode, root agents own final communication, edits, validation,
  commits, pushes, and PR actions. Explicit LOA mode instead keeps the parent as
  reconciliation/final checker while separately owned async agents perform
  user-authorized execution and LOA alone checkpoints a state file (for example
  `LLM-STATE.md` at the consumer repo root).
- A task's complexity tier is applied through the platform's per-task mechanism (model/effort parameter, IDE picker, per-agent override), and doing so is mandatory whenever such a mechanism exists: every dispatch sets the model explicitly from the client model map in `tool-subagents/agent-orchestrator.md` (Claude Code Agent tool: `light` -> `haiku`, `standard` -> `sonnet`, `deep` -> `opus`). Omitting an available parameter so the child inherits the session default is a routing defect. Only when the platform has no mechanism does the task run at platform default, and that fact is stated, not silently assumed.
- `readonly` in agent frontmatter is an advisory contract, not platform-enforced
  everywhere. A mode-capable coordinator may declare writable authority, but
  its prompt must restrict writes and external effects to explicit LOA mode;
  ordinary specialists and normal coordinator mode remain read-only.
- Human-facing output produced by a subagent (PR comments, review replies, wiki
  comments, chat messages) stays a draft until the user approves it, per
  `rules/human-comment-reply-gate.md`.
- Canonical `tool-subagents/*.md` frontmatter always carries a portable
  `model:` value (`inherit`/`haiku`/`sonnet`/`opus` — never a provider-specific
  word like Cursor's `fast`); an optional `tier:` (`light`/`standard`/`deep`)
  is a cost hint layered on top, independent of the complexity tier a parent
  agent assigns at dispatch time. `scripts/create-specialist-agent.js
  --apply-subagents` renders that hint per provider instead of copying it
  verbatim: `tier: light` becomes `model: haiku` in `.claude/agents` renders
  and `model: fast` in `.cursor/agents` renders, and the toolkit-only
  `readonly`/`tier` keys are dropped from both, since Codex reads `.toml`
  only and never sees this rewrite.

Regenerate compatibility surfaces with:

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md
```

In PowerShell:

```powershell
./scripts/sync-tool-configs.ps1 . -SkipAgentsMd
```
