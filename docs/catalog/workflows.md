# Workflows

Step-by-step instructions for repeatable work. Use a workflow when the user asks for a process or outcome that benefits from a sequenced checklist; use a skill when the agent should auto-select an on-demand capability from metadata; keep rules as constraints (always-on, or loaded on demand by their trigger). Every workflow file stays under 12,000 characters (`rules/workflow-authoring.md`); this catalog is an index, not a workflow, and the limit does not apply to it; larger procedures are split into companion workflows referenced by path.

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
| `context-compaction.md` | Preserve useful chat or workspace context into durable LLM knowledge and produce a compact future handoff |
| `automation-maintenance.md` | Safely inspect, rename, update, or delete scheduled LLM-tool automations while preserving schedule, status, prompt, and thread binding |
| `capture-learning.md` | Write a trial-and-error discovery into the skill, rule or workflow that owns it, or capture a short-lived `learnings/` intake item when the owner is unclear |
| `run-retrospective.md` | End-of-run retrospective: capture signals, classify mistakes by signature, append the run record, promote recurring mistakes up the ladder, verify, and report trend metrics |
| `knowledge-base-sync.md` | Scheduled knowledge-base sync: gather new knowledge, run the intake gate, promote it on one rolling pull request, archive inbox items after the merge |
| `resource-value-check.md` | Mandatory gate before adding a skill, workflow, agent or rule: blind race against the plain model, CSV record, `scripts/check_value_checks.py` |
| `assistant-workspace-cleanup.md` | Inventory, classify, approve, execute, and verify a cleanup of an AI-assistant workspace (chats, agent sessions, projects, scheduled tasks, artifacts, orchestration ledgers) with a reversibility-grouped approval gate, ID allow-listed lanes, and live-state verification |
| `conversation-monitoring.md` | Watch named conversations (inbox, chat, messaging threads) on a fixed interval until a stop time, alert the user only on new external messages, never reply, and pause or stop safely |
| `workspace-hygiene-auditor-validation.md` | Run the Workspace Hygiene Auditor specialist validation workflow |
| `workspace-hygiene-auditor-evolution.md` | Improve the Workspace Hygiene Auditor specialist from validated misses, noisy findings, and routing gaps |

### Core Engineering

| Workflow | Use when |
| --- | --- |
| `project-execution-main.md` | Orchestrating broad infrastructure, code, pipeline, and notebook work in the data-science project context |
| `project-discovery.md` | Understand a repository, its architecture, and how to work in it |
| `ticket-review.md` | Perform an in-agent AI diff review — report only, no fixes or commits |
| `pre-pr-check.md` | Run validation, review, and docs pass before opening or updating a PR |
| `changed-code-quality-gate.md` | Run a mandatory static-analysis gate against only code added or modified in the current Git change set |
| `run-tests.md` | Run the right tests for a given change |
| `update-docs.md` | Update README, architecture notes, or task docs to match a code or config change |
| `commit-and-push.md` | Semantic commit organization, validation, rebase, and safe push procedure |
| `environment-diagnose.md` | Diagnose local environment, auth, dependency, and container issues safely |

### Tickets, PRs, CI, And Releases

| Workflow | Use when |
| --- | --- |
| `ticket-implementation.md` | Implement a ticket using its research output as input |
| `ticket-research-and-implementation-and-validation.md` | Research a Jira ticket, implement it, then review, fix, and validate until CI is green |
| `pr-validator-validation.md` | Run the PR Validator specialist for live-head PR/ticket readiness, human comments, CI, docs, and approve/block reporting |
| `pr-validator-evolution.md` | Improve the PR Validator from validated live-head, ticket-trace, human-thread, CI, routing, or token-efficiency lessons |
| `java-change-validation.md` | Run a read-only Java specialist validation pass across Java diffs, tests, docs, build evidence, and reviewer reply drafts |
| `gh-address-comments.md` | Address actionable GitHub PR review comments with a human-facing reply approval gate |
| `gh-fix-ci.md` | Diagnose and repair failing GitHub Actions checks on the current PR or branch |
| `pr-automation-review.md` | Triage and fix GitHub PR automation review bot findings (vendor-agnostic; check name varies by org) |
| `security-check-required.md` | Mandatory security gate before any commit or push: secrets, dependency, static-analysis, and toolkit-surface checks |
| `security-report.md` | OWASP-aligned security review with parallel audit lanes and a single synthesized report |

