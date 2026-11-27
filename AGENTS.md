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

- Always check work after you change it; never assert success from the edit alone. Run the narrowest meaningful verification (tests, linters, the script you touched, filesystem or API output).
- Generated or exported images require an image quality check before completion: open each one in its real render path and fix and re-render until it is sharp, uncropped, legible at its destination size and current.
- Documentation created or changed by agents, chats, automations, scripts, or humans requires `documentation-reviewer` before completion (`rules/documentation-review-required.md`).
- Workflow files must stay under 12,000 characters (`rules/workflow-authoring.md`); split reusable phases instead of deleting detail.
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
- Run `./scripts/security-check-toolkit.sh` (or `.\scripts\security-check-toolkit.ps1`) before closing work here; changed code also passes `workflows/changed-code-quality-gate.md`.

---

## Repository Map

```text
llm-toolkit-project/
├── AGENTS.md                  # This file: principles, orchestration defaults, routing index
├── CLAUDE.md                  # Thin pointer to AGENTS.md
├── INTENTS.md                 # Plain-English ask -> rule / workflow / skill map
├── README.md                  # Overview, setup, full catalogs
├── INFRA.sh / INFRA.ps1       # Plan-first machine bootstrap (wraps scripts/bootstrap-dev.*)
├── package.json               # npm entrypoints for the validators
├── rules/                     # Generic rules, 15 always-on + 8 on demand (+ rules/examples/ templates)
├── workflows/                 # Step-by-step procedures (<= 12,000 chars each)
├── skills/                    # On-demand capabilities (SKILL.md + references/rules/scripts/agents)
├── tool-subagents/            # Shared subagent prompts (.md + .toml), agent-orchestrator first
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

| User intent | Use |
| --- | --- |
| "Review my changes" / "review this PR" | **ticket-review** workflow |
| "Pre-PR check" / "ready for PR" | **pre-pr-check** workflow + skill |
| "Quality gate" / "Sonar" / "Semgrep changed code" | **changed-code-quality-gate** workflow |
| "Validate this PR" / "approve or block" | **pr-validator-validation** workflow + **pr-validator** skill |
| "Validate Java changes" | **java-change-validation** workflow + **java-change-validator** skill |
| "Commit and push" / "validate and push" | **commit-and-push** workflow (with **pre-pr-check** first) |
| "Fix CI" / "address PR comments" / "PR bot findings" | **gh-fix-ci**, **gh-address-comments**, **pr-automation-review** workflows |
| "Start ticket ABC-123" / "implement a ticket" | **ticket-implementation** workflow |
| "Run tests" / "test plan" | **run-tests** workflow |
| "Terraform" / ".tf change" / "plan/apply" / "state or import" (mandatory routing) | **terraform-change-safety** skill; the root runs `terraform fmt -check`, `terraform validate`, and a reviewed plan per touched root, with apply and state changes only on explicit user authorization |
| "Investigate this alarm" / "CloudWatch alarm RCA" | **aws-alarm-investigator-validation** workflow + **aws-alarm-investigator** skill |
| "Analyze logs" / "CloudWatch logs" / "nginx logs" | **log-investigation** workflow + **log-analysis** skill |
| "Incident" / "production issue" / "runbook" | **incident-ops**, **runbook-authoring** skills |
| "Update docs" / "review documentation" | **update-docs** workflow or **doc-delta** skill; **documentation-reviewer-validation** workflow |
| "Architecture docs" / "diagrams" / "C4" / "PlantUML" | **diagram-authoring** skill, **diagram-creation-specialist-validation** |
| "Confluence" / "wiki page" / "promote deployed docs" | **confluence-documentation** workflow + skill; **prod-doc-promoter-validation** |
| "Verify the UI" / "compare with Figma" / "check exported images" | **ui-verify** skill |
| "Export Markdown to PDF" / "PowerPoint deck" | **markdown-pdf-export** workflow + skill |
| "Write / replace / review a publication (article or post)" / "position this article for my target role" / "replace the published story and post" | **study-publication-medium-linkedin** workflow; **publication-positioning** rule |
| "Security review" / "OWASP audit" / "threat model" | **security-report** workflow |
| "Cut a release" / "Maven release" / "E2E for release" | **maven-release** skill |
| "Migrate Jenkins to GitHub Actions" / "CI parity" | **jenkins-to-github-actions** skill |
| "Local env broken" / "set up my machine" | **environment-diagnose** workflow, **local-env-bootstrap** skill, `INFRA.sh` / `INFRA.ps1` |
| "Which plugins are installed" / "reproduce my assistant setup" | **llm-toolchain-provisioning** skill |
| "Split this across agents" / "which model per task" / "LOA mode" | **agent-orchestrator** skill, **model-selector** skill, **agent-orchestrator-validation** workflow |
| "Save tokens" / "compact command output" | **token-efficiency** skill |
| "Create a specialist agent" / "improve the specialist" | **specialist-agent-factory** workflow + skill |
| "Compact this chat" / "mine chat history into assets" | **context-compaction** workflow |
| "What do we know about X" / "save this knowledge" / "keep the knowledge base in sync" | **knowledge-base** skill, **knowledge-base-sync** workflow, under `rules/knowledge-base.md` |
| "Save this as a learning" / "improve the toolkit" | **capture-learning** workflow; **llm-context-engineering** skill |
| "Run a retrospective" / "learn from this run's mistakes" / "what keeps going wrong in a workflow" | **run-retrospective** workflow + skill, under `rules/workflow-self-improvement.md` |
| "Import external skills" | **external-skill-intake** skill |
| "Add / install a plugin" / "remove unnecessary plugins" / "audit installed plugins" / "which plugin, skill or agent fits this task" | `docs/plugins.md` and `scripts/plugins.py`, under `rules/plugin-governance.md` (loaded on demand) |
| "Add a skill / workflow / agent / rule" / "is this resource worth it" | **resource-value-check** workflow (mandatory before adding), `scripts/check_value_checks.py` |
| "Java / Python / JavaScript / shell patterns" | **python-best-practices**, **js-ts-best-practices** skills |
| "Notebook analysis" / "ML experiment" / "data pipeline" | **data-pipeline-change** workflow |
| "Thesis" / "ABNT" | **thesis-writing-main** workflow |
| "Job scan" / "job search" / "track my applications" | **job-search-pipeline** workflow + skill |
| "Is this course / degree / MBA / certification worth it" / "does it carry weight in the market" | **credential-evaluation** skill |
| "Sync my CV with LinkedIn" / "I left my employer, update everywhere" / "keep my CV, profile and job files consistent" | **career-profile-sync** workflow |

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

- `rules/command-safety.md`: running risky shell commands (network, pipes, installs, deletes, sudo)
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

`workflows/README.md` describes every workflow. Specialists ship as a `*-validation` (run it) plus `*-evolution` (improve it) pair.

- **Orchestration and toolkit evolution:** `workflows/task-quality-loop.md`, `workflows/agent-orchestrator-validation.md`, `workflows/agent-orchestrator-evolution.md`, `workflows/model-selector-validation.md`, `workflows/model-selector-evolution.md`, `workflows/specialist-agent-factory.md`, `workflows/context-compaction.md`, `workflows/automation-maintenance.md`, `workflows/capture-learning.md`, `workflows/run-retrospective.md`, `workflows/knowledge-base-sync.md`, `workflows/assistant-workspace-cleanup.md`, `workflows/conversation-monitoring.md`, `workflows/workspace-hygiene-auditor-validation.md`, `workflows/workspace-hygiene-auditor-evolution.md`, `workflows/resource-value-check.md`
- **Core engineering:** `workflows/project-discovery.md`, `workflows/ticket-review.md`, `workflows/pre-pr-check.md`, `workflows/changed-code-quality-gate.md`, `workflows/run-tests.md`, `workflows/update-docs.md`, `workflows/commit-and-push.md`, `workflows/environment-diagnose.md`
- **Tickets, PRs, CI, releases:** `workflows/ticket-implementation.md`, `workflows/ticket-research-and-implementation-and-validation.md`, `workflows/pr-validator-validation.md`, `workflows/pr-validator-evolution.md`, `workflows/java-change-validation.md`, `workflows/gh-address-comments.md`, `workflows/gh-fix-ci.md`, `workflows/pr-automation-review.md`, `workflows/security-check-required.md`, `workflows/security-report.md`
- **Infrastructure, operations, logs:** `workflows/aws-alarm-investigator-validation.md`, `workflows/aws-alarm-investigator-evolution.md`, `workflows/log-investigation.md`, `workflows/aws-airflow-terraform-change.md`, `workflows/aws-airflow-terraform-project.md`, `workflows/aws-data-platform-ops.md`, `workflows/folder-reorganization.md`, `workflows/third-party-installer-vetting.md`
- **Documentation, diagrams, wiki:** `workflows/documentation-reviewer-validation.md`, `workflows/documentation-reviewer-evolution.md`, `workflows/diagram-creation-specialist-validation.md`, `workflows/diagram-creation-specialist-evolution.md`, `workflows/confluence-documentation.md`, `workflows/prod-doc-promoter-validation.md`, `workflows/prod-doc-promoter-evolution.md`, `workflows/markdown-pdf-export.md`, `workflows/study-publication-medium-linkedin.md`, `workflows/technical-content-publishing.md`
- **Data science, thesis, notebooks, pipelines:** `workflows/project-execution-main.md`, `workflows/notebook-analysis-update.md`, `workflows/notebook-to-script.md`, `workflows/notebook-latex-polish.md`, `workflows/ml-experiment-update.md`, `workflows/thesis-writing-main.md`, `workflows/thesis-chapter-writing.md`, `workflows/thesis-plagiarism-check.md`, `workflows/data-source-ingestion.md`, `workflows/data-source-storage-backend.md`, `workflows/dataset-onboarding.md`, `workflows/data-pipeline-change.md`
- **Career and job search:** `workflows/job-search-pipeline.md`, `workflows/career-profile-sync.md`, `workflows/job-portal-profile-sync.md`, `workflows/job-search-attack-plan.md`, `workflows/recruiter-legitimacy-check.md`, `workflows/screening-interview-quick-prep.md`, `workflows/technical-interview-prep.md`

---

## Skills

`skills/README.md` holds the catalog with one-line purposes; frontmatter descriptions are the trigger surface.

### Orchestration And Context Engineering

| Skill | Purpose |
| --- | --- |
| **agent-orchestrator** | Capability-first routing, safe parallel delegation, per-task model tiering, bounded quality loops, durable state ledger, and explicit LOA mode |
| **model-selector** | Assign every task a complexity tier, concrete model, effort, and token band before it runs; audit finished task tables for overspend |
| **specialist-agent-factory** | Create or update reusable specialist agents (subagent prompt, validation/evolution workflows, skill entrypoint, routing, provider overlays) |
| **token-efficiency** | Reduce token consumption: command-output compaction (RTK), `gh --json`/`jq` field selection, ripgrep budgeting, ast-grep, repomix packing |
| **llm-context-engineering** | Keep AGENTS/rules/workflows/skills lean, generic, provider-agnostic, and loaded on demand |
| **llm-toolchain-provisioning** | Export, review, and restore installed LLM assistant extensions (plugins, marketplaces, MCP servers) as a portable manifest |
| **external-skill-intake** | Safely evaluate, download, adapt, scan, and index skills from public LLM-tool repositories |
| **error-driven-learning** | Always-on discipline: read `learnings/INDEX.md` before work and capture trial-and-error discoveries after it |
| **onboarding** | Get started with this toolkit in a repo, or add it to one |
| **project-discovery** | Understand a project: structure, architecture, flows, how-tos, related projects |
| **design-driven-dev** | Investigation-first Socratic design process before coding |
| **pathfinder** | CoLD-based vertical slicing of design docs and implementation plans |
| **second-opinion** | Dual-model side-by-side sanity check of plans, designs, or code |
| **cli-creator** | Build durable command-line tools and companion skills from API docs, specs, or scripts |
| **run-retrospective** | End-of-run retrospective: run records, mistake signatures, promotion ladder (learning, checklist, guard, rule), and trend metrics via `run_retro.py` |
| **knowledge-base** | Search the toolkit knowledge base before reading source, run the intake gate, save to the pending inbox, set up and check the local vector KB via `scripts/kb.py` |
| **assistant-workspace-cleanup** | Inventory, classify, and safely clean up an AI-assistant workspace (chats, agent sessions, projects, scheduled tasks, artifacts, ledgers) behind a reversibility-grouped approval gate, ID allow-listed lanes, and live-state verification |
| **workspace-hygiene-auditor** | Read-only specialist that turns a workspace inventory into a classified cleanup plan (one action, confidence, and reason per item) and flags stale-state, coverage-gap, and run-duration risks |
| **repeat-work-discovery** | Scan mail, calendar, and files for repeated work, return a ranked top-5 list of proposed skills with trigger, time saved, and tool recommendations, and build the approved ones |
| **productivity-impact-estimate** | Estimate weekly, monthly, and yearly engineering time saved by the toolkit with a transparent, reproducible model, labelled as an estimate and not a measurement |

### Engineering Practices And Languages

| Skill | Purpose |
| --- | --- |
| **best-practices** | SOLID, clean code, layered architecture, resilience, anti-patterns |
| **js-ts-best-practices** | JavaScript/TypeScript patterns: async, type safety, DI, Node/TS toolchain choices |
| **python-best-practices** | Python patterns: typing, DI, concurrency, packaging, testing |
| **testing** | AC traceability, test pyramid, mocking, coverage, and test patterns |
| **run-tests** | Pick and run the smallest meaningful validation for a change set |
| **git-conventions** | Branch naming, semantic commits, PR lifecycle, rebase workflow, duplicate-file gate |
| **environment-diagnose** | Diagnose local environment, auth, Docker, cache, and setup issues |
| **local-env-bootstrap** | Bootstrap or repair a local development environment across repos |
| **web-form-submit-debugging** | Diagnose a web form whose Next or Submit button does nothing: read validation, capture network and console, instrument the page, rule out extensions, then pick a workaround or report a site defect |

### Review, Validation, And Quality Gates

| Skill | Purpose |
| --- | --- |
| **ticket-review** | In-agent diff review scoped to a ticket, PR, or branch (report only) |
| **pre-pr-check** | Full pre-PR gate: repo validations, changed-code quality gate, UI-verify check, in-agent review |
| **pr-validator** | Read-only PR/ticket readiness validation on the live head with approve-ready, blocked, or monitor reporting |
| **java-change-validator** | Read-only Java diff, test, framework wiring, migration, and build-evidence validation before merge or reply |
| **documentation-reviewer** | Read-only review of docs, runbooks, PR bodies, release notes, and generated surfaces for source-grounded accuracy |
| **ui-verify** | Verify front-end changes in a real browser through any configured browser MCP before declaring work done |

### CI, Releases, And Delivery

| Skill | Purpose |
| --- | --- |
| **jenkins-to-github-actions** | Migrate Jenkins pipelines to GitHub Actions safely |
| **maven-release** | Maven release: prepare, perform, Nexus deployment, downstream updates |
| **maven-build-troubleshooting** | Diagnose Maven build, OWASP dependency-check, Java runtime, and local webapp startup failures |

### Operations, Infrastructure, And Cloud

| Skill | Purpose |
| --- | --- |
| **runbook-authoring** | Structured operational runbooks for deploy, triage, rollback, and recurring operations |
| **incident-ops** | Incident triage, mitigation, communication, and observability-gap recovery |
| **log-analysis** | Read-only CloudWatch, server, access, Log4j, Lambda, Glue, and Firehose log investigation with redaction |
| **aws-alarm-investigator** | Read-only CloudWatch alarm root-cause investigation with confidence-rated hypotheses and email-ready fixes |
| **terraform-change-safety** | Terraform change-safety patterns: `terraform_data` lifecycle, module variable wiring, alarm first-datapoint planning, alias-qualified permissions |
| **folder-reorganization** | Reorganize a folder tree (renames, moves, archive) without breaking automations, scripts, documents, or cloud-sync links: approval-first proposal, path map, resumable scripted run with rollback, verification against live consumers |
| **aws-airflow-terraform-project** | Repository-specific AWS Airflow Terraform guidance for the data-science project (toolkit-local context) |

### Security

| Skill | Purpose |
| --- | --- |
| **security-best-practices** | Language- and framework-specific secure-by-default reviews |
| **security-ownership-map** | Git-based security ownership topology, bus factor, and sensitive-code ownership |

### Documentation, Diagrams, And Wiki

| Skill | Purpose |
| --- | --- |
| **doc-delta** | Suggest or apply documentation updates from staged changes |
| **update-docs** | Keep docs aligned with code changes |
| **document-conversion** | Convert between PDF, DOCX, PPTX, XLSX, and Markdown (thesis exports, reports) |
| **diagram-authoring** | Create, validate, and export deterministic high-resolution C4, AWS, sequence, and flow diagrams with mandatory image QA |
| **diagram-creation-specialist** | Read-only source-grounded diagram planning, notation, export, and image-quality validation |
| **system-architecture-specialist** | Read-only application architecture, boundary, data-flow, integration, and quality-attribute review |
| **confluence-documentation** | Safe Confluence CRUD, hierarchy, labels, comments, attachments, and rollback-state backups |
| **prod-doc-promoter** | Read-only promotion planning for deployed-ticket documentation from a wiki intake folder to canonical homes |
| **markdown-pdf-export** | Generate and verify ticket-ready PDFs from Markdown (HTML+Chrome for tables, Kroki+Pandoc for diagrams) |
| **technical-content-publishing** | Turn a software project into evidence-grounded Medium-style article, LinkedIn post and carousel, cover image, and architecture diagram as reviewed drafts, never posted |
| **current-events-briefing** | Brief the user on a live or just-finished public event with symmetric coverage, independent analysis, fact-checker findings, same-pollster comparisons, and an honest "no consolidated verdict yet" |

### Data Science, Notebooks, And Pipelines

| Skill | Purpose |
| --- | --- |
| **jupyter-notebook** | Notebook hygiene: kernel state, cell order, outputs, review, promotion to scripts |

### Career And Job Search

| Skill | Purpose |
| --- | --- |
| **job-search-pipeline** | Profile-driven job scan: board discovery and hard-rule screening, owner-approved applications, inbox/board status reconciliation, guarded xlsx tracker updates, skill-gap mapping, ranked digest |
| **credential-evaluation** | Decide whether a degree, MBA, master's, bootcamp, or certification is worth it for someone's career: who really awards it, legal recognition where it will be used, market signal, opportunity cost, and accredited alternatives. |
| **contract-platform-vetting** | Vet AI-training and expert-contractor marketplaces as bridge income: legitimacy check, rate selection inside the posted band, ranking by band and task fit, effective-hourly math, weekly-hour caps |
| **interview-prep-planner** | Build an interview-preparation plan: classify interview types, gap analysis against the profile, prioritized study plan with resources and drills, week-one triage, STAR prompts, and a resumable deliverable |
| **technical-interview-prep** | Coach a candidate through one technical interview: truthful cheat sheet, intro rehearsal, Java coding-pattern drills, full mock with end-of-session scoring, and a debrief that turns the asked problem into the next drill |

Skills marked toolkit-local in `skills/README.md` (AWS Airflow Terraform project) carry this toolkit's own data-science/thesis context; other consumers can ignore them.

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

`security-check-toolkit` runs every installed scanner (gitleaks, semgrep, shellcheck, PSScriptAnalyzer, yamllint, actionlint, hadolint, syft/grype/trivy, SkillSpector) plus the dependency-free LLM-surface prompt-injection scan; missing scanners are skipped with a reason. `npm run validate` runs the node validators (skill index, rules redirects, workflow sizes, subagent parity) and the Python unit tests. Also run the duplicate-file gate before push:

```bash
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files" && exit 1
```

If a validation failure reveals a reusable toolchain gotcha, capture it under `learnings/` (`workflows/capture-learning.md`) after user approval.

## After Completing Tasks

- If code changed, run the **changed-code-quality-gate** workflow before **ticket-review** or **pre-pr-check** can pass.
- Before adding any new skill, workflow, agent or rule, pass `workflows/resource-value-check.md` (mandatory; learnings are exempt).
- If rules, workflows, skills, or subagents changed, update the indexes (`README.md`, this file, `INTENTS.md`, the folder `README.md`) in the same change; consumer repos using links get updates automatically.
- Keep root `AGENTS.md`, `README.md`, and `INTENTS.md` as indexes, not playbooks (`skills/llm-context-engineering/SKILL.md`).
