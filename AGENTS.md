# LLM Toolkit Project - Agent Guidance

This repository is the shared source of truth for local LLM-assisted development assets: rules, workflows, skills, tool subagents, rubrics, learnings, setup scripts, and provider compatibility surfaces. It is generic and IDE-agnostic (Codex, Cursor, Claude Code, Windsurf, Copilot, Gemini CLI, OpenCode, Antigravity, generic agents). Consumer projects link to this toolkit or select from it; they must not copy private, project-specific, company-specific, or ticket-specific guidance back into the shared catalog.

---

## Core Principles

Apply these to every task.

### 1. Read Learnings First

- Read `learnings/INDEX.md` before non-trivial work and follow any relevant happy path (`rules/error-driven-learning.md`).

### 2. Think Before Coding

- State assumptions explicitly. If uncertain, ask. If multiple interpretations exist, present them; do not pick silently.

### 3. Simplicity First And Surgical Changes

- No features beyond what was asked; no abstractions for single-use code.
- Touch only what you must and match existing style. Every changed line traces to the request. For ticket work stay inside ticket scope; no adjacent refactors.

### 4. Goal-Driven Execution

- Define success criteria, state a brief plan for multi-step work, and verify after each step.

### 5. Verify Your Changes

- Always check work after you change it; never assert success from the edit alone. Run the narrowest meaningful verification (tests, linters, the script you touched, filesystem or API output).
- Generated or exported images require the `image-quality-inspection` gate before completion.
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
├── rules/                     # Always-on generic rules (+ rules/examples/ templates)
├── workflows/                 # Step-by-step procedures (<= 12,000 chars each)
├── skills/                    # On-demand capabilities (SKILL.md + references/rules/scripts/agents)
├── tool-subagents/            # Shared subagent prompts (.md + .toml), agent-orchestrator first
├── rubrics/                   # Architecture, security, and code-review checklists
├── integrations/              # Jira, Confluence, GitHub, Jenkins, AWS CLI, Slack CLI, AWS Agent Toolkit
├── clients/                   # Provider overlay guidance and sync commands
├── learnings/                 # Indexed trial-and-error discoveries (INDEX.md first)
├── docs/                      # tool-compatibility-paths, repo-setup-prompt, jira-setup, docs/llm/
├── scripts/                   # Setup, sync, validation, security gate, quality gate, PDF export
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
6. **Tasks tables record what actually ran.** The wave-ordered table (agent, task, tier, model/effort, validator, loop, ETA, status) shows the real model per task; a uniform expensive column means tiering was skipped.
7. **The root owns writes.** Specialists are read-only; the root performs edits, validation, commits, pushes, PR actions, and user communication. Explicit `LOA mode` (long-running autonomous orchestration) is opt-in only and keeps the parent as reconciliation/final checker with an `LLM-STATE.md` checkpoint.
8. **Notifications are configuration.** Mirroring the tasks table to a chat channel is opt-in per consumer (a configured route plus standing authorization) and never assumed.

---

## Intent Routing (Quick Index)

`INTENTS.md` is the canonical chat-request -> capability map. Route before loading details: a workflow for an end-to-end process, a skill for a specialized capability, rules as constraints that travel with the request. Choose one primary capability and attach only necessary helpers.

