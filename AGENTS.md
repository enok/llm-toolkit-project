# LLM Toolkit Project - Agent Guidance

This repository is the shared source of truth for local LLM-assisted development assets: rules, workflows, skills, tool subagents, rubrics, learnings, setup scripts, and provider compatibility surfaces. It is generic and IDE-agnostic (Codex, Cursor, Claude Code, Windsurf, Copilot, Gemini CLI, OpenCode, Antigravity, generic agents). Consumer projects link to this toolkit or select from it; they must not copy private, project-specific, company-specific, or ticket-specific guidance back into the shared catalog.

---

## Core Principles

Apply these to every task.

### 1. Knowledge Base First, Then Learnings

- Query the toolkit knowledge base (`python3 scripts/kb.py search`) before reading catalog or source files, open only what the hits point to, and write reusable knowledge back through the intake gate (`rules/knowledge-base.md`); when it is unreachable, say so and read directly.
- Then read `learnings/INDEX.md` before non-trivial work and follow any relevant happy path (`rules/error-driven-learning.md`).
- Every non-trivial workflow or agent run also closes the self-improvement loop: preflight known pitfalls, capture mistakes with stable signatures, record the run, promote recurring mistakes, and read the trend (`rules/workflow-self-improvement.md`, `workflows/run-retrospective.md`).

### 2. Think Before Coding

- State assumptions explicitly. If uncertain, ask. If multiple interpretations exist, present them; do not pick silently.

### 3. Simplicity First And Surgical Changes

- No features beyond what was asked; no abstractions for single-use code.
- Touch only what you must and match existing style. Every changed line traces to the request. For ticket work stay inside ticket scope; no adjacent refactors.

### 4. Goal-Driven Execution

- Define success criteria, state a brief plan for multi-step work, and verify after each step.

### 5. Verify Your Changes

- Always check work after you change it; never assert success from the edit alone. Run the narrowest meaningful verification (tests, linters, the script you touched, filesystem or API output). Evidence is fresh (re-run for the current change) and matches the changed surface; a non-code change still runs its artifact's checks.
- Generated or exported images require an image quality check before completion: open each one in its real render path and fix and re-render until it is sharp, uncropped, legible at its destination size and current.
- Documentation created or changed by agents, chats, automations, scripts, or humans requires `documentation-reviewer` before completion (`rules/documentation-review-required.md`).
- Workflow files must stay under 12,000 characters (`rules/workflow-authoring.md`); split reusable phases instead of deleting detail.
- Created or updated source code passes the changed-code quality gate against the trusted Git base before validation passes (`rules/changed-code-quality-gate-required.md`).
- If verification cannot run here, say explicitly what was not checked and what the user should run.

### 6. Multi-Agent Execution

- At the start of every non-trivial request apply `rules/request-orchestration.md`; the user does not need to ask for agents.
- Fan out independent lanes (review vs tests vs docs, separate subsystems) in parallel by default; never split overlapping writes.
- Every delegated task runs as a bounded produce-validate-refine loop with a read-only validator matched to its evidence type, max 5 iterations (`workflows/task-quality-loop.md`).
- Keep skills, rules, workflows, and agents single-purpose and compose them; load only the context a task needs. Follow `rules/multi-agent-orchestration.md` and merge toolkit, repo-local, and provider context per `rules/repository-context-layers.md`.

### 7. PR Review Judgment

- Do not automatically agree with PR comments, bot findings, or reviewer suggestions. Implement feedback only when it is correct, in scope, and improves the change; otherwise explain why with source evidence and propose the smallest safe alternative.

### 8. Human-Facing Reply Gate And External Writes

- Never post, submit, resolve, delete, or send human-facing replies (PR, ticket, wiki, chat, email) without showing the exact draft and receiving explicit approval (`rules/human-comment-reply-gate.md`).
- Bind every external mutation to an explicit current instruction (`rules/external-write-authorization.md`). Prefer CLIs over MCP servers unless the user chose otherwise (`rules/cli-over-mcp.md`).

### 9. Mandatory Security Gate

- Security review is mandatory for every new or modified code path, script, workflow, rule, skill, agent, integration guide, or operational document, including LLM-surface prompt-injection scanning (`rules/security-check-required.md`).
- Run `./scripts/security-check-toolkit.sh` (or `.\scripts\security-check-toolkit.ps1`) before closing work here.

