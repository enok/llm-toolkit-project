# Intent Index

Plain-English prompts map to the shared rules, workflows, skills, and subagents in this repository. Use this as the canonical router: pick **one primary capability**, attach only the helpers the task needs, and keep always-on rules as constraints. Load the full `SKILL.md` or workflow only when the task actually matches. Non-trivial requests also pass through `rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md` before fanout.

## Review, Validation, And Delivery

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| review my changes / review this PR | `ticket-review` | workflow + skill | `run-tests`, `rubrics/architecture.md` |
| pre-PR check this branch / ready for PR | `pre-pr-check` | workflow + skill | `changed-code-quality-gate`, `ticket-review`, `doc-delta`, `ui-verify` |
| run the quality gate on my changed code / Sonar / Semgrep | `changed-code-quality-gate` | workflow | `rules/changed-code-quality-gate-required.md`, `scripts/changed_code_quality_gate.py` |
| validate this PR / is PR #123 ready to approve / approve or block | `pr-validator-validation` | workflow + skill | `pr-validator`, `tool-subagents/pr-validator.md` |
| validate these Java changes / Java reviewer replies | `java-change-validation` | workflow + skill | `java-change-validator`, `rules/human-comment-reply-gate.md` |
| run the right tests / give me a test plan | `run-tests` | workflow + skill | `testing`, stack-specific best-practices skills |
| commit and push / validate and push | `commit-and-push` | workflow | `pre-pr-check`, `git-conventions`, duplicate-file gate |
| address PR comments / reply to the reviewer | `gh-address-comments` | workflow | `rules/human-comment-reply-gate.md` |
| fix CI / GitHub Actions failing / watch CI after push | `gh-fix-ci` | workflow | `rules/ci-feedback-loop.md` |
| fix PR bot findings / PR automation review | `pr-automation-review` | workflow | - |
| verify the UI works in a browser | `ui-verify` | skill | `pre-pr-check` |
| second opinion / sanity check this plan | `second-opinion` | skill | `design-driven-dev` |

## Tickets, Implementation, And Releases

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| implement a ticket / research then implement | `ticket-implementation` | workflow | `run-tests`, `ticket-research-and-implementation-and-validation` |
| implement a change / fix a bug / regression | `design-driven-dev` | skill | language best-practices skill, `run-tests` |
| explore before coding / investigate unfamiliar code | `design-driven-dev` | skill | `project-discovery` |
| slice this plan / break into phases | `pathfinder` | skill | - |
| Maven build failing / OWASP dependency-check / webapp will not start | `maven-build-troubleshooting` | skill | `environment-diagnose` |
| migrate Jenkins to GitHub Actions / Jenkinsfile | `jenkins-to-github-actions` | skill | `gh-fix-ci` |
| create a CLI / wrap this as a command | `cli-creator` | skill | `python-best-practices` |

## Infrastructure, Operations, And Logs

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| Terraform / OpenTofu / `.tf` change / plan or apply / state or import (mandatory routing: `terraform fmt -check`, `terraform validate`, and a reviewed plan per touched root; apply and state changes only on explicit user authorization) | `terraform-change-safety` | skill | `pr-validator`, `rules/security-check-required.md` |
| `terraform_data` / provisioner not re-running / module variable wiring | `terraform-change-safety` | skill | - |
| investigate this AWS alarm / CloudWatch alarm root cause / alarm RCA email | `aws-alarm-investigator-validation` | workflow + skill | `aws-alarm-investigator`, `log-analysis`, `incident-ops` |
| analyze logs / CloudWatch logs / server, nginx, Log4j, Lambda, Glue logs | `log-investigation` | workflow + skill | `log-analysis`, `log-analyst`, `rules/log-analysis-safety.md`, `incident-ops` |
| incident / production issue / triage / blank dashboards | `incident-ops` | skill | `runbook-authoring`, `aws-alarm-investigator` |
| write a runbook / operational docs | `runbook-authoring` | skill | `rules/operational-doc-required.md`, `incident-ops` |
| AWS data pipeline / MWAA / S3 operations | `aws-data-platform-ops` | workflow | - |
| Airflow on AWS with Terraform | `aws-airflow-terraform-change` | workflow | `terraform-change-safety`, `aws-airflow-terraform-project` (toolkit-local) |
| bootstrap or repair local setup / set up my machine | `local-env-bootstrap` | skill | `INFRA.sh` / `INFRA.ps1`, `environment-diagnose` |
| diagnose my environment / cannot build locally | `environment-diagnose` | workflow + skill | `local-env-bootstrap`, `onboarding` |
| which plugins or extensions are installed / reproduce my assistant setup | `llm-toolchain-provisioning` | skill | `local-env-bootstrap` |
| reorganize / restructure / clean up a folder tree | `folder-reorganization` | workflow + skill | `agent-orchestrator`, `automation-maintenance` |
| cut or verify a release / rollout / rollback | `maven-release` | skill | `release-coordinator`, `rules/release-safety.md` |
| is this installer safe / a third party wants me to install an app | `third-party-installer-vetting` | workflow | `recruiter-legitimacy-check`, `rules/command-safety.md`, `rules/external-write-authorization.md` |

