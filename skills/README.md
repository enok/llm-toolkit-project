# Skills

Skills are on-demand capabilities. Each skill lives in `skills/<skill-name>/SKILL.md` and may include optional `rules/`, `references/`, `scripts/`, `agents/`, or `assets/`. Provider folders (`.agents/skills`, `.claude/skills`, `.codex/skills`, `.cursor/skills`, `.windsurf/skills`, `.agent/skills`, `.gemini/skills`, `.opencode/skills`) are links back to this catalog; see `docs/tool-compatibility-paths.md`.

## Conventions

- Folder name must match the `name:` field in `SKILL.md` (lowercase, hyphens).
- Keep the frontmatter `description` short and trigger-rich (what it does AND when to use it) so agents can select the skill from metadata alone.
- Keep the `SKILL.md` body under ~5,000 tokens; put depth in `references/*.md` (frontmatter `title` and `tags`) and fine-grained checks in `rules/*.md`.
- Put broad always-on behavior in top-level `rules/`; put specialized procedures inside the skill; do not duplicate rule text into skills.
- Read-only specialists (`*-specialist`, `*-validator`, `*-reviewer`, `*-investigator`) never edit or post; the root agent owns writes and human-facing replies.
- Keep project-specific details out of shared skills unless they are explicitly scoped to this toolkit's data-science/thesis context (marked "toolkit-local context" below).
- New or modified skills must pass `scripts/validate-skills-with-skillspector.sh --changed` and `scripts/scan-llm-surface-security.py` before commit (`rules/security-check-required.md`).

## Catalog

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

## Validation

Run from the repository root:

```bash
./scripts/validate-toolkit-indexes.sh
npm run skills:index:check
./scripts/validate-skills-with-skillspector.sh --changed
```

PowerShell:

```powershell
.\scripts\validate-toolkit-indexes.ps1
npm run skills:index:check
.\scripts\validate-skills-with-skillspector.ps1
```

See `skills/ARCHITECTURE.md` for the full structure and `workflows/specialist-agent-factory.md` for creating a new specialist (skill + subagent + validation/evolution workflows).
