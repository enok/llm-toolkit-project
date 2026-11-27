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
| **llm-context-engineering** | Keep AGENTS/rules/workflows/skills lean, generic, provider-agnostic, and loaded on demand |
| **llm-toolchain-provisioning** | Export, review, and restore installed LLM assistant extensions (plugins, marketplaces, MCP servers) as a portable manifest; plugin catalog via `scripts/plugins.py` |
| **external-skill-intake** | Safely evaluate, download, adapt, scan, and index skills from public LLM-tool repositories; plugin-specific checks for the intake procedure in `docs/plugins.md` |
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