### Infrastructure, Operations, And Logs

| Workflow | Use when |
| --- | --- |
| `aws-alarm-investigator-validation.md` | Run read-only LLM-guided root-cause investigation for AWS CloudWatch alarms |
| `aws-alarm-investigator-evolution.md` | Improve the AWS alarm investigator from validated misses, noisy hypotheses, unsafe evidence handling, and routing gaps |
| `log-investigation.md` | Read-only operational log investigation across CloudWatch, server, application, and access logs |
| `aws-airflow-terraform-change.md` | Plan and implement Terraform-managed Apache Airflow on AWS with clear platform boundaries, validation, and deployment inputs |
| `aws-airflow-terraform-project.md` | Project-local companion to aws-airflow-terraform-change for the data-platform repo (Airflow DAGs plus Terraform roots) |
| `aws-data-platform-ops.md` | Inspect or operate AWS-backed data pipelines with explicit scope, verification, and evidence |
| `folder-reorganization.md` | Reorganize a folder tree without breaking automations, scripts, documents, or cloud-sync links: inspect, propose, approve, pause automations, execute with rollback, verify, resume, report |
| `third-party-installer-vetting.md` | Vet a desktop app a third party asks the user to install (interview, proctoring, client, or vendor tool) with read-only signature, hash, antivirus, and hash-lookup checks, weigh privacy risk, ask for alternatives, and leave the decision to the user |

### Documentation, Diagrams, And Wiki

| Workflow | Use when |
| --- | --- |
| `documentation-reviewer-validation.md` | Run the Documentation Reviewer specialist validation workflow |
| `documentation-reviewer-evolution.md` | Improve the Documentation Reviewer specialist from validated misses, noisy findings, and routing gaps |
| `diagram-creation-specialist-validation.md` | Run the Diagram Creation Specialist for source-grounded C4, AWS, sequence, Mermaid, PlantUML, export, and image-quality validation |
| `diagram-creation-specialist-evolution.md` | Improve the Diagram Creation Specialist from validated notation, export, image-quality, routing, or token-efficiency lessons |
| `confluence-documentation.md` | Create, read, update, delete, move, label, comment, and manage Confluence documentation safely |
| `prod-doc-promoter-validation.md` | Promoting deployed-ticket documentation from a temporary wiki intake folder to canonical homes after a production deploy |
| `prod-doc-promoter-evolution.md` | Improve the Prod Doc Promoter specialist from validated promotion misses, unsafe automation decisions, destination-map gaps, and routing issues |
| `markdown-pdf-export.md` | Generate and verify Jira-ready PDFs from Markdown source files |
| `study-publication-medium-linkedin.md` | Publish a merged study repo as a short system-design-first Medium article and a LinkedIn teaser post in AIDA order per the consumer's positioning profile, with a validation gate before every draft, drafts-only mode, README link PRs, back-links, and a replacement path for live pieces, behind separate approval gates |
| `technical-content-publishing.md` | Turn a software project into an evidence-grounded article, social post, carousel, and visuals - drafted and validated, never posted |

### Data Science, Thesis, And Notebooks