---

## Repository Map

```text
llm-toolkit-project/
├── AGENTS.md                  # This file: principles, orchestration defaults, routing index
├── CLAUDE.md                  # Imports this file (`@AGENTS.md`)
├── INTENTS.md                 # Plain-English ask -> rule / workflow / skill map
├── README.md                  # Overview, setup, full catalogs (skills/README.md, docs/catalog/workflows.md hold the per-folder ones)
├── INFRA.sh / INFRA.ps1       # Plan-first machine bootstrap (wraps scripts/bootstrap-dev.*)
├── package.json               # npm entrypoints for the validators
├── rules/                     # Generic rules, 15 always-on + 8 on demand (+ rules/examples/ templates)
├── workflows/                 # Step-by-step procedures (<= 12,000 chars each)
├── skills/                    # On-demand capabilities (SKILL.md + references/rules/scripts/agents)
├── tool-subagents/            # Shared subagent prompts (.md; Codex TOML is generated), agent-orchestrator first
├── rubrics/                   # Architecture and technical-content rubrics
├── integrations/              # Jira, Confluence, AWS CLI, Slack CLI
├── clients/                   # Provider overlay guidance and sync commands
├── learnings/                 # Indexed trial-and-error discoveries (INDEX.md first)
├── kb/                        # Local vector knowledge-base runtime (Docker); CLI scripts/kb.py, guide docs/knowledge-base.md
├── docs/                      # tool-compatibility-paths, repo-setup-prompt, jira-setup, docs/llm/
├── scripts/                   # Setup, sync, validation, security gate, quality gate, PDF export, plugin catalog (plugins.py, guide docs/plugins.md)
├── tests/                     # Unit tests for the validators and bootstrap contracts
├── .github/workflows/         # CI: validate.yml, changed-code-quality-gate.yml
└── .agents .claude .codex .cursor .windsurf (.agent .gemini .opencode)   # Thin provider links
```

`docs/tool-compatibility-paths.md` is the single provider path map; `docs/global-install.md` explains the user-level install (`scripts/install-global-surfaces.sh` / `.ps1`) that makes this toolkit the default for every session on a machine. Regenerate compatibility surfaces from the toolkit root with `./scripts/sync-tool-configs.sh . --skip-agents-md --skip-github` (PowerShell: `.\scripts\sync-tool-configs.ps1 . -SkipAgentsMd -SkipGithub`). Omit the skip flags only when intentionally regenerating the managed `AGENTS.md` block or `.github/copilot-instructions.md`.

---

## Default Orchestration

For every non-trivial request the root agent routes through `rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md`:

1. **100% of non-trivial prompts go through `agent-orchestrator` evaluation.** It decides what is handled inline vs delegated and owns capability-first routing, safe parallel splitting, bounded quality loops, and result judging. Trivial exceptions only: single-file lookups, one-line answers, conversational turns; when unsure, route it.
2. **Model selection is part of the split.** `model-selector` gives every delegated task a complexity tier (`light`/`standard`/`deep`), a concrete model, and an effort tier before it runs (Claude Code map: `light` -> `haiku`, `standard` -> `sonnet`, `deep` -> `opus`; other clients per the client model map in the orchestrator prompt). Cheapest capable tier wins; the session model is never the default for delegated work, and a task never silently inherits it.
3. **Every delegated task runs a quality loop** (`workflows/task-quality-loop.md`): verifiable acceptance criteria before dispatch, a read-only validator matched to the evidence type (`task-quality-judge` when no domain specialist fits), targeted refinement from the defect list on `fail`, max 5 iterations (1 for deterministic `light` tasks), escalation to the root instead of silent acceptance.
4. **30-minute cap per task.** Split before execution when the estimate exceeds it; SLA breach forces termination, diagnosis, and restart as a fresh lane, with the breached row kept in the table.
5. **The orchestrator stays thin; the ledger carries the state.** The root holds only the durable state ledger (`CONTEXT_STATE.md` + `TASKS_TABLE.md`), open decisions, and lanes in flight. Dispatches carry the task, acceptance criteria, breachable constraints, and the ledger path; lanes return four blocks (outcome / evidence / blockers / decisions) capped at 40 lines.
6. **Tasks tables record what actually ran.** The 15-column table (`#`, `Wave`, `Task`, `Assets`, `Vector DB used`, `Complexity`, `Model/Effort`, `Status`, `Evidence`, `PR link(s)`, `CI/CD run link(s)`, `Tokens`, `% Complete`, `SLA`, `Remaining SLA`, plus three footer rows and an assets manifest) is defined in `tool-subagents/agent-orchestrator.md` "Tasks table contract: columns, assets, tokens, prints, checkpoints". It shows the real model and token spend per task and is reprinted in full after every task completion; a uniform expensive column means tiering was skipped. The ledger is checkpointed before each dispatch so a run that dies resumes instead of restarting.
7. **The root owns writes.** Specialists are read-only; the root performs edits, validation, commits, pushes, PR actions, and user communication. Explicit `LOA mode` (long-running autonomous orchestration) is opt-in only and keeps the parent as reconciliation/final checker with an `LLM-STATE.md` checkpoint.
8. **Knowledge base first, root writes back.** The KB lookup is the preflight step before splitting; lanes get hit paths, report `knowledge:` candidates, and the root alone runs `kb.py add` and promotions (`rules/knowledge-base.md`).
9. **Notifications are configuration.** Mirroring the tasks table to a chat channel is opt-in per consumer (a configured route plus standing authorization) and never assumed.