| User intent | Use |
| --- | --- |
| "Review my changes" / "review this PR" | **ticket-review** or **review** workflow |
| "Review and fix" / "fix my branch" | **ticket-review-and-fix** or **review-and-fix** workflow |
| "Pre-PR check" / "ready for PR" | **pre-pr-check** workflow + skill |
| "Quality gate" / "Sonar" / "Semgrep changed code" | **changed-code-quality-gate** workflow + skill |
| "Validate this PR" / "approve or block" | **pr-validator-validation** workflow + **pr-validator** skill |
| "Ticket is solved, drive the PR" | **ticket-pr-validation-loop** workflow |
| "Validate Java changes" | **java-change-validation** workflow + **java-change-validator** skill |
| "Commit and push" / "validate and push" | **commit-and-push** workflow (with **pre-pr-check** first) |
| "Fix CI" / "address PR comments" / "PR bot findings" | **gh-fix-ci**, **gh-address-comments**, **pr-automation-review** workflows |
| "Start ticket ABC-123" / "implement a ticket" | **task-starter** skill, **ticket-research** and **ticket-implementation** workflows |
| "Run tests" / "test plan" | **run-tests** workflow or **test-plan** skill |
| "Terraform" / ".tf change" / "plan/apply" / "state or import" (mandatory routing) | **terraform-specialist-validation** workflow + **terraform-specialist** skill, with **terraform-change-safety** |
| "Airflow DAG" / "Glue job" / "crawler" / "MWAA" | **dag-glue-specialist-validation** workflow + **dag-glue-specialist** skill |
| "Investigate this alarm" / "CloudWatch alarm RCA" | **aws-alarm-investigator-validation** workflow + **aws-alarm-investigator** skill |
| "Analyze logs" / "CloudWatch logs" / "nginx logs" | **log-investigation** workflow + **log-analysis** skill |
| "Incident" / "production issue" / "runbook" | **incident-ops**, **runbook-authoring** skills |
| "Update docs" / "review documentation" | **update-docs** workflow or **doc-delta** skill; **documentation-reviewer-validation** workflow |
| "Architecture docs" / "diagrams" / "C4" / "PlantUML" | **document-creation** workflow, **diagram-authoring** skill, **diagram-creation-specialist-validation**, **system-architecture-specialist-validation** |
| "Confluence" / "wiki page" / "promote deployed docs" | **confluence-documentation** workflow + skill; **confluence-documentation-specialist-validation**; **prod-doc-promoter-validation** |
| "Verify the UI" / "compare with Figma" / "check exported images" | **ui-verify**, **figma-compare**, **image-quality-inspection** skills |
| "Export Markdown to PDF" / "PowerPoint deck" | **markdown-pdf-export** workflow + skill; **pptx-generator** / **powerpoint-slides** skills |
| "Security review" / "OWASP audit" / "threat model" | **security-report** workflow, **security**, **owasp-security-review**, **security-threat-model** skills |
| "Cut a release" / "Maven release" / "E2E for release" | **release-manager**, **maven-release**, **e2e-release-verification** skills; **ticket-release** workflow |
| "Load test" / "JMeter" | **jmeter-performance-testing** skill |
| "Copy this record from prod to stage" | **cross-env-data-copy** skill |
| "Migrate Jenkins to GitHub Actions" / "CI parity" | **jenkins-to-github-actions**, **ci-migration-and-parity** skills |
| "Local env broken" / "set up my machine" | **environment-diagnose** workflow, **local-env-bootstrap** skill, `INFRA.sh` / `INFRA.ps1` |
| "Which plugins are installed" / "reproduce my assistant setup" | **llm-toolchain-provisioning** skill |
| "Split this across agents" / "which model per task" / "LOA mode" | **agent-orchestrator** skill, **model-selector** skill, **agent-orchestrator-validation** workflow |
| "Save tokens" / "compact command output" | **token-efficiency** skill |
| "Create a specialist agent" / "improve the specialist" | **specialist-agent-factory** / **specialist-agent-evolution** workflows + skill |
| "Compact this chat" / "mine chat history into assets" | **context-compaction** / **chat-knowledge-curation** workflows |
| "Save this as a learning" / "improve the toolkit" | **capture-learning**, **self-improvement**, **toolkit-maintenance** workflows; **llm-context-engineering** skill |
| "Import external skills" | **external-skill-intake** skill |
| "Java / Python / JavaScript / shell patterns" | **java-best-practices**, **python-best-practices**, **js-ts-best-practices**, **shell-scripting** skills |
| "RAG" / "agent memory" / "LLM app architecture" | **llm-application-architecture** skill |
| "Notebook analysis" / "ML experiment" / "data pipeline" | **notebook-analysis**, **ml-experiment**, **data-pipeline-change** workflows + skills |
| "Thesis" / "TCC" / "ABNT" / "USP MBA context" | **thesis-writing-main** workflow; **research-thesis-support**, **abnt-formatting**, **usp-mba-course-context** skills |
| "Brazilian public data" | **transparency-portal**, **ibge-datasets**, **municipal-compliance-analysis** skills |

