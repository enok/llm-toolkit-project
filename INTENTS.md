# Intent Index

Plain-English prompts map to the shared rules, workflows, skills, and subagents in this repository. Use this as the canonical router: pick **one primary capability**, attach only the helpers the task needs, and keep always-on rules as constraints. Load the full `SKILL.md` or workflow only when the task actually matches. Non-trivial requests also pass through `rules/request-orchestration.md` and `tool-subagents/agent-orchestrator.md` before fanout.

## Review, Validation, And Delivery

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| review my changes / review this PR | `ticket-review` or `review` | workflow + skill | `run-tests`, `code-review`, `rubrics/code-review-checklist.md` |
| review and fix this branch / fix my branch | `ticket-review-and-fix` or `review-and-fix` | workflow + skill | `run-tests`, `pre-pr-check`, `commit-and-push` |
| fix the issues from the review | `fix` | skill | `ticket-review`, `pre-pr-check` |
| pre-PR check this branch / ready for PR | `pre-pr-check` | workflow + skill | `changed-code-quality-gate`, `ticket-review`, `doc-delta`, `ui-verify` |
| run the quality gate on my changed code / Sonar / Semgrep | `changed-code-quality-gate` | workflow + skill | `rules/changed-code-quality-gate-required.md`, `scripts/changed_code_quality_gate.py` |
| validate this PR / is PR #123 ready to approve / approve or block | `pr-validator-validation` | workflow + skill | `pr-validator`, `tool-subagents/pr-validator.md`, `ticket-pr-validation-loop` |
| the ticket is solved, take its PR to approval / monitor the PR | `ticket-pr-validation-loop` | workflow | `ticket-review-and-fix`, `gh-address-comments`, `gh-fix-ci`, `ci-watcher` |
| validate these Java changes / Java reviewer replies | `java-change-validation` | workflow + skill | `java-change-validator`, `java-best-practices`, `rules/human-comment-reply-gate.md` |
| run the right tests / give me a test plan | `run-tests` / `test-plan` | workflow + skill | `testing`, stack-specific best-practices skills, `e2e-release-verification` |
| commit and push / validate and push | `commit-and-push` | workflow | `pre-pr-check`, `git-conventions`, duplicate-file gate |
| address PR comments / reply to the reviewer | `gh-address-comments` | workflow | `rules/human-comment-reply-gate.md`, `review-and-fix` |
| fix CI / GitHub Actions failing / watch CI after push | `gh-fix-ci` | workflow | `ci-watcher`, `rules/ci-feedback-loop.md` |
| fix PR bot findings / PR automation review | `pr-automation-review` | workflow | `review-and-fix` |
| verify the UI works in a browser | `ui-verify` | skill | `figma-compare`, `image-quality-inspection`, `pre-pr-check` |
| does this match the Figma design | `figma-compare` | skill | `ui-verify`, `image-quality-inspection` |
| check the exported image / blurry diagram / screenshot quality | `image-quality-inspection` | skill | `diagram-authoring`, `markdown-pdf-export`, `documentation-reviewer` |
| second opinion / sanity check this plan | `second-opinion` | skill | `design-driven-dev` |
| load test / JMeter / performance test | `jmeter-performance-testing` | skill | `e2e-release-verification`, `log-analysis` |