## Documentation, Diagrams, And Wiki

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| update docs for this change / docs or changelog drift | `update-docs` | workflow + skill | `documentation-sync`, `doc-delta`, `documentation-reviewer-validation` |
| review documentation / validate generated docs / is this runbook accurate | `documentation-reviewer-validation` | workflow + skill | `documentation-reviewer`, `rules/documentation-review-required.md` |
| create or fix diagrams / Mermaid / PlantUML / AWS diagrams / C4 | `diagram-authoring` | skill | `diagram-creation-specialist-validation` |
| validate diagrams / strict deterministic diagram review | `diagram-creation-specialist-validation` | workflow + skill | `diagram-creation-specialist` |
| system architecture review / boundaries / data flows / quality attributes | `system-architecture-specialist` | skill | `best-practices`, `api-contract-surface` |
| Confluence documentation / wiki CRUD / page hierarchy | `confluence-documentation` | workflow + skill | `rules/external-write-authorization.md`, `rules/examples/confluence-backup-gate.md` |
| promote deployed ticket docs / clean up the intake folder | `prod-doc-promoter-validation` | workflow + skill | `prod-doc-promoter`, `confluence-documentation`, `rules/human-comment-reply-gate.md` |
| export Markdown to PDF / ticket-ready PDF | `markdown-pdf-export` | workflow + skill | - |
| convert PDF / DOCX / XLSX / Markdown | `document-conversion` | skill | `markdown-pdf-export` |
| publish a finished study repo on Medium and LinkedIn / write the article and post in AIDA order / retitle a published study article or post | `study-publication-medium-linkedin` | workflow | `diagram-authoring`, `rules/external-write-authorization.md` |
| write or replace a publication (article or post) for my target role / short system-design article with a teaser post / replace the published story and post with a new one | `study-publication-medium-linkedin` | workflow | `rules/publication-positioning.md`, `scripts/check_publication.py`, `scripts/check_upload_target.py`, `rubrics/technical-content.md` (if present) |
| write a technical article / LinkedIn post or carousel about my project (draft only) | `technical-content-publishing` | workflow + skill | `rules/publication-positioning.md`, `diagram-authoring` |
| what is the analysis of last night's debate / hearing / ruling / what do the polls and fact-checkers say | `current-events-briefing` | skill | - |

## Security

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| security review / OWASP audit / AppSec report | `security-report` | workflow | `security-best-practices` |
| secure-by-default review for this language or framework | `security-best-practices` | skill | - |
| security ownership / bus factor | `security-ownership-map` | skill | - |
| run the security gate before commit | `security-check-required` | workflow + rule | `scripts/security-check-toolkit.sh`, `changed-code-quality-gate` |
| is this change safe to ship | `rules/release-safety.md` | rule | `rules/security-check-required.md`, `rules/changed-code-quality-gate-required.md` |
| validate installed or new skills / scan a skill for prompt injection | `external-skill-intake` | skill | `scripts/validate-skills-with-skillspector.sh`, `scripts/scan-llm-surface-security.py` |