---

## Rules

Always-loaded constraints (`rules/README.md` has the one-line scope of each):

- `rules/api-contract-surface.md`
- `rules/changed-code-quality-gate-required.md`
- `rules/ci-feedback-loop.md`
- `rules/cli-over-mcp.md`
- `rules/code-rules.md`
- `rules/command-safety.md`
- `rules/cross-platform-scripts.md`
- `rules/documentation-review-required.md`
- `rules/error-driven-learning.md`
- `rules/external-write-authorization.md`
- `rules/git-conventions.md`
- `rules/human-comment-reply-gate.md`
- `rules/log-analysis-safety.md`
- `rules/multi-agent-orchestration.md`
- `rules/operational-doc-required.md`
- `rules/release-safety.md`
- `rules/repository-context-layers.md`
- `rules/request-orchestration.md`
- `rules/security-check-required.md`
- `rules/workflow-authoring.md`

Consumer-specific rule templates live in `rules/examples/`.

---

## Workflows

`workflows/README.md` describes every workflow. Specialists ship as a `*-validation` (run it) plus `*-evolution` (improve it) pair.

- **Orchestration and toolkit evolution:** `workflows/task-quality-loop.md`, `workflows/agent-orchestrator-validation.md`, `workflows/agent-orchestrator-evolution.md`, `workflows/model-selector-validation.md`, `workflows/model-selector-evolution.md`, `workflows/specialist-agent-factory.md`, `workflows/specialist-agent-evolution.md`, `workflows/context-compaction.md`, `workflows/chat-knowledge-curation.md`, `workflows/automation-maintenance.md`, `workflows/capture-learning.md`, `workflows/self-improvement.md`, `workflows/toolkit-maintenance.md`
- **Core engineering:** `workflows/project-discovery.md`, `workflows/review.md`, `workflows/review-and-fix.md`, `workflows/ticket-review.md`, `workflows/ticket-review-and-fix.md`, `workflows/pre-pr-check.md`, `workflows/changed-code-quality-gate.md`, `workflows/run-tests.md`, `workflows/update-docs.md`, `workflows/commit-and-push.md`, `workflows/cross-repo-impact.md`, `workflows/new-backend-feature.md`, `workflows/environment-diagnose.md`, `workflows/dependency-upgrade.md`
- **Tickets, PRs, CI, releases:** `workflows/ticket-research.md`, `workflows/ticket-implementation.md`, `workflows/ticket-research-and-implementation.md`, `workflows/ticket-research-and-implementation-and-validation.md`, `workflows/ticket-pr-validation-loop.md`, `workflows/pr-validator-validation.md`, `workflows/pr-validator-evolution.md`, `workflows/java-change-validation.md`, `workflows/java-validator-evolution.md`, `workflows/gh-address-comments.md`, `workflows/gh-fix-ci.md`, `workflows/pr-automation-review.md`, `workflows/ticket-release.md`, `workflows/security-check-required.md`, `workflows/security-report.md`
- **Infrastructure, operations, logs:** `workflows/terraform-specialist-validation.md`, `workflows/terraform-specialist-evolution.md`, `workflows/terraform-manual-infrastructure-handoff.md`, `workflows/dag-glue-specialist-validation.md`, `workflows/dag-glue-specialist-evolution.md`, `workflows/aws-alarm-investigator-validation.md`, `workflows/aws-alarm-investigator-evolution.md`, `workflows/log-investigation.md`, `workflows/aws-airflow-terraform-change.md`, `workflows/aws-airflow-terraform-project.md`, `workflows/aws-data-pipeline-ops.md`, `workflows/aws-data-platform-ops.md`
- **Documentation, diagrams, wiki:** `workflows/document-creation.md`, `workflows/documentation-reviewer-validation.md`, `workflows/documentation-reviewer-evolution.md`, `workflows/diagram-creation-specialist-validation.md`, `workflows/diagram-creation-specialist-evolution.md`, `workflows/system-architecture-specialist-validation.md`, `workflows/system-architecture-specialist-evolution.md`, `workflows/confluence-documentation.md`, `workflows/confluence-documentation-specialist-validation.md`, `workflows/confluence-documentation-specialist-evolution.md`, `workflows/prod-doc-promoter-validation.md`, `workflows/prod-doc-promoter-evolution.md`, `workflows/markdown-pdf-export.md`, `workflows/documentation-sync-project.md`, `workflows/bilingual-doc-sync.md`, `workflows/paired-doc-sync.md`, `workflows/translation-sync.md`
- **Data science, thesis, notebooks, pipelines:** `workflows/project-execution-main.md`, `workflows/notebook-analysis.md`, `workflows/notebook-analysis-update.md`, `workflows/notebook-to-script.md`, `workflows/notebook-latex-polish.md`, `workflows/ml-experiment.md`, `workflows/ml-experiment-update.md`, `workflows/experiment-result-update.md`, `workflows/research-analysis-cycle.md`, `workflows/analysis-validation.md`, `workflows/thesis-writing-main.md`, `workflows/thesis-chapter-writing.md`, `workflows/thesis-submission-preparation.md`, `workflows/thesis-completion-guide.md`, `workflows/thesis-bibliography-integration.md`, `workflows/thesis-plagiarism-check.md`, `workflows/thesis-plagiarism-prevention.md`, `workflows/tcc-method-selection.md`, `workflows/tcc-analysis-and-writing-sync.md`, `workflows/tcc-formatting-abnt-review.md`, `workflows/refresh-usp-mba-course-context.md`, `workflows/course-material-grounding.md`, `workflows/data-source-ingestion.md`, `workflows/data-source-storage-backend.md`, `workflows/dataset-onboarding.md`, `workflows/data-pipeline-change.md`, `workflows/pipeline-change-project.md`, `workflows/bilingual-notebook-sync.md`

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
| **chat-knowledge-curation** | Mine chat history, memory notes, rollout summaries, automation runs, and learnings into durable toolkit assets |
| **llm-context-engineering** | Keep AGENTS/rules/workflows/skills lean, generic, provider-agnostic, and loaded on demand |
| **llm-application-architecture** | Design or evaluate RAG, agents, memory, tool use, gateways, evaluation, and rollout architecture for LLM applications |
| **llm-toolchain-provisioning** | Export, review, and restore installed LLM assistant extensions (plugins, marketplaces, MCP servers) as a portable manifest |
| **external-skill-intake** | Safely evaluate, download, adapt, scan, and index skills from public LLM-tool repositories |
| **error-driven-learning** | Always-on discipline: read `learnings/INDEX.md` before work and capture trial-and-error discoveries after it |
| **onboarding** | Get started with this toolkit in a repo, or add it to one |
| **project-discovery** | Understand a project: structure, architecture, flows, how-tos, related projects |
| **design-driven-dev** | Investigation-first Socratic design process before coding |
| **pathfinder** | CoLD-based vertical slicing of design docs and implementation plans |
| **second-opinion** | Dual-model side-by-side sanity check of plans, designs, or code |
| **cli-creator** | Build durable command-line tools and companion skills from API docs, specs, or scripts |