## Tickets, Implementation, And Releases

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| start ticket `<TICKET-ID>` / plan this task | `task-starter` or `ticket-research` | skill / workflow | `ticket-implementation`, `cross-repo-impact`, `design-driven-dev` |
| implement a ticket / research then implement | `ticket-implementation` / `ticket-research-and-implementation` | workflow | `run-tests`, `review-and-fix`, `ticket-research-and-implementation-and-validation` |
| implement a change / fix a bug / regression | `design-driven-dev` | skill | language best-practices skill, `run-tests`, `test-plan` |
| new backend feature / add endpoint | `new-backend-feature` | workflow | `api-contract-surface`, `testing`, `security` |
| explore before coding / investigate unfamiliar code | `design-driven-dev` | skill | `project-discovery`, `parallel-explorer` |
| slice this plan / break into phases | `pathfinder` | skill | `task-starter` |
| check cross-repo impact / downstream consumers | `cross-repo-impact` | workflow + skill | `api-contract-surface`, `cross-repo-analyst` |
| upgrade dependencies / bump library | `dependency-upgrade` | workflow | `run-tests`, `security` |
| cut or verify a release / rollout / rollback | `release-manager` | skill | `e2e-release-verification`, `release-coordinator`, `rules/release-safety.md` |
| Maven release / release:prepare / deploy to Nexus | `ticket-release` | workflow + skill | `maven-release`, `maven-build-troubleshooting` |
| Maven build failing / OWASP dependency-check / webapp will not start | `maven-build-troubleshooting` | skill | `environment-diagnose`, `java-best-practices` |
| migrate Jenkins to GitHub Actions / Jenkinsfile | `jenkins-to-github-actions` | skill | `ci-migration-and-parity`, `gh-fix-ci` |
| keep CI parity while migrating pipelines | `ci-migration-and-parity` | skill | `jenkins-to-github-actions` |
| copy this record from prod to stage / prep stage data | `cross-env-data-copy` | skill | `rules/command-safety.md`, `runbook-authoring` |
| embed Zoom meeting / Meeting SDK / Zoom signature | `zoom-meeting-sdk` | skill | `security`, `js-ts-best-practices` |
| create a CLI / wrap this as a command | `cli-creator` | skill | `shell-scripting`, `python-best-practices` |

## Infrastructure, Operations, And Logs

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| Terraform / OpenTofu / `.tf` change / plan or apply / state or import (mandatory routing) | `terraform-specialist-validation` | workflow + skill | `terraform-specialist`, `terraform-change-safety`, `terraform`, `pr-validator`, `security-auditor` |
| Terraform cannot apply / manual infrastructure table for the platform team | `terraform-manual-infrastructure-handoff` | workflow | `terraform-specialist`, `confluence-documentation-specialist`, `documentation-reviewer` |
| `terraform_data` / provisioner not re-running / module variable wiring | `terraform-change-safety` | skill | `terraform-specialist` |
| Terraform module patterns / tests / CI | `terraform` | skill | `terraform-specialist`, `security`, `testing` |
| import existing infrastructure into IaC | `infra-adoption` | skill | `terraform-specialist`, `terraform` |
| validate a DAG / Airflow / MWAA / Glue job / crawler / Data Catalog | `dag-glue-specialist-validation` | workflow + skill | `dag-glue-specialist`, `python-best-practices`, `log-analysis`, `system-architecture-specialist` |
| investigate this AWS alarm / CloudWatch alarm root cause / alarm RCA email | `aws-alarm-investigator-validation` | workflow + skill | `aws-alarm-investigator`, `log-analysis`, `incident-ops` |
| analyze logs / CloudWatch logs / server, nginx, Log4j, Lambda, Glue logs | `log-investigation` | workflow + skill | `log-analysis`, `log-analyst`, `rules/log-analysis-safety.md`, `incident-ops` |
| incident / production issue / triage / blank dashboards | `incident-ops` | skill | `release-manager`, `runbook-authoring`, `aws-alarm-investigator` |
| write a runbook / operational docs | `runbook-authoring` | skill | `rules/operational-doc-required.md`, `incident-ops` |
| AWS data pipeline / MWAA / S3 operations | `aws-data-pipeline-ops` or `aws-data-platform-ops` | workflow | `data-pipeline`, `dag-glue-specialist` |
| Airflow on AWS with Terraform | `aws-airflow-terraform-change` | workflow | `terraform-specialist`, `aws-airflow-terraform-project` (toolkit-local) |
| bootstrap or repair local setup / set up my machine | `local-env-bootstrap` | skill | `INFRA.sh` / `INFRA.ps1`, `environment-diagnose` |
| diagnose my environment / cannot build locally | `environment-diagnose` | workflow + skill | `local-env-bootstrap`, `onboarding` |
| which plugins or extensions are installed / reproduce my assistant setup | `llm-toolchain-provisioning` | skill | `local-env-bootstrap` |
| shell script / Bash / PowerShell work | `shell-scripting` | skill | `rules/command-safety.md`, `rules/cross-platform-scripts.md`, `security` |

