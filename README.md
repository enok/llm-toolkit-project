# LLM Toolkit for Data Science Projects

A generic, IDE-agnostic toolkit for LLM-assisted development: always-on **rules**, step-by-step **workflows**, on-demand **skills**, reusable **tool subagents**, review **rubrics**, integration guides, captured **learnings**, and cross-platform setup/validation **scripts**. It works with Codex, Cursor, Claude Code, Windsurf, GitHub Copilot, Gemini CLI, OpenCode, Antigravity, and generic agents.

The toolkit is the single source of truth. Consumer projects link to it (symlinks or junctions) plus a few generated pointer files; they never copy canonical content. Keep generic guidance here and repository-specific details in the consumer's own `AGENTS.md` and `docs/llm/`. A small set of assets is scoped to this toolkit's own data-science/thesis context and is labelled as such.

## What Is Included

| Area | Path | Purpose |
| --- | --- | --- |
| Rules | `rules/` | 20 short always-on constraints: code, git, security gates, request orchestration, model selection, human-reply gate, external-write authorization, CLI-over-MCP, cross-platform scripts, workflow authoring |
| Workflows | `workflows/` | 99 sequenced procedures: review and fix loops, PR/ticket validation, releases, specialist validation/evolution pairs, docs and diagrams, infrastructure and log investigation, data-science and thesis work |
| Skills | `skills/` | 102 on-demand capabilities with progressive disclosure (`SKILL.md` + `references/`, `rules/`, `scripts/`, `agents/`) |
| Tool subagents | `tool-subagents/` | 25 shared subagent prompts (`.md` + `.toml`) rendered into `.cursor/agents`, `.claude/agents`, and `.codex/agents`, led by `agent-orchestrator` |
| Rubrics | `rubrics/` | Architecture, security, and holistic code-review checklists with the `review-report.json` contract |
| Integrations | `integrations/` | Jira, Confluence, GitHub, Jenkins, AWS CLI, Slack CLI, AWS Agent Toolkit setup guides |
| Clients | `clients/` | Provider overlay guidance and client sync commands |
| Learnings | `learnings/` | 45 indexed trial-and-error discoveries (AWS, Terraform, Confluence, git/Windows/shell, agent behavior, notebooks) |
| Scripts | `scripts/` | Setup, link repair, sync, machine bootstrap, security gate, index validation, changed-code quality gate, LLM-surface scan, PDF export |
| Tests and CI | `tests/`, `.github/workflows/` | Unit tests for the validators and GitHub Actions that run the full gate on `main` |
| Docs | `docs/` | Provider path map, repo setup prompt, Jira setup |

## Architecture

Canonical content lives in one place; provider directories are thin compatibility surfaces:

```text
rules/             broad always-relevant guidance (always loaded)
workflows/         manually invoked procedures (<= 12,000 characters each)
skills/            on-demand capabilities
tool-subagents/    reusable subagent prompts (.md + .toml)
rubrics/           review scoring and checklists
learnings/         indexed gotchas (read learnings/INDEX.md first)

.agents/skills .claude/skills .codex/skills .cursor/skills .windsurf/skills   -> skills/
.agent/skills .gemini/skills .opencode/skills                                 -> skills/
.windsurf/rules .cursor/rules                                                 -> rules/
.windsurf/workflows .cursor/workflows                                         -> workflows/
.cursor/agents .claude/agents .codex/agents                                   -> tool-subagents/ (rendered)
```