### Engineering Practices And Languages

| Skill | Purpose |
| --- | --- |
| **best-practices** | SOLID, clean code, layered architecture, resilience, anti-patterns |
| **java-best-practices** | Java patterns: DI, concurrency, logging, metrics wiring, testing, modern JDK/Spring choices |
| **js-ts-best-practices** | JavaScript/TypeScript patterns: async, type safety, DI, Node/TS toolchain choices |
| **python-best-practices** | Python patterns: typing, DI, concurrency, packaging, testing |
| **shell-scripting** | Bash, POSIX sh, and PowerShell best practices: strict mode, error handling, portability, UTF-8 without BOM |
| **testing** | AC traceability, test pyramid, mocking, coverage, and test patterns |
| **test-plan** | Generate a test plan from a staged diff or branch |
| **run-tests** | Pick and run the smallest meaningful validation for a change set |
| **git-conventions** | Branch naming, semantic commits, PR lifecycle, rebase workflow, duplicate-file gate |
| **environment-diagnose** | Diagnose local environment, auth, Docker, cache, and setup issues |
| **local-env-bootstrap** | Bootstrap or repair a local development environment across repos |

### Review, Validation, And Quality Gates

| Skill | Purpose |
| --- | --- |
| **code-review** | Structured code review for bugs, correctness, security, and test coverage |
| **review** | In-agent diff review of staged changes or current branch (report only) |
| **ticket-review** | In-agent diff review scoped to a ticket, PR, or branch (report only) |
| **review-and-fix** | Review, split investigation and fixes across subagents, apply scoped fixes, converge on a verified result |
| **fix** | Apply fixes from a prior review report (`docs/jira/<TICKET>/review-report.json`) |
| **pre-pr-check** | Full pre-PR gate: repo validations, changed-code quality gate, UI-verify check, in-agent review |
| **changed-code-quality-gate** | Mandatory static-analysis gate limited to code added or modified in the current Git change set |
| **pr-validator** | Read-only PR/ticket readiness validation on the live head with approve-ready, blocked, or monitor reporting |
| **java-change-validator** | Read-only Java diff, test, framework wiring, migration, and build-evidence validation before merge or reply |
| **documentation-reviewer** | Read-only review of docs, runbooks, PR bodies, release notes, and generated surfaces for source-grounded accuracy |
| **ui-verify** | Verify front-end changes in a real browser through any configured browser MCP before declaring work done |
| **figma-compare** | Compare implemented UI against a Figma frame and report severity-ranked mismatches |
| **image-quality-inspection** | Blocking quality gate and fix-and-rerender loop for every generated or exported image |
| **task-starter** | Turn a ticket or task description into a scoped implementation plan |
| **ticket-research** | Research a ticket across code, docs, Jira, Confluence, and GitHub context |