---

## Intent Routing (Quick Index)

`INTENTS.md` is the canonical chat-request -> capability map. Route before loading details: a workflow for an end-to-end process, a skill for a specialized capability, rules as constraints that travel with the request. Choose one primary capability and attach only necessary helpers.

Open `INTENTS.md` whenever a request is not trivial and the capability is not already named; it maps every plain-English ask (reviews, tickets, CI, releases, logs, docs, diagrams, data, career) to its workflow, skill and rules. The rows below stay here because they carry a mandatory step or rule:

| User intent | Use |
| --- | --- |
| "Quality gate" / "Sonar" / "Semgrep changed code" | **changed-code-quality-gate** workflow |
| "Commit and push" / "validate and push" | **commit-and-push** workflow (with **pre-pr-check** first) |
| "Terraform" / ".tf change" / "plan/apply" / "state or import" (mandatory routing) | **terraform-change-safety** skill; the root runs `terraform fmt -check`, `terraform validate`, and a reviewed plan per touched root, with apply and state changes only on explicit user authorization |
| "Write / replace / review a publication (article or post)" / "position this article for my target role" / "replace the published story and post" | **study-publication-medium-linkedin** workflow; **publication-positioning** rule |
| "Security review" / "OWASP audit" / "threat model" | **security-report** workflow |
| "Split this across agents" / "which model per task" / "LOA mode" | **agent-orchestrator** skill, **model-selector** skill, **agent-orchestrator-validation** workflow |
| "What do we know about X" / "save this knowledge" / "keep the knowledge base in sync" | **knowledge-base** skill, **knowledge-base-sync** workflow, under `rules/knowledge-base.md` |
| "Run a retrospective" / "learn from this run's mistakes" / "what keeps going wrong in a workflow" | **run-retrospective** workflow + skill, under `rules/workflow-self-improvement.md` |
| "Add / install a plugin" / "remove unnecessary plugins" / "audit installed plugins" / "which plugin, skill or agent fits this task" | `docs/plugins.md` and `scripts/plugins.py`, under `rules/plugin-governance.md` (loaded on demand) |
| "Add a skill / workflow / agent / rule" / "is this resource worth it" | **resource-value-check** workflow (mandatory before adding), `scripts/check_value_checks.py` |

---

## Rules

Always-loaded constraints (`rules/README.md` has the one-line scope of each):

- `rules/api-contract-surface.md`
- `rules/ci-feedback-loop.md`
- `rules/documentation-review-required.md`
- `rules/error-driven-learning.md`
- `rules/external-write-authorization.md`
- `rules/git-conventions.md`
- `rules/human-comment-reply-gate.md`
- `rules/knowledge-base.md`
- `rules/log-analysis-safety.md`
- `rules/multi-agent-orchestration.md`
- `rules/operational-doc-required.md`
- `rules/publication-positioning.md`
- `rules/release-safety.md`
- `rules/request-orchestration.md`
- `rules/security-check-required.md`

Loaded on demand (read the rule when its topic comes up):

