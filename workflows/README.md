# Workflows

Step-by-step instructions for repeatable work. Use a workflow when the user asks for a process or outcome that benefits from a sequenced checklist; use a skill when the agent should auto-select an on-demand capability from metadata; keep rules as always-on constraints. Every workflow stays under 12,000 characters (`rules/workflow-authoring.md`); larger procedures are split into companion workflows referenced by path.

Specialist agents ship as a **validation** workflow (run the specialist) plus an **evolution** workflow (improve it from validated misses, noise, or routing gaps). `INTENTS.md` maps plain-English asks to the right entry point; `rules/request-orchestration.md` routes non-trivial requests through `tool-subagents/agent-orchestrator.md`.

## Available workflows

### Orchestration, Quality Loops, And Toolkit Evolution

| Workflow | Use when |
| --- | --- |
| `task-quality-loop.md` | Reusable per-task produce-validate-refine loop with a hard iteration budget, validator selection map, and tier escalation |
| `agent-orchestrator-validation.md` | Validate capability-first agent orchestration, per-task model selection, SLA accounting, and explicit LOA mode handoffs |
| `agent-orchestrator-evolution.md` | Improve agent orchestrator routing, model selection, validation, state checkpoints, and token efficiency from validated evidence |
| `model-selector-validation.md` | Assign and verify per-task complexity tier, model, effort, and token band before execution, and audit a finished tasks table for overspend |
| `model-selector-evolution.md` | Improve the Model Selector specialist from mis-tiered tasks, overspend misses, and stale lookup rows |
| `specialist-agent-factory.md` | Create a reusable specialist agent with prompt, workflows, skill entrypoint, routing, client overlays, and validation gates |
| `specialist-agent-evolution.md` | Improve reusable specialist agents from validated misses, noisy outputs, weak routing, and token-efficiency lessons |
| `context-compaction.md` | Preserve useful chat or workspace context into durable LLM knowledge and produce a compact future handoff |
| `chat-knowledge-curation.md` | Mine chat, memory, rollout, automation, and learning evidence into durable LLM toolkit assets |
| `automation-maintenance.md` | Safely inspect, rename, update, or delete scheduled LLM-tool automations while preserving schedule, status, prompt, and thread binding |
| `capture-learning.md` | Capture a trial-and-error discovery into the learnings inbox so any future LLM session goes directly to the happy path |
| `self-improvement.md` | Capture mistakes as happy-path learnings, identify reusable skills/workflows, and safely harvest external LLM-tool skills |
| `toolkit-maintenance.md` | Maintain the shared LLM toolkit — mine feedback, de-duplicate guidance, add generic skills/workflows, validate indexes, and sync clients |

### Core Engineering

| Workflow | Use when |
| --- | --- |
| `project-execution-main.md` | Orchestrating broad infrastructure, code, pipeline, and notebook work in the data-science project context |
| `project-discovery.md` | Understand a repository, its architecture, and how to work in it |
| `review.md` | Review code changes for bugs, correctness, security, and test coverage |
| `review-and-fix.md` | Review + fix + test + push loop for current branch changes |
| `ticket-review.md` | Perform an in-agent AI diff review — report only, no fixes or commits |
| `ticket-review-and-fix.md` | Review + fix + test + push loop for current branch changes |
| `pre-pr-check.md` | Run validation, review, and docs pass before opening or updating a PR |
| `changed-code-quality-gate.md` | Run a mandatory static-analysis gate against only code added or modified in the current Git change set |
| `run-tests.md` | Run the right tests for a given change |
| `update-docs.md` | Update README, architecture notes, or task docs to match a code or config change |
| `commit-and-push.md` | Semantic commit organization, validation, rebase, and safe push procedure |
| `cross-repo-impact.md` | Map downstream impact of a shared change across sibling or related repositories |
| `new-backend-feature.md` | Add a new REST endpoint, service, or backend feature |
| `environment-diagnose.md` | Diagnose local environment, auth, dependency, and container issues safely |
| `dependency-upgrade.md` | Upgrade dependencies with compatibility, security, and validation in mind |

### Tickets, PRs, CI, And Releases