`docs/tool-compatibility-paths.md` is the single path map. Repair links and refresh generated surfaces from the toolkit root with:

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md --skip-github
```

```powershell
.\scripts\sync-tool-configs.ps1 . -SkipAgentsMd -SkipGithub
```

### How agents use it

1. **Rules** travel with every request (`rules/request-orchestration.md` routes non-trivial work; `rules/security-check-required.md`, `rules/human-comment-reply-gate.md`, and `rules/external-write-authorization.md` gate side effects).
2. **`agent-orchestrator`** (`tool-subagents/agent-orchestrator.md`) splits multi-lane work into a wave-ordered task table, assigns each task a complexity tier and concrete model through `model-selector`, runs every delegated task as a bounded produce-validate-refine loop (`workflows/task-quality-loop.md`, max 5 iterations), keeps a durable state ledger (`CONTEXT_STATE.md` + `TASKS_TABLE.md`), and enforces a 30-minute SLA per task.
3. **Read-only specialists** (`pr-validator`, `java-change-validator`, `documentation-reviewer`, `terraform-specialist`, `dag-glue-specialist`, `aws-alarm-investigator`, `log-analyst`, `system-architecture-specialist`, `diagram-creation-specialist`, `confluence-documentation-specialist`, `prod-doc-promoter`, `task-quality-judge`, `verifier`, ...) return evidence, findings, and draft replies; the root agent owns edits, commits, pushes, and human-facing replies.
4. Each specialist ships as a **skill** entrypoint plus a **validation** workflow and an **evolution** workflow; `workflows/specialist-agent-factory.md` creates new ones.

## Quick Start

### First time on a machine

```bash
./INFRA.sh              # plan only: git, node, python, jq, ripgrep, gh, aws, mvn, ast-grep, repomix, agent CLIs
./INFRA.sh --apply      # install the full profile
```

Windows PowerShell: `.\INFRA.ps1` plans, `.\INFRA.ps1 -Apply` installs. Both wrap `scripts/bootstrap-dev.sh|.ps1`, are idempotent, print installed/missing tools, and leave every authentication step (`gh auth login`, `aws configure sso`, Atlassian CLI) interactive.

### Use the toolkit in every session (user-level install)

To make this toolkit the default source of skills, subagents, rules, and workflows for every LLM tool on the machine, in every project, install it at the user level:

```bash
./scripts/install-global-surfaces.sh            # plan: shows what would be linked/written
./scripts/install-global-surfaces.sh --apply    # links ~/.claude, ~/.codex, ~/.cursor, ~/.codeium/windsurf, ~/.gemini, ... to this toolkit
```

```powershell
.\scripts\install-global-surfaces.ps1 -Apply
```

It links each tool's home-directory skill and agent paths to `skills/` and `tool-subagents/`, and writes a managed block into each tool's global instruction file (`~/.claude/CLAUDE.md`, `~/.codex/AGENTS.md`, `~/.gemini/GEMINI.md`, Windsurf `global_rules.md`) that routes every non-trivial prompt through `rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md`. Re-run after `git pull`; see `docs/global-install.md` for the per-tool table, the Cursor manual step, and uninstall.

### Use in another repo

Clone this toolkit next to a consumer project, then run the setup script from the consumer repo:

```bash
../llm-toolkit-project/scripts/setup-repo.sh .
```

```powershell
..\llm-toolkit-project\scripts\setup-repo.ps1 .
```

The setup scripts create or repair toolkit links for every supported provider, scaffold `docs/llm/` (README, `toolkit-selection.txt`, rules and workflows folders), generate local `scripts/sync-llm-configs.*` wrappers, `.cursorignore`/`.cursorindexingignore`, a `CLAUDE.md` pointer, Copilot instructions, and the managed `AGENTS.md` toolkit block, and update `.gitignore`. Windows directory links need Developer Mode or an elevated shell (`setup-repo.cmd` requires an Administrator prompt). If scripted setup is blocked, use `docs/repo-setup-prompt.md` as an LLM-guided repair prompt.

After setup, hand this prompt to the agent inside the consumer repo:

> I just ran `setup-repo` from our shared LLM toolkit. Walk me through the configuration steps in AGENTS.md, help me curate `docs/llm/toolkit-selection.txt`, and add repo-local context under `docs/llm/`.

### Selecting context

Consumer repos curate shared context in `docs/llm/toolkit-selection.txt`:

```text
rules/code-rules.md
rules/security-check-required.md
rules/request-orchestration.md
workflows/pre-pr-check.md
workflows/run-tests.md
```

Then refresh generated exports from the consumer repo with `scripts/sync-llm-configs.sh` (Bash) or `scripts\sync-llm-configs.ps1` (PowerShell). Refresh links after toolkit updates with `../llm-toolkit-project/scripts/ensure-symlinks.sh . --pull` (add `--force` to replace blocking local paths).

## Rules

| Rule | File | Scope |
| --- | --- | --- |
| **API Contract Surface** | `rules/api-contract-surface.md` | Contract changes must identify downstream consumers, gateways, and generated artifacts |
| **Changed-Code Quality Gate Required** | `rules/changed-code-quality-gate-required.md` | Blocking static-analysis gate scoped to added or modified lines |
| **CI Feedback Loop** | `rules/ci-feedback-loop.md` | Turn CI failures into rule and workflow updates |
| **CLI over MCP** | `rules/cli-over-mcp.md` | Prefer capable authenticated CLIs; record why MCP was chosen when it is |
| **Code Rules** | `rules/code-rules.md` | Coding discipline, source verification, change management |
| **Command Safety** | `rules/command-safety.md` | Review shell commands for destructive, exfiltration, or injection risk |
| **Cross-Platform Scripts** | `rules/cross-platform-scripts.md` | Scripts must run on Windows, Linux, and macOS |
| **Documentation Review Required** | `rules/documentation-review-required.md` | Route created or changed documentation through `documentation-reviewer` |
| **Error-Driven Learning** | `rules/error-driven-learning.md` | Capture trial-and-error wins as indexed learnings |
| **External Write Authorization** | `rules/external-write-authorization.md` | Bind every external mutation (tickets, PRs, wiki, chat, email) to an explicit instruction |
| **Git Conventions** | `rules/git-conventions.md` | Branch naming, protected-branch etiquette, semantic commits, rebase, duplicate-file gate |
| **Human Comment Reply Gate** | `rules/human-comment-reply-gate.md` | Draft-and-approve gate for human-facing replies |
| **Log Analysis Safety** | `rules/log-analysis-safety.md` | Read-only, bounded, redacted log analysis |
| **Multi-Agent Orchestration** | `rules/multi-agent-orchestration.md` | Parallel fanout, tier and validator handoff, when to serialize |
| **Operational Doc Required** | `rules/operational-doc-required.md` | Recurring operations become runbooks; metric catalogs and wiki backup gates |
| **Release Safety** | `rules/release-safety.md` | Deploy order, verification, rollback, completion evidence |
| **Repository Context Layers** | `rules/repository-context-layers.md` | How toolkit rules merge with repo-local `AGENTS.md` and provider pointers |
| **Request Orchestration** | `rules/request-orchestration.md` | Routing into specialists, model-selection contract, quality loops, safety boundaries |
| **Security Check Required** | `rules/security-check-required.md` | Mandatory security gate incl. LLM-surface prompt-injection scan and skill scanners |
| **Workflow Authoring** | `rules/workflow-authoring.md` | 12K size limit, splits, single responsibility, composition |

Templates for consumer-specific rules live in `rules/examples/`.

## Workflows

See `workflows/README.md` for the categorized catalog of all 99 workflows. Highlights:

| Workflow | Use when |
| --- | --- |
| `workflows/task-quality-loop.md` | Every delegated task: produce, validate with a read-only validator, refine (max 5 iterations) |
| `workflows/pre-pr-check.md`, `workflows/changed-code-quality-gate.md`, `workflows/commit-and-push.md` | Validation gate, changed-code static analysis, semantic commit regrouping and safe push |
| `workflows/ticket-review.md`, `workflows/ticket-review-and-fix.md`, `workflows/review.md`, `workflows/review-and-fix.md` | Review-only or review-fix-test-push loops |
| `workflows/ticket-research.md` ... `workflows/ticket-pr-validation-loop.md` | Research, implement, validate, and drive a ticket's PR to approval |
| `workflows/pr-validator-validation.md`, `workflows/java-change-validation.md`, `workflows/documentation-reviewer-validation.md` | Read-only specialist validation passes |
| `workflows/terraform-specialist-validation.md`, `workflows/dag-glue-specialist-validation.md`, `workflows/aws-alarm-investigator-validation.md`, `workflows/log-investigation.md` | Infrastructure, pipeline, alarm, and log investigations |
| `workflows/document-creation.md`, `workflows/diagram-creation-specialist-validation.md`, `workflows/confluence-documentation.md`, `workflows/markdown-pdf-export.md` | Docs, diagrams, wiki, and PDF export |
| `workflows/specialist-agent-factory.md`, `workflows/specialist-agent-evolution.md`, `workflows/toolkit-maintenance.md`, `workflows/chat-knowledge-curation.md`, `workflows/context-compaction.md` | Growing and maintaining the toolkit itself |
| `workflows/thesis-writing-main.md`, `workflows/notebook-analysis.md`, `workflows/data-pipeline-change.md`, `workflows/ml-experiment.md` | Data-science and thesis work |

All workflows by area:

- **Orchestration and toolkit evolution:** `workflows/task-quality-loop.md`, `workflows/agent-orchestrator-validation.md`, `workflows/agent-orchestrator-evolution.md`, `workflows/model-selector-validation.md`, `workflows/model-selector-evolution.md`, `workflows/specialist-agent-factory.md`, `workflows/specialist-agent-evolution.md`, `workflows/context-compaction.md`, `workflows/chat-knowledge-curation.md`, `workflows/automation-maintenance.md`, `workflows/capture-learning.md`, `workflows/self-improvement.md`, `workflows/toolkit-maintenance.md`
- **Core engineering:** `workflows/project-discovery.md`, `workflows/review.md`, `workflows/review-and-fix.md`, `workflows/ticket-review.md`, `workflows/ticket-review-and-fix.md`, `workflows/pre-pr-check.md`, `workflows/changed-code-quality-gate.md`, `workflows/run-tests.md`, `workflows/update-docs.md`, `workflows/commit-and-push.md`, `workflows/cross-repo-impact.md`, `workflows/new-backend-feature.md`, `workflows/environment-diagnose.md`, `workflows/dependency-upgrade.md`
- **Tickets, PRs, CI, releases:** `workflows/ticket-research.md`, `workflows/ticket-implementation.md`, `workflows/ticket-research-and-implementation.md`, `workflows/ticket-research-and-implementation-and-validation.md`, `workflows/ticket-pr-validation-loop.md`, `workflows/pr-validator-validation.md`, `workflows/pr-validator-evolution.md`, `workflows/java-change-validation.md`, `workflows/java-validator-evolution.md`, `workflows/gh-address-comments.md`, `workflows/gh-fix-ci.md`, `workflows/pr-automation-review.md`, `workflows/ticket-release.md`, `workflows/security-check-required.md`, `workflows/security-report.md`
- **Infrastructure, operations, logs:** `workflows/terraform-specialist-validation.md`, `workflows/terraform-specialist-evolution.md`, `workflows/terraform-manual-infrastructure-handoff.md`, `workflows/dag-glue-specialist-validation.md`, `workflows/dag-glue-specialist-evolution.md`, `workflows/aws-alarm-investigator-validation.md`, `workflows/aws-alarm-investigator-evolution.md`, `workflows/log-investigation.md`, `workflows/aws-airflow-terraform-change.md`, `workflows/aws-airflow-terraform-project.md`, `workflows/aws-data-pipeline-ops.md`, `workflows/aws-data-platform-ops.md`
- **Documentation, diagrams, wiki:** `workflows/document-creation.md`, `workflows/documentation-reviewer-validation.md`, `workflows/documentation-reviewer-evolution.md`, `workflows/diagram-creation-specialist-validation.md`, `workflows/diagram-creation-specialist-evolution.md`, `workflows/system-architecture-specialist-validation.md`, `workflows/system-architecture-specialist-evolution.md`, `workflows/confluence-documentation.md`, `workflows/confluence-documentation-specialist-validation.md`, `workflows/confluence-documentation-specialist-evolution.md`, `workflows/prod-doc-promoter-validation.md`, `workflows/prod-doc-promoter-evolution.md`, `workflows/markdown-pdf-export.md`, `workflows/documentation-sync-project.md`, `workflows/bilingual-doc-sync.md`, `workflows/paired-doc-sync.md`, `workflows/translation-sync.md`
- **Data science, thesis, notebooks, pipelines:** `workflows/project-execution-main.md`, `workflows/notebook-analysis.md`, `workflows/notebook-analysis-update.md`, `workflows/notebook-to-script.md`, `workflows/notebook-latex-polish.md`, `workflows/ml-experiment.md`, `workflows/ml-experiment-update.md`, `workflows/experiment-result-update.md`, `workflows/research-analysis-cycle.md`, `workflows/analysis-validation.md`, `workflows/thesis-writing-main.md`, `workflows/thesis-chapter-writing.md`, `workflows/thesis-submission-preparation.md`, `workflows/thesis-completion-guide.md`, `workflows/thesis-bibliography-integration.md`, `workflows/thesis-plagiarism-check.md`, `workflows/thesis-plagiarism-prevention.md`, `workflows/tcc-method-selection.md`, `workflows/tcc-analysis-and-writing-sync.md`, `workflows/tcc-formatting-abnt-review.md`, `workflows/refresh-usp-mba-course-context.md`, `workflows/course-material-grounding.md`, `workflows/data-source-ingestion.md`, `workflows/data-source-storage-backend.md`, `workflows/dataset-onboarding.md`, `workflows/data-pipeline-change.md`, `workflows/pipeline-change-project.md`, `workflows/bilingual-notebook-sync.md`

## Skills at a Glance

Full catalog with conventions: `skills/README.md`. Invoke by intent (`INTENTS.md`) or name.

#### Orchestration And Context Engineering

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

#### Engineering Practices And Languages

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

#### Review, Validation, And Quality Gates

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

#### CI, Releases, And Delivery

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

#### Operations, Infrastructure, And Cloud

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

#### Security

| Skill | Purpose |
| --- | --- |
| **security** | Injection prevention, auth, secrets, XSS/CSRF/SSRF, PII, threat modeling |
| **security-best-practices** | Language- and framework-specific secure-by-default reviews |
| **security-threat-model** | Repository-grounded threat modeling with trust boundaries, abuse paths, and mitigations |
| **security-ownership-map** | Git-based security ownership topology, bus factor, and sensitive-code ownership |
| **owasp-security-review** | OWASP-style application security audit for Java, JS/TS, Python, and React projects |
| **security-checkpoint** | Repository-specific minimum security gate for the data-science thesis repository (toolkit-local context) |

#### Documentation, Diagrams, And Wiki

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

#### Data Science, Notebooks, And Pipelines

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

#### Thesis And Course Context (toolkit-local)

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

---

## Tool Subagents

`tool-subagents/README.md` lists all 25 shared subagents and the delegation contract (objective, scope, constraints, allowed tools, write ownership, acceptance criteria, validator, loop budget, complexity tier). `agent-orchestrator` is the default coordinator; `model-selector` assigns tiers; `task-quality-judge` and `verifier` judge results; the read-only specialists cover PRs, Java, docs, wiki, diagrams, architecture, Terraform, DAG/Glue, alarms, logs, contracts, security, CI, tests, releases, and cross-repo impact.

## Integrations

| Integration | File | Purpose |
| --- | --- | --- |
| **Jira** | `integrations/jira.md` | Ticket details, search, issue management (CLI + MCP); getting-started walkthrough in `docs/jira-setup.md` |
| **Confluence** | `integrations/confluence.md` | Documentation, wikis, architecture pages (CLI + MCP) |
| **GitHub** | `integrations/github.md` | Code, PRs, branches, CI status (CLI + MCP) |
| **Jenkins** | `integrations/jenkins.md` | Job/build status, console logs, triggering builds, pipeline authoring |
| **AWS CLI** | `integrations/aws-cli.md` | Cloud infrastructure, deployment, logs |
| **Slack CLI** | `integrations/slack-cli.md` | Slack application development with pinned installation |
| **AWS Agent Toolkit** | `integrations/aws-agent-toolkit.md` | Upstream AWS Agent Toolkit setup review and side effects (documentation only) |

## Validation

Before committing toolkit changes, run the gate (Bash / Git Bash):

```bash
./scripts/validate-toolkit-indexes.sh          # indexes, frontmatter, path references, workflow sizes, genericity
./scripts/security-check-toolkit.sh            # secrets, static analysis, LLM-surface scan, skill scanners, lint
./scripts/validate-skills-with-skillspector.sh --changed
npm run validate                               # node validators (skills index, rules redirects, sizes, subagents) + python tests
```

PowerShell:

```powershell
.\scripts\validate-toolkit-indexes.ps1
.\scripts\security-check-toolkit.ps1
.\scripts\validate-skills-with-skillspector.ps1
npm run validate
```

The gate checks skill frontmatter, referenced paths, the 12,000-character workflow limit, subagent `.md`/`.toml` parity, cloud-sync duplicates, project-specific leak patterns (`FORBIDDEN_PROJECT_PATTERNS`), prompt-injection patterns in LLM surfaces (`scripts/scan-llm-surface-security.py`), and runs every installed scanner (gitleaks, semgrep, shellcheck, PSScriptAnalyzer, yamllint, actionlint, hadolint, syft/grype/trivy, SkillSpector). Missing scanners are skipped with a reason; set `SECURITY_ALLOW_ALL_SKIPPED=1` only for local runs without any scanner. `.github/workflows/validate.yml` runs the same gate in CI, and `changed-code-quality-gate.yml` runs the changed-code static analysis on pull requests.

## Safety

- Do not commit secrets, credentials, private hostnames, ticket-specific content, real customer or organization names, or copied consumer payloads.
- Do not commit cloud-sync duplicates such as `file (1).md`.
- Keep generated consumer exports local unless they are intentionally part of this toolkit.
- Prefer links and generated compatibility surfaces over duplicated tool-specific copies.
- Read-only specialists never edit or post; human-facing replies and external writes need explicit approval (`rules/human-comment-reply-gate.md`, `rules/external-write-authorization.md`).

## Useful Entry Points

- `AGENTS.md` - agent guidance, core principles, and the always-loaded routing index
- `INTENTS.md` - phrase-to-capability map
- `workflows/README.md`, `skills/README.md`, `rules/README.md`, `tool-subagents/README.md` - catalogs
- `learnings/INDEX.md` - one-line index of every captured learning
- `docs/tool-compatibility-paths.md` - provider path map
- `docs/repo-setup-prompt.md` - LLM-guided consumer setup