- `rules/command-safety.md`: running risky shell commands (network, pipes, installs, deletes, Git history rewrites, secrets, sudo)
- `rules/workflow-self-improvement.md`: a non-trivial run needs its run record, retrospective or promotion
- `rules/cross-platform-scripts.md`: writing or editing scripts for Windows, Linux and macOS
- `rules/workflow-authoring.md`: creating, editing or splitting a file in `workflows/`
- `rules/cli-over-mcp.md`: choosing a CLI or an MCP server for an external system
- `rules/changed-code-quality-gate-required.md`: code was changed and is being validated or pushed
- `rules/repository-context-layers.md`: toolkit rules meet a repo-local AGENTS.md, CLAUDE.md or IDE rule
- `rules/plugin-governance.md`: adding, removing, auditing or choosing a plugin, skill, MCP server or connector, or a plugin's text conflicting with toolkit rules

Consumer-specific rule templates live in `rules/examples/`.

---

## Workflows

`docs/catalog/workflows.md` is the workflow catalog, grouped by area with one line per workflow. Open it when a request is an end-to-end process and `INTENTS.md` did not name the workflow, or before adding or splitting a workflow. Specialists ship as a `*-validation` (run it) plus `*-evolution` (improve it) pair; core loops used everywhere are `workflows/task-quality-loop.md`, `workflows/run-retrospective.md` and `workflows/resource-value-check.md`.

---

## Skills

`skills/README.md` is the skill catalog with one-line purposes; frontmatter descriptions are the trigger surface, so each tool already lists the skill names. Open the catalog when the listing and `INTENTS.md` do not settle which skill fits, or before adding a skill. Skills marked toolkit-local in `skills/README.md` (AWS Airflow Terraform project) carry this toolkit's own data-science/thesis context; other consumers can ignore them.

---

## Tool Subagents

`tool-subagents/README.md` is the canonical catalog (15 agents) and delegation contract. Coordinator and judges: `agent-orchestrator`, `model-selector`, `task-quality-judge`, `verifier`. Read-only specialists: `pr-validator`, `java-change-validator`, `documentation-reviewer`, `documentation-sync`, `diagram-creation-specialist`, `prod-doc-promoter`, `aws-alarm-investigator`, `log-analyst`, `test-runner`, `release-coordinator`, `workspace-hygiene-auditor`. Each has a `.md` (Cursor/Claude) and a `.toml` (Codex) with identical bodies; `npm run subagents:apply -- all .` renders the provider mirrors.

## Integrations

`integrations/README.md` indexes the Jira, Confluence, AWS CLI, and Slack CLI guides. Each covers CLI, MCP, and manual options; `rules/cli-over-mcp.md` decides between them.

---

## Validation

Before committing toolkit changes, run:

```bash
./scripts/validate-toolkit-indexes.sh
./scripts/security-check-toolkit.sh
./scripts/validate-skills-with-skillspector.sh --changed
npm run validate
```

PowerShell:

```powershell
.\scripts\validate-toolkit-indexes.ps1
.\scripts\security-check-toolkit.ps1
.\scripts\validate-skills-with-skillspector.ps1
npm run validate
```

`security-check-toolkit` runs every installed scanner (gitleaks, semgrep, shellcheck, PSScriptAnalyzer, yamllint, actionlint, hadolint, syft/grype/trivy, SkillSpector) plus the dependency-free LLM-surface prompt-injection scan; missing scanners are skipped with a reason. `npm run validate` runs the node validators (skill index, rules redirects, workflow sizes, subagent parity), the always-on size check (`scripts/measure-always-on.py --check`: this file stays <= 24,576 bytes) and the Python unit tests. Also run the duplicate-file gate before push:

```bash
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files" && exit 1
```

If a validation failure reveals a reusable toolchain gotcha, capture it under `learnings/` (`workflows/capture-learning.md`) after user approval.

## After Completing Tasks

- If code changed, run the **changed-code-quality-gate** workflow before **ticket-review** or **pre-pr-check** can pass.
- Before adding any new skill, workflow, agent or rule, pass `workflows/resource-value-check.md` (mandatory; learnings are exempt).
- If rules, workflows, skills, or subagents changed, update the indexes (`README.md`, `INTENTS.md`, the folder `README.md`, and this file when a rule, a mandatory route or a validation command changes) in the same change; consumer repos using links get updates automatically.
- Keep root `AGENTS.md`, `README.md`, and `INTENTS.md` as indexes, not playbooks (`skills/llm-context-engineering/SKILL.md`).