| Workflow | Use when |
| --- | --- |
| `ticket-research.md` | Deep-dive a Jira ticket before implementation |
| `ticket-implementation.md` | Implement a ticket using its research output as input |
| `ticket-research-and-implementation.md` | Research a Jira ticket deeply then implement it end-to-end |
| `ticket-research-and-implementation-and-validation.md` | Research a Jira ticket, implement it, then ticket-review-and-fix until CI is green |
| `ticket-pr-validation-loop.md` | Validate a solved ticket and drive the related PR through comments, CI/CD, fixes, and final approval readiness |
| `pr-validator-validation.md` | Run the PR Validator specialist for live-head PR/ticket readiness, human comments, CI, docs, and approve/block reporting |
| `pr-validator-evolution.md` | Improve the PR Validator from validated live-head, ticket-trace, human-thread, CI, routing, or token-efficiency lessons |
| `java-change-validation.md` | Run a read-only Java specialist validation pass across Java diffs, tests, docs, build evidence, and reviewer reply drafts |
| `java-validator-evolution.md` | Improve the Java change validator from validated misses, noisy findings, and reusable Java review lessons |
| `gh-address-comments.md` | Address actionable GitHub PR review comments with a human-facing reply approval gate |
| `gh-fix-ci.md` | Diagnose and repair failing GitHub Actions checks on the current PR or branch |
| `pr-automation-review.md` | Triage and fix GitHub PR automation review bot findings (vendor-agnostic; check name varies by org) |
| `ticket-release.md` | Cut a Maven release — prepare, perform, verify in Nexus, and update downstream client projects |
| `security-check-required.md` | Mandatory security gate before any commit or push: secrets, dependency, static-analysis, and toolkit-surface checks |
| `security-report.md` | OWASP-aligned security review with parallel audit lanes and a single synthesized report |

### Infrastructure, Operations, And Logs

| Workflow | Use when |
| --- | --- |
| `terraform-specialist-validation.md` | Run the Terraform Specialist for module/root review, plan safety, state lifecycle, multi-env roots, and IaC readiness reporting |
| `terraform-specialist-evolution.md` | Evolve the Terraform Specialist after misses, noisy findings, or token-inefficient runs |
| `terraform-manual-infrastructure-handoff.md` | Generate a source-grounded manual infrastructure handoff from Terraform when the target environment cannot be applied |
| `dag-glue-specialist-validation.md` | Validate Airflow DAGs, MWAA/Astro deployments, AWS Glue jobs, crawlers, Data Catalog changes, and ETL pipeline PRs with the DAG/Glue Specialist |
| `dag-glue-specialist-evolution.md` | Improve the DAG/Glue Specialist from validated Airflow, Glue, crawler, Data Catalog, runtime-safety, external-source, and routing lessons |
| `aws-alarm-investigator-validation.md` | Run read-only LLM-guided root-cause investigation for AWS CloudWatch alarms |
| `aws-alarm-investigator-evolution.md` | Improve the AWS alarm investigator from validated misses, noisy hypotheses, unsafe evidence handling, and routing gaps |
| `log-investigation.md` | Read-only operational log investigation across CloudWatch, server, application, and access logs |
| `aws-airflow-terraform-change.md` | Plan and implement Terraform-managed Apache Airflow on AWS with clear platform boundaries, validation, and deployment inputs |
| `aws-airflow-terraform-project.md` | Project-local companion to aws-airflow-terraform-change for the data-platform repo (Airflow DAGs plus Terraform roots) |
| `aws-data-pipeline-ops.md` | Inspect AWS-backed data pipelines with read-first S3, MWAA, Airflow, CloudWatch, and Secrets Manager operations |
| `aws-data-platform-ops.md` | Inspect or operate AWS-backed data pipelines with explicit scope, verification, and evidence |

### Documentation, Diagrams, And Wiki

| Workflow | Use when |
| --- | --- |
| `document-creation.md` | Create or update architecture docs, diagrams, and Confluence pages |
| `documentation-reviewer-validation.md` | Run the Documentation Reviewer specialist validation workflow |
| `documentation-reviewer-evolution.md` | Improve the Documentation Reviewer specialist from validated misses, noisy findings, and routing gaps |
| `diagram-creation-specialist-validation.md` | Run the Diagram Creation Specialist for source-grounded C4, AWS, sequence, Mermaid, PlantUML, export, and image-quality validation |
| `diagram-creation-specialist-evolution.md` | Improve the Diagram Creation Specialist from validated notation, export, image-quality, routing, or token-efficiency lessons |
| `system-architecture-specialist-validation.md` | Source-grounded application architecture, boundary, data-flow, integration, and quality-attribute review |
| `system-architecture-specialist-evolution.md` | Improve the System Architecture Specialist from validated architecture, source-grounding, routing, handoff, or token-efficiency lessons |
| `confluence-documentation.md` | Create, read, update, delete, move, label, comment, and manage Confluence documentation safely |
| `confluence-documentation-specialist-validation.md` | Run the Confluence Documentation Specialist for source-grounded wiki page, hierarchy, attachment, comment, and draft-reply validation |
| `confluence-documentation-specialist-evolution.md` | Improve the Confluence Documentation Specialist from validated wiki, hierarchy, attachment, comment, routing, or token-efficiency lessons |
| `prod-doc-promoter-validation.md` | Promoting deployed-ticket documentation from a temporary wiki intake folder to canonical homes after a production deploy |
| `prod-doc-promoter-evolution.md` | Improve the Prod Doc Promoter specialist from validated promotion misses, unsafe automation decisions, destination-map gaps, and routing issues |
| `markdown-pdf-export.md` | Generate and verify Jira-ready PDFs from Markdown source files |
| `documentation-sync-project.md` | Project-local companion to update-docs: keep the data-science repo docs, notebooks, and README aligned after changes |
| `bilingual-doc-sync.md` | Keep English and localized documentation or notebooks aligned during code and analysis changes |
| `paired-doc-sync.md` | Keep paired docs, notebooks, and deliverables synchronized across languages or presentation variants |
| `translation-sync.md` | Keep English and translated docs, labels, and examples synchronized after changes |