| Workflow | Use when |
| --- | --- |
| `notebook-analysis-update.md` | Update notebooks, EDA, or statistical analysis while preserving reproducibility |
| `notebook-to-script.md` | Promote stable notebook logic into reusable code, scripts, or pipeline steps |
| `notebook-latex-polish.md` | Improve LaTeX math in notebooks or technical docs for readability, consistency, and exportability |
| `ml-experiment-update.md` | Update notebooks, feature pipelines, or model code with reproducibility, leakage checks, and deployment-minded ML discipline |
| `thesis-writing-main.md` | Orchestrate thesis writing, formatting, bibliography, validation, and submission following the institutional thesis specification |
| `thesis-chapter-writing.md` | Writing a thesis chapter by type (introduction, literature review, methodology, results, discussion, conclusion) |
| `thesis-plagiarism-check.md` | Pre-submission plagiarism check for the bilingual thesis: self-review, automated similarity scan, report interpretation, documentation |

### Data Pipelines And Governance

| Workflow | Use when |
| --- | --- |
| `data-source-ingestion.md` | Adding, modifying, or troubleshooting bronze-layer ingestion from public data sources, with storage-mode selection |
| `data-source-storage-backend.md` | Add or change a storage backend (local, S3, or hybrid) for the bronze ingestion layer, including the backend module, client updates, CLI options, and usage examples |
| `dataset-onboarding.md` | Add a new dataset or external feed to a data platform with contracts, validation, and docs |
| `data-pipeline-change.md` | Change an existing Bronze, Silver, Gold, or warehouse-style data pipeline safely |

### Career And Job Search

| Workflow | Use when |
| --- | --- |
| `job-search-pipeline.md` | Run one job scan for a candidate profile: inbox and board reconciliation, owner-approved applications, new-posting discovery and screening, guarded tracker update, skill gaps, digest |
| `career-profile-sync.md` | Keep employment facts, skills, and certifications consistent across a public profile, the CV and its master, and job-search files: ledger first, one-pass update list with intentional snapshots, profile edits, CV re-render and visual check, truthfulness review, hash-checked device writes |
| `job-portal-profile-sync.md` | Complete or fix the owner's profile on a job board or candidate portal in the owner's own signed-in browser session - survey read-only, compare with the profile and master CV, fix unambiguous errors, propose the rest, apply approved edits, verify after reload, optionally apply to named openings, and report what stays owner-only |
| `job-search-attack-plan.md` | Run an urgent, runway-limited job-search sprint for a candidate - two-track intake (bridge income plus target roles), posting analysis, ranked tiers, owner-approved applications with a tracker, a day-by-day plan with templates, interview prep and a resumable context file, delivered as a PDF with clickable links |
| `recruiter-legitimacy-check.md` | Check whether a recruiter, job offer, or contract is legitimate - read every channel in full, map the vendor chain, verify headers and firms, check process, money and terms, give an evidence-backed verdict, draft replies only |
| `screening-interview-quick-prep.md` | Prepare a candidate fast for a screening interview or short technical test - map must-haves to CV evidence with honest gap labels, write CV-grounded answers, verify study videos, add rapid-fire concepts and coding warm-ups, and deliver one keepable cheat sheet |
| `technical-interview-prep.md` | Prepare a candidate for one technical interview (human or AI interviewer) - intake, fact-checked narrative and printable two-block cheat sheet, concept gaps, intro rehearsal, coding-pattern drills, full mock with scoring, final reminders, and a debrief that turns the problem actually asked into the next drill |

Many workflows fan out independent read-only lanes; follow `rules/multi-agent-orchestration.md` and the per-task quality loop in `workflows/task-quality-loop.md` when doing so. Project-local companions (`*-project.md`, thesis workflows) carry this toolkit's data-science/thesis context and are safe to ignore in other consumers.

## How To Invoke

- Ask naturally: "run the pre-PR check", "validate this PR", "investigate this alarm", "export this Markdown to PDF".
- Use `INTENTS.md` for routing and `AGENTS.md` for the always-loaded quick index.
- Reference the file directly when you want a specific workflow (`workflows/<name>.md`).
- Composed workflows reference their sub-workflows by path: `Run the **<name>** workflow (workflows/<name>.md) in full.`
