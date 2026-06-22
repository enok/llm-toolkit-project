# LLM Toolkit Project - Agent Guidance

This repository is the shared source of truth for local LLM-assisted development assets: rules, workflows, skills, rubrics, setup scripts, and provider compatibility surfaces. Consumer projects should link to this toolkit or select from it; they should not copy private, project-specific, company-specific, or ticket-specific guidance back into the shared catalog.

## Core Principles

1. Read `learnings/INDEX.md` before non-trivial work and follow any relevant happy path.
2. Keep shared guidance generic. Put real customer names, internal hostnames, production payloads, ticket IDs, and one-off paths in the consumer repo instead.
3. Prefer progressive disclosure: short always-loaded rules, task workflows, on-demand skills, and deeper references only when needed.
4. Keep provider folders thin. Canonical content lives in `rules/`, `workflows/`, `skills/`, `rubrics/`, and `tool-subagents/`.
5. Verify changes before reporting success. Run the smallest meaningful checks first, then the toolkit validation gate before commit or push.

## Repository Map

| Path | Purpose |
| --- | --- |
| `rules/` | Short, generic rules that broadly apply across tasks |
| `workflows/` | Step-by-step procedures for manually invoked work |
| `skills/` | On-demand capabilities with optional references, rules, agents, or scripts |
| `tool-subagents/` | Shared subagent prompt definitions for compatible IDEs |
| `rubrics/` | Architecture, security, and review checklists |
| `integrations/` | Generic setup notes for external tools |
| `docs/llm/` | Local toolkit selection and data-science/thesis context |
| `learnings/` | Trial-and-error discoveries and known local gotchas |
| `scripts/` | Setup, sync, validation, and document export helpers |

## Intent Routing

Use `INTENTS.md` as the quick phrase-to-capability map. Common examples:

| User asks for | Prefer |
| --- | --- |
| Review my changes | `ticket-review` or `review` |
| Review and fix | `review-and-fix` |
| Pre-PR check | `pre-pr-check` |
| Run the right tests | `run-tests` |
| Update docs | `update-docs` or `doc-delta` |
| Improve this toolkit | `toolkit-maintenance` and `llm-context-engineering` |
| Capture a lesson | `capture-learning` and `error-driven-learning` |
| Work with thesis or USP MBA context | `research-thesis-support`, `tcc-deliverables`, or `usp-mba-course-context` |

## Validation

Before committing toolkit changes, run:

```powershell
.\scripts\validate-toolkit-indexes.ps1
.\scripts\security-check-toolkit.ps1
.\scripts\validate-skills-with-skillspector.ps1
```

Git Bash equivalents:

```bash
./scripts/validate-toolkit-indexes.sh
./scripts/security-check-toolkit.sh
./scripts/validate-skills-with-skillspector.sh
```

`security-check-toolkit` runs SkillSpector automatically when the Python package is installed. The dedicated SkillSpector script is useful for focused current/new skill vetting and fails on `HIGH`/`CRITICAL` findings by default.

Also run the duplicate-file gate before push:

```bash
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files" && exit 1
```

If a validation failure reveals a reusable toolchain gotcha, capture it under `learnings/` after user approval.