## Documentation, Diagrams, And Wiki

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| update docs for this change | `update-docs` | workflow + skill | `doc-delta`, `documentation-reviewer-validation`, `document-creation` |
| review documentation / validate generated docs / is this runbook accurate | `documentation-reviewer-validation` | workflow + skill | `documentation-reviewer`, `rules/documentation-review-required.md` |
| create architecture docs / technical documentation | `document-creation` | workflow + skill | `diagram-authoring`, `system-architecture-specialist-validation`, `confluence-documentation` |
| create or fix diagrams / Mermaid / PlantUML / AWS diagrams / C4 | `diagram-authoring` | skill | `diagram-creation-specialist-validation`, `image-quality-inspection` |
| validate diagrams / strict deterministic diagram review | `diagram-creation-specialist-validation` | workflow + skill | `diagram-creation-specialist`, `image-quality-inspection` |
| system architecture review / boundaries / data flows / quality attributes | `system-architecture-specialist-validation` | workflow + skill | `system-architecture-specialist`, `best-practices`, `api-contract-surface` |
| Confluence documentation / wiki CRUD / page hierarchy | `confluence-documentation` | workflow + skill | `rules/external-write-authorization.md`, `rules/examples/confluence-backup-gate.md` |
| validate wiki docs / source-to-wiki drift / attachments and comments | `confluence-documentation-specialist-validation` | workflow + skill | `confluence-documentation-specialist`, `documentation-reviewer` |
| promote deployed ticket docs / clean up the intake folder | `prod-doc-promoter-validation` | workflow + skill | `prod-doc-promoter`, `confluence-documentation-specialist`, `rules/human-comment-reply-gate.md` |
| export Markdown to PDF / ticket-ready PDF | `markdown-pdf-export` | workflow + skill | `image-quality-inspection`, `security` |
| create or edit PowerPoint / PPTX slides | `pptx-generator` | skill | `powerpoint-slides`, `document-conversion` |
| academic or thesis defense deck | `powerpoint-slides` | skill | `pptx-generator`, `tcc-defense-prep` |
| convert PDF / DOCX / XLSX / Markdown | `document-conversion` | skill | `markdown-pdf-export` |
| keep bilingual or paired docs in sync / translation drift | `bilingual-doc-sync` / `paired-doc-sync` / `translation-sync` | workflow | `documentation-reviewer` |

## Security

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| security review / OWASP audit / AppSec report | `security-report` | workflow | `security`, `owasp-security-review`, `security-auditor`, `owasp-security-auditor` |
| injection / auth / secrets / PII question | `security` | skill | `security-best-practices` |
| secure-by-default review for this language or framework | `security-best-practices` | skill | `security` |
| threat model this system | `security-threat-model` | skill | `security`, `owasp-security-review` |
| security ownership / bus factor | `security-ownership-map` | skill | `security` |
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
| compact this chat / preserve context / create a handoff | `context-compaction` | workflow | `chat-knowledge-curation`, `capture-learning` |
| mine chat history / memory / automation runs into durable assets | `chat-knowledge-curation` | workflow + skill | `toolkit-maintenance`, `self-improvement` |
| create a specialist agent / specialist factory | `specialist-agent-factory` | workflow + skill | `llm-context-engineering`, `tool-subagents/README.md` |
| improve the specialist / the validator got it wrong again | `specialist-agent-evolution` | workflow | the matching `*-evolution` workflow (`pr-validator-evolution`, `java-validator-evolution`, `documentation-reviewer-evolution`, `terraform-specialist-evolution`, `dag-glue-specialist-evolution`, `aws-alarm-investigator-evolution`, `diagram-creation-specialist-evolution`, `system-architecture-specialist-evolution`, `confluence-documentation-specialist-evolution`, `prod-doc-promoter-evolution`, `model-selector-evolution`, `agent-orchestrator-evolution`) |
| create, rename, pause, or delete an automation | `automation-maintenance` | workflow | `rules/external-write-authorization.md` |
| edit AGENTS / rules / workflows / skills | `llm-context-engineering` | skill | `toolkit-maintenance`, `rules/workflow-authoring.md` |
| improve this toolkit / maintain the toolkit | `toolkit-maintenance` | workflow | `self-improvement`, `validate-toolkit-indexes`, `learnings/INDEX.md` |
| capture a lesson / save this as a learning | `capture-learning` | workflow | `error-driven-learning` |
| improve the toolkit from this work / capture mistakes | `self-improvement` | workflow | `capture-learning`, `external-skill-intake` |
| import or adapt external LLM skills | `external-skill-intake` | skill | `self-improvement`, `security` |
| LLM app, RAG, agents, memory | `llm-application-architecture` | skill | `llm-context-engineering` |
| understand this project / onboard me | `project-discovery` | workflow + skill | `onboarding`, `parallel-explorer` |
| set up dev-tools in this repo / get started | `onboarding` | skill | `scripts/setup-repo.sh`, `docs/repo-setup-prompt.md` |