### Data Science, Thesis, And Notebooks

| Workflow | Use when |
| --- | --- |
| `notebook-analysis.md` | Work safely in notebooks while preserving reproducibility and promotion paths into versioned code |
| `notebook-analysis-update.md` | Update notebooks, EDA, or statistical analysis while preserving reproducibility |
| `notebook-to-script.md` | Promote stable notebook logic into reusable code, scripts, or pipeline steps |
| `notebook-latex-polish.md` | Improve LaTeX math in notebooks or technical docs for readability, consistency, and exportability |
| `ml-experiment.md` | Run or update an ML experiment with explicit baselines, leakage checks, and reproducible evaluation |
| `ml-experiment-update.md` | Update notebooks, feature pipelines, or model code with reproducibility, leakage checks, and deployment-minded ML discipline |
| `experiment-result-update.md` | Propagate an analytical or model result change into the docs, notebooks, and supporting context that depend on it |
| `research-analysis-cycle.md` | Run an evidence-heavy research or thesis analysis cycle from question framing through method choice, result generation, and report updates |
| `analysis-validation.md` | Validate analytical outputs (numbers, figures, tables, claims) before they support thesis conclusions |
| `thesis-writing-main.md` | Orchestrate thesis writing, formatting, bibliography, validation, and submission following the institutional TCC specification |
| `thesis-chapter-writing.md` | Writing a thesis chapter by type (introduction, literature review, methodology, results, discussion, conclusion) |
| `thesis-submission-preparation.md` | Final pre-submission checklist, final review, and submission packaging |
| `thesis-completion-guide.md` | End-to-end completion guide for the MBA thesis: remaining chapters, analyses, deliverables, and submission order |
| `thesis-bibliography-integration.md` | Systematically insert and verify bibliographic references that justify every thesis method, decision, and framework |
| `thesis-plagiarism-check.md` | Pre-submission plagiarism check for the bilingual thesis: self-review, automated similarity scan, report interpretation, documentation |
| `thesis-plagiarism-prevention.md` | Day-to-day plagiarism prevention habits, tooling, and the emergency fix when a section is flagged |
| `tcc-method-selection.md` | Choose or refine the thesis analytical method once the research question is clear (candidates, criteria, decision record) |
| `tcc-analysis-and-writing-sync.md` | Project-local step after research-analysis-cycle: keep thesis narrative, tables, and figures aligned with the latest analysis |
| `tcc-formatting-abnt-review.md` | Comparing the institutional TCC manual and template against ABNT NBR 14724 |
| `refresh-usp-mba-course-context.md` | Refresh the repo LLM guidance when new USP MBA class material lands in the local course corpus |
| `course-material-grounding.md` | Ground a task in the local USP MBA course corpus (class material, slides, notebooks) before applying generic best practices |

### Data Pipelines And Governance

| Workflow | Use when |
| --- | --- |
| `data-source-ingestion.md` | Adding, modifying, or troubleshooting bronze-layer ingestion from public data sources, with storage-mode selection |
| `data-source-storage-backend.md` | Add or change a storage backend (local, S3, or hybrid) for the bronze ingestion layer, including the backend module, client updates, CLI options, and usage examples |
| `dataset-onboarding.md` | Add a new dataset or external feed to a data platform with contracts, validation, and docs |
| `data-pipeline-change.md` | Change an existing Bronze, Silver, Gold, or warehouse-style data pipeline safely |
| `pipeline-change-project.md` | Project-local companion to data-pipeline-change: bronze/silver/gold pipeline changes with contract and downstream checks |
| `bilingual-notebook-sync.md` | Keep English and Portuguese notebook pairs synchronized after edits (cells, outputs, narrative, translations) |

Many workflows fan out independent read-only lanes; follow `rules/multi-agent-orchestration.md` and the per-task quality loop in `workflows/task-quality-loop.md` when doing so. Project-local companions (`*-project.md`, `documentation-sync-project.md`, thesis workflows) carry this toolkit's data-science/thesis context and are safe to ignore in other consumers.

## How To Invoke

- Ask naturally: "run the pre-PR check", "validate this PR", "investigate this alarm", "export this Markdown to PDF".
- Use `INTENTS.md` for routing and `AGENTS.md` for the always-loaded quick index.
- Reference the file directly when you want a specific workflow (`workflows/<name>.md`).
- Composed workflows reference their sub-workflows by path: `Run the **<name>** workflow (workflows/<name>.md) in full.`