### CI, Releases, And Delivery

| Skill | Purpose |
| --- | --- |
| **ci-watcher** | Background CI monitoring after push with failure triage |
| **ci-migration-and-parity** | Keep parity while moving or comparing CI pipelines across systems |
| **jenkins-to-github-actions** | Migrate Jenkins pipelines to GitHub Actions safely |
| **cross-repo-impact** | Map downstream impact of a shared change across sibling repos |
| **e2e-release-verification** | Pick and run the smallest relevant E2E or regression verification for a release |
| **release-manager** | Cut, verify, and manage releases with rollout and rollback planning |
| **maven-release** | Maven release: prepare, perform, Nexus deployment, downstream updates |
| **maven-build-troubleshooting** | Diagnose Maven build, OWASP dependency-check, Java runtime, and local webapp startup failures |
| **jmeter-performance-testing** | Plan, run, analyze, and report Apache JMeter load and performance tests against any HTTP service |
| **cross-env-data-copy** | Copy a single record between environments with read-only fetch, MERGE preview, and human confirmation before any write |
| **zoom-meeting-sdk** | Secure defaults for embedding Zoom meetings (server-side SDK JWT signatures, credentials, web embed rules) |

### Operations, Infrastructure, And Cloud

| Skill | Purpose |
| --- | --- |
| **runbook-authoring** | Structured operational runbooks for deploy, triage, rollback, and recurring operations |
| **incident-ops** | Incident triage, mitigation, communication, and observability-gap recovery |
| **log-analysis** | Read-only CloudWatch, server, access, Log4j, Lambda, Glue, and Firehose log investigation with redaction |
| **aws-alarm-investigator** | Read-only CloudWatch alarm root-cause investigation with confidence-rated hypotheses and email-ready fixes |
| **dag-glue-specialist** | Read-only Airflow DAG, MWAA/Astro, AWS Glue job, crawler, Data Catalog, and ETL pipeline validation |
| **terraform** | Terraform/OpenTofu modules, tests, CI/CD, and security/compliance patterns |
| **terraform-specialist** | Read-only Terraform specialist: module/root review, plan safety, state and import lifecycle, multi-env roots, drift codification |
| **terraform-change-safety** | Terraform change-safety patterns: `terraform_data` lifecycle, module variable wiring, alarm first-datapoint planning, alias-qualified permissions |
| **infra-adoption** | Adopt or import existing infrastructure into managed IaC |
| **aws-airflow-terraform-project** | Repository-specific AWS Airflow Terraform guidance for the data-science project (toolkit-local context) |