## Languages And Engineering Practices

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| Java patterns / Spring | `java-best-practices` | skill | `best-practices`, `testing`, `java-change-validator` |
| JavaScript or TypeScript patterns / async | `js-ts-best-practices` | skill | `best-practices`, `testing` |
| Python patterns | `python-best-practices` | skill | `best-practices`, `testing` |
| SOLID / clean code / architecture patterns | `best-practices` | skill | `system-architecture-specialist` |
| testing patterns / coverage / AC traceability | `testing` | skill | `test-plan`, `run-tests` |
| git conventions / branch naming / semantic commits | `git-conventions` | skill + rule | `commit-and-push` |
| should I use the CLI or the MCP server | `rules/cli-over-mcp.md` | rule | `rules/command-safety.md` |
| can you post this comment / update the ticket | `rules/human-comment-reply-gate.md` | rule | `rules/external-write-authorization.md` |

## Data Science, Thesis, And Public Data

| Ask in plain English | Primary capability | Type | Helpers |
| --- | --- | --- | --- |
| notebook analysis / EDA / clean up this notebook | `notebook-analysis` | workflow + skill | `jupyter-notebook`, `latex-notebooks`, `notebook-to-script` |
| update an existing notebook analysis | `notebook-analysis-update` | workflow | `notebook-analysis`, `analysis-validation` |
| polish LaTeX math in a notebook | `notebook-latex-polish` | workflow | `latex-notebooks` |
| keep the English and Portuguese notebooks in sync | `bilingual-notebook-sync` | workflow | `bilingual-doc-sync`, `paired-doc-sync` |
| ML experiment / model training / leakage check | `ml-experiment` | workflow + skill | `ml-engineering`, `experiment-result-update` |
| update an existing ML experiment | `ml-experiment-update` | workflow | `ml-experiment`, `experiment-result-update` |
| data pipeline change / Bronze, Silver, Gold | `data-pipeline-change` | workflow + skill | `data-pipeline`, `data-pipeline-boundaries`, `data-governance` |
| project-local pipeline change (toolkit-local) | `pipeline-change-project` | workflow | `data-pipeline-change`, `data-pipeline-boundaries` |
| project-local docs sync after a change (toolkit-local) | `documentation-sync-project` | workflow | `update-docs`, `documentation-governance` |
| orchestrate broad project work (toolkit-local) | `project-execution-main` | workflow | `project-overview`, `agent-orchestrator` |
| ingest a new data source / dataset onboarding | `data-source-ingestion` / `dataset-onboarding` | workflow | `data-source-storage-backend`, `data-governance` |
| research or thesis analysis cycle | `research-analysis-cycle` | workflow | `research-thesis-support`, `analysis-validation` |
| USP MBA or thesis context / which method should I use | `research-thesis-support` | skill | `usp-mba-course-context`, `tcc-method-selection`, `course-material-grounding` |
| new class material landed / refresh the course context | `refresh-usp-mba-course-context` | workflow | `course-material-grounding`, `usp-mba-course-context` |
| keep the thesis text aligned with the latest analysis | `tcc-analysis-and-writing-sync` | workflow | `research-analysis-cycle`, `tcc-deliverables` |
| write the thesis / thesis chapter / submission | `thesis-writing-main` | workflow | `thesis-chapter-writing`, `thesis-submission-preparation`, `thesis-completion-guide` |
| bibliography / references / ABNT citations | `thesis-bibliography-integration` | workflow + skill | `thesis-bibliography`, `abnt-formatting` |
| ABNT formatting / TCC manual review | `abnt-formatting` | skill | `tcc-formatting-abnt-review`, `document-conversion` |
| plagiarism check before submission | `thesis-plagiarism-check` | workflow | `thesis-plagiarism-prevention` |
| TCC defense preparation | `tcc-defense-prep` | skill | `powerpoint-slides`, `tcc-deliverables` |
| Brazilian public data / Portal da Transparencia / IBGE | `transparency-portal` or `ibge-datasets` | skill | `municipal-compliance-analysis`, `learnings/transparency-portal-api.md` |

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