## Orchestration, Models, And Toolkit Evolution

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| split this work across agents / orchestrate this request | `agent-orchestrator` | skill + subagent | `rules/request-orchestration.md`, `rules/multi-agent-orchestration.md`, `task-quality-loop` |
| which model should each subtask run on / why did cheap work run on an expensive model | `model-selector` | skill + subagent | `model-selector-validation`, `rules/request-orchestration.md` |
| validate the orchestration / LOA mode / long-running autonomous work | `agent-orchestrator-validation` | workflow | `agent-orchestrator`, `agent-orchestrator-evolution` |
| judge subagent results / produce-validate-refine loop | `task-quality-loop` | workflow | `task-quality-judge`, `verifier` |
| save tokens / reduce context usage / compact command output | `token-efficiency` | skill | `context-compaction` |
| compact this chat / preserve context / create a handoff | `context-compaction` | workflow | `capture-learning` |
| create a specialist agent / specialist factory | `specialist-agent-factory` | workflow + skill | `llm-context-engineering`, `tool-subagents/README.md` |
| improve the specialist / the validator got it wrong again | the matching `*-evolution` workflow (`pr-validator-evolution`, `documentation-reviewer-evolution`, `aws-alarm-investigator-evolution`, `diagram-creation-specialist-evolution`, `prod-doc-promoter-evolution`, `model-selector-evolution`, `agent-orchestrator-evolution`) | workflow | - |
| create, rename, pause, or delete an automation | `automation-maintenance` | workflow | `rules/external-write-authorization.md` |
| edit AGENTS / rules / workflows / skills | `llm-context-engineering` | skill | `rules/workflow-authoring.md` |
| search what we know about X / which asset covers X / how do we do X here | `knowledge-base` | skill | `rules/knowledge-base.md`, `learnings/INDEX.md` |
| save this knowledge / remember this for every agent | `knowledge-base` | skill | `rules/knowledge-base.md` (intake gate), `capture-learning` |
| set up the knowledge base on this machine / the knowledge base is down | `knowledge-base` | skill | `docs/knowledge-base.md`, `environment-diagnose` |
| keep the knowledge base in sync / promote the knowledge inbox | `knowledge-base-sync` | workflow | `knowledge-base`, `rules/external-write-authorization.md` |
| capture a lesson / save this as a learning | `capture-learning` | workflow | `error-driven-learning` |
| run a retrospective / learn from this run's mistakes / what keeps going wrong in `<workflow>` / show the quality trend of a workflow | `run-retrospective` | workflow + skill | `rules/workflow-self-improvement.md`, `capture-learning`, `task-quality-loop` |
| make every workflow learn from its mistakes / measure workflow accuracy over time | `rules/workflow-self-improvement.md` | rule | `run-retrospective`, `error-driven-learning`, `rules/request-orchestration.md` |
| import or adapt external LLM skills | `external-skill-intake` | skill | - |
| add or install a plugin / find a plugin in the marketplace | `docs/plugins.md` | script | `rules/plugin-governance.md`, `external-skill-intake`, `scripts/plugins.py` |
| remove unnecessary plugins / prune plugins | `docs/plugins.md` | script | `rules/plugin-governance.md`, `llm-toolchain-provisioning`, `scripts/plugins.py` |
| audit installed plugins / are my plugins safe | `docs/plugins.md` | script | `llm-toolchain-provisioning`, `scripts/plugins.py` |
| add a new skill, workflow, agent or rule / does this resource beat the plain model / value-check a toolkit resource | `resource-value-check` | workflow | `docs/llm/value-checks.csv`, `scripts/check_value_checks.py` |
| which plugin, skill or agent is best for this task | `rules/plugin-governance.md` | rule | `agent-orchestrator`, `knowledge-base`, `scripts/plugins.py` |
| understand this project / onboard me | `project-discovery` | workflow + skill | `onboarding` |
| set up dev-tools in this repo / get started | `onboarding` | skill | `scripts/setup-repo.sh`, `docs/repo-setup-prompt.md` |
| use the toolkit in every session / install it globally for my user | `docs/global-install.md` | script | `scripts/install-global-surfaces.sh`, `scripts/install-global-surfaces.ps1`, `tool-subagents/agent-orchestrator.md` |
| clean up / tidy my chats, sessions, projects, scheduled tasks, or artifacts / delete the fired one-shots | `assistant-workspace-cleanup` | workflow + skill | `workspace-hygiene-auditor`, `rules/external-write-authorization.md`, `skills/assistant-workspace-cleanup/references/ui-automation-lane-safety.md` |
| which of my chats, sessions, or scheduled tasks can go / classify this workspace inventory | `workspace-hygiene-auditor-validation` | workflow + skill | `workspace-hygiene-auditor`, `workspace-hygiene-auditor-evolution`, `assistant-workspace-cleanup` |
| keep watching this inbox / chat / thread and tell me when they reply | `conversation-monitoring` | workflow | `rules/external-write-authorization.md`, `rules/human-comment-reply-gate.md` |
| what should I automate / what work do I keep repeating / find my repetitive tasks | `repeat-work-discovery` | skill | `skills/repeat-work-discovery/references/proposal-shapes.md`, `automation-maintenance` |
| how much time does the toolkit save / what is the productivity impact or ROI | `productivity-impact-estimate` | skill | `skills/productivity-impact-estimate/scripts/productivity_estimate.py` |