### Security

| Skill | Purpose |
| --- | --- |
| **security** | Injection prevention, auth, secrets, XSS/CSRF/SSRF, PII, threat modeling |
| **security-best-practices** | Language- and framework-specific secure-by-default reviews |
| **security-threat-model** | Repository-grounded threat modeling with trust boundaries, abuse paths, and mitigations |
| **security-ownership-map** | Git-based security ownership topology, bus factor, and sensitive-code ownership |
| **owasp-security-review** | OWASP-style application security audit for Java, JS/TS, Python, and React projects |
| **security-checkpoint** | Repository-specific minimum security gate for the data-science thesis repository (toolkit-local context) |

### Documentation, Diagrams, And Wiki

| Skill | Purpose |
| --- | --- |
| **doc-delta** | Suggest or apply documentation updates from staged changes |
| **update-docs** | Keep docs aligned with code changes |
| **document-creation** | Create or update architecture docs, diagrams, and wiki pages |
| **document-conversion** | Convert between PDF, DOCX, PPTX, XLSX, and Markdown (thesis exports, reports) |
| **documentation-governance** | Repository-specific documentation and governance constraints for the data-science thesis repository (toolkit-local context) |
| **diagram-authoring** | Create, validate, and export deterministic high-resolution C4, AWS, sequence, and flow diagrams with mandatory image QA |
| **diagram-creation-specialist** | Read-only source-grounded diagram planning, notation, export, and image-quality validation |
| **system-architecture-specialist** | Read-only application architecture, boundary, data-flow, integration, and quality-attribute review |
| **confluence-documentation** | Safe Confluence CRUD, hierarchy, labels, comments, attachments, and rollback-state backups |
| **confluence-documentation-specialist** | Read-only Confluence page, hierarchy, attachment, comment, rendered-page, and source-to-wiki validation |
| **prod-doc-promoter** | Read-only promotion planning for deployed-ticket documentation from a wiki intake folder to canonical homes |
| **markdown-pdf-export** | Generate and verify ticket-ready PDFs from Markdown (HTML+Chrome for tables, Kroki+Pandoc for diagrams) |
| **pptx-generator** | Generate, edit, and read PowerPoint decks with PptxGenJS |
| **powerpoint-slides** | Visually rich academic and thesis-defense PowerPoint decks |

### Data Science, Notebooks, And Pipelines

