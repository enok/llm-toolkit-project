---
name: project-discovery
description: "Help engineers understand the destination project—structure, architecture, flows, how-tos, and related projects. Use when the user wants to 'understand this project,' 'architecture diagram,' 'flow diagram,' 'onboard me to this repo,' 'how do I do X here,' or document how to do things in the codebase."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Project Discovery

Help engineers understand the **destination project** (the repo they are working in): explore structure, document how to do things, create flow and architecture diagrams when missing, identify related or surrounding projects and install steps, and recommend README/docs updates.

## When to Apply

- User says "understand this project," "how does this codebase work," or "explain this repo"
- User asks for an "architecture diagram," "flow diagram," or "system overview" for this project
- User wants to "onboard me to this project," "what do I need to run this," or "what other repos or services do I need"
- User asks "how do I do X in this project?" (e.g. run tests, deploy, add a feature)
- User wants to "document how to …" for this codebase

---

## Steps

### 1. Explore the codebase

- Read root files: README, package.json / pom.xml / build files, config (e.g. tsconfig, Dockerfile).
- Inspect key directories (src/, lib/, app/, tests/, docs/) and any existing architecture or flow docs.
- Read **CONTRIBUTING.md**, **docs/ai-onboarding.md**, or **docs/onboarding.md** when present so instructions stay consistent with project conventions.

### 2. Summarize and document

Produce or update:

- **Project overview** — Purpose, stack, main entry points, and where to find config.
- **How-to explanations** — How to run, test, build, deploy, or add a feature, derived from actual scripts and config (not generic advice).
- **Architecture diagrams** — If missing or clearly outdated, create or update the standard architecture view set: C4 component view for software structure, AWS architecture view for cloud topology, and sequence view for runtime details when evidence supports them. Prefer committed paths such as `docs/architecture.md`. Use `skills/diagram-authoring/references/diagram-type-standards.md` for type selection, then [diagram-conventions.md](references/diagram-conventions.md) for Markdown placement and Mermaid syntax.
- **Flow diagrams** — For important flows (e.g. request path, deployment, data flow) when useful and not already documented. Place under `docs/` (e.g. `docs/flows/request-flow.md`). Flowcharts are summaries and do not replace C4/AWS/sequence views for architecture documentation.

### 3. Surrounding projects and setup

- From config, docs, and scripts, identify sibling repos, services, or tools (e.g. API backends, shared libs).
- List what to clone or install and in what order when relevant, so the engineer can run the project and its dependencies.

### 4. Doc delta

- Compare current README and key docs to what you inferred from the codebase.
- Suggest concrete README/docs updates (sections to add or change). If the user asks to apply changes, edit the files; otherwise offer the suggestions in chat.

---

## Output locations

- Prefer **committed** paths: `docs/architecture.md`, `docs/flows/`, README, CONTRIBUTING.md so the team benefits.
- For ticket-related artifacts (research docs, generated reports, plans, drafts), write to `docs/jira/<TICKET>/`. For general project docs, write to `docs/` or the appropriate committed path. For drafts the user may not want to commit, output in chat or to a temporary path and suggest where to move.

---

## Reference

- Diagram type selection: `skills/diagram-authoring/references/diagram-type-standards.md`
- Diagram format and placement: [diagram-conventions.md](references/diagram-conventions.md)
- Merging toolkit rules with repo-local instruction files: [repository-context-layers.md](references/repository-context-layers.md) (mirrors `rules/repository-context-layers.md`)