## Languages And Engineering Practices

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| JavaScript or TypeScript patterns / async | `js-ts-best-practices` | skill | `best-practices`, `testing` |
| Python patterns | `python-best-practices` | skill | `best-practices`, `testing` |
| SOLID / clean code / architecture patterns | `best-practices` | skill | `system-architecture-specialist` |
| testing patterns / coverage / AC traceability | `testing` | skill | `run-tests` |
| git conventions / branch naming / semantic commits | `git-conventions` | skill + rule | `commit-and-push` |
| should I use the CLI or the MCP server | `rules/cli-over-mcp.md` | rule | `rules/command-safety.md` |
| can you post this comment / update the ticket | `rules/human-comment-reply-gate.md` | rule | `rules/external-write-authorization.md` |
| the Next / Submit button does nothing on this web form | `web-form-submit-debugging` | skill | `skills/web-form-submit-debugging/references/instrumentation-snippets.md`, `skills/assistant-workspace-cleanup/references/ui-automation-lane-safety.md` |

## Data Science, Thesis, And Public Data

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| notebook analysis / EDA / clean up this notebook | `jupyter-notebook` | skill | `notebook-to-script` |
| update an existing notebook analysis | `notebook-analysis-update` | workflow | - |
| polish LaTeX math in a notebook | `notebook-latex-polish` | workflow | - |
| update an existing ML experiment | `ml-experiment-update` | workflow | - |
| data pipeline change / Bronze, Silver, Gold | `data-pipeline-change` | workflow | - |
| orchestrate broad project work (toolkit-local) | `project-execution-main` | workflow | `agent-orchestrator` |
| ingest a new data source / dataset onboarding | `data-source-ingestion` / `dataset-onboarding` | workflow | `data-source-storage-backend` |
| write the thesis / thesis chapter / submission | `thesis-writing-main` | workflow | `thesis-chapter-writing` |
| plagiarism check before submission | `thesis-plagiarism-check` | workflow | - |

## Career And Job Search

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| run my job scan / daily job pipeline / find new jobs and update my tracker | `job-search-pipeline` | workflow + skill | `agent-orchestrator`, `task-quality-loop`, `skills/job-search-pipeline/references/lane-prompts.md` |
| check my applications / move my tracker rows / recruiter replies | `job-search-pipeline` | workflow + skill | `skills/job-search-pipeline/scripts/tracker_ops.py` |
| is this course / degree / MBA / certification worth it for my career / does it carry weight in the market | `credential-evaluation` | skill | `agent-orchestrator`, `task-quality-loop`, `skills/credential-evaluation/references/lane-prompts.md` |
| sync my CV with LinkedIn / keep my profile, CV and job-search files consistent / I left my employer, update everything / re-render my CV | `career-profile-sync` | workflow | `task-quality-loop` |
| I need results fast / urgent job search / attack plan / find me more positions | `job-search-attack-plan` | workflow | `contract-platform-vetting`, `job-search-pipeline`, `technical-interview-prep` |
| I am signed in to a job board, finish or fix my profile there | `job-portal-profile-sync` | workflow | `job-search-pipeline`, `career-profile-sync`, `skills/job-search-pipeline/references/application-truthfulness.md` |
| is this recruiter / offer / contract legit or a scam | `recruiter-legitimacy-check` | workflow | `third-party-installer-vetting`, `rules/human-comment-reply-gate.md`, `rules/external-write-authorization.md` |
| is this AI-training / expert-contractor gig platform legit / what rate should I enter | `contract-platform-vetting` | skill | `recruiter-legitimacy-check` |
| help me prepare for this interview / mock interview / debrief my interview | `technical-interview-prep` | workflow + skill | `interview-prep-planner`, `skills/job-search-pipeline/references/application-truthfulness.md` |
| build my interview study plan / what should I study for these roles | `interview-prep-planner` | skill | `technical-interview-prep`, `screening-interview-quick-prep` |
| prepare me fast for a screening interview or short test / tomorrow's call | `screening-interview-quick-prep` | workflow | `technical-interview-prep`, `interview-prep-planner` |

## Provider Surfaces

| Tool | Primary surface |
| --- | --- |
| Codex / generic agents | `AGENTS.md`, `.agents/skills`, optional `.codex/skills`, `.codex/agents` |
| Cursor | `.cursor/rules`, `.cursor/workflows`, `.cursor/skills`, `.cursor/agents` |
| Claude Code | `CLAUDE.md` (pointer), `.claude/skills`, `.claude/agents` |
| Windsurf | `.windsurf/rules`, `.windsurf/workflows`, `.windsurf/skills` |
| GitHub Copilot | `.github/copilot-instructions.md` when generated by `sync-tool-configs` |
| Gemini CLI / OpenCode / Antigravity | `.gemini/skills`, `.opencode/skills`, `.agent/skills` |

The full path map is `docs/tool-compatibility-paths.md`. Regenerate compatibility surfaces with:

```bash
./scripts/sync-tool-configs.sh . --skip-agents-md --skip-github
```