| Skill | Purpose |
| --- | --- |
| **jupyter-notebook** | Notebook hygiene: kernel state, cell order, outputs, review, promotion to scripts |
| **latex-notebooks** | LaTeX math inside notebooks and technical docs |
| **notebook-analysis** | EDA, statistical analysis, plots, notebook cleanup, and narrative reporting with reproducibility |
| **ml-engineering** | Feature engineering, model training, evaluation, and experiment reporting in end-to-end projects |
| **ml-experiment** | Run or update ML experiments with baselines, leakage checks, and reproducible evaluation |
| **data-pipeline** | Ingestion, transformation, schema, storage, and backfill changes across Bronze/Silver/Gold layers |
| **data-pipeline-boundaries** | Repository-specific data pipeline boundaries for the data-science project (toolkit-local context) |
| **data-governance** | Dataset provenance, privacy, licensing, and evidence integrity in analytics projects |
| **ibge-datasets** | Brazilian IBGE public datasets: municipality codes, population, census |
| **transparency-portal** | Brazilian Portal da Transparencia (CGU) API: federal transfers, sanctions, pagination |
| **municipal-compliance-analysis** | Federal transfer spending vs municipal compliance outcomes analysis (thesis domain) |

### Thesis And Course Context (toolkit-local)

| Skill | Purpose |
| --- | --- |
| **research-thesis-support** | Evidence-heavy research, capstone, and thesis work in data-science repositories |
| **usp-mba-course-context** | USP MBA thesis/TCC context: methodology, chapter structure, advisor feedback |
| **course-material-grounding** | Ground tasks in the local MBA course corpus |
| **tcc-deliverables** | Thesis-facing evidence, figures, tables, and methodology deliverables |
| **tcc-defense-prep** | TCC defense preparation: deck structure, examiner questions, timing |
| **thesis-bibliography** | ABNT-format academic references that justify thesis decisions and methods |
| **abnt-formatting** | ABNT academic formatting for TCC thesis documents |
| **project-overview** | Project overview and context for the data-science thesis repository (toolkit-local context) |

Skills marked toolkit-local in `skills/README.md` (project overview, documentation governance, security checkpoint, data pipeline boundaries, AWS Airflow Terraform project, thesis and course context) carry this toolkit's own data-science/thesis context; other consumers can ignore them.

---

## Tool Subagents

`tool-subagents/README.md` is the canonical catalog (25 agents) and delegation contract. Coordinator and judges: `agent-orchestrator`, `model-selector`, `task-quality-judge`, `verifier`. Read-only specialists: `pr-validator`, `java-change-validator`, `documentation-reviewer`, `documentation-sync`, `confluence-documentation-specialist`, `diagram-creation-specialist`, `system-architecture-specialist`, `prod-doc-promoter`, `terraform-specialist`, `dag-glue-specialist`, `aws-alarm-investigator`, `log-analyst`, `code-reviewer`, `contract-analyzer`, `cross-repo-analyst`, `parallel-explorer`, `test-runner`, `ci-triage`, `security-auditor`, `owasp-security-auditor`, `release-coordinator`. Each has a `.md` (Cursor/Claude) and a `.toml` (Codex) with identical bodies; `npm run subagents:apply -- all .` renders the provider mirrors.

## Integrations

`integrations/README.md` indexes the Jira, Confluence, GitHub, Jenkins, AWS CLI, Slack CLI, and AWS Agent Toolkit guides. Each covers CLI, MCP, and manual options; `rules/cli-over-mcp.md` decides between them.

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

- If code changed, run **changed-code-quality-gate** before **ticket-review** or **pre-pr-check** can pass.
- If rules, workflows, skills, or subagents changed, update the indexes (`README.md`, this file, `INTENTS.md`, the folder `README.md`) in the same change; consumer repos using links get updates automatically.
- Keep root `AGENTS.md`, `README.md`, and `INTENTS.md` as indexes, not playbooks (`skills/llm-context-engineering/SKILL.md`).
