---
name: project-discovery
description: "Explain or document the repo the engineer is working in: what it does, its structure, architecture and flow diagrams, how-tos (run, test, build, deploy), related projects, and README gaps. Has a read-only explain mode for plain questions. Use whenever the user says 'understand this project,' 'what does this project do,' 'explain this repo,' 'architecture diagram,' 'flow diagram,' 'onboard me,' or 'how do I do X here,' even if they never say 'discovery'."
license: MIT
metadata:
  author: dev-tools
  version: "1.1.1"
---

# Project Discovery

Help engineers understand the **destination project** (the repo they are working in): explore structure, document how to do things, create flow and architecture diagrams when missing, identify related or surrounding projects and install steps, and recommend README/docs updates.

## When to Apply

- User says "understand this project," "how does this codebase work," "explain this repo," or "what does this project do?"
- User asks for an "architecture diagram," "flow diagram," or "system overview" for this project
- User wants to "onboard me to this project," "what do I need to run this," or "what other repos or services do I need"
- User asks "how do I do X in this project?" (e.g. run tests, deploy, add a feature)
- User wants to "document how to …" for this codebase

---

## Explain-only mode

Use when the ask is a read-only question ("what does this project do?", "explain this repo") and no docs or diagrams were requested. The deliverable is a chat answer and no files are written, because the user asked a question, not for repo changes.

- **Read cheapest-first:** README, the repo instruction file (`AGENTS.md`/`CLAUDE.md`) for conventions only, the docs index (headings of `docs/*.md`), the build file, the core source of the main flow or example, tests, CI config, and `git log --oneline -15`.
- **Separate subject from plumbing** (so the answer describes the project, not the tooling around it): a generated shared-rules block in `AGENTS.md`, provider link folders (`.claude/`, `.cursor/`, `.windsurf/`, `.agents/`), config-sync scripts, and exported assistant instructions are LLM-tool wiring, not the project. Mention them in one closing line.
- **Answer shape:** (1) what it is and why, in one paragraph; (2) the core domain or example, with roles mapped to concrete classes/modules and rules or numbers quoted from source; (3) a short map of docs and code; (4) how correctness is enforced (tests, CI jobs, docs drift guards, branch protection); (5) how to run it, with commands copied from README or CI.
- **Fidelity:** state only numbers, versions, and rules you read from source in this run, since README claims drift from code. When README and code disagree, say which and where.
- **Lane sizing:** a small repo needs one `light` read lane, not the full-discovery split in `workflows/project-discovery.md`, which costs more than the question is worth. Offer a doc delta (step 4 below) only if you found a real gap.

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

- Diagram type selection (read when choosing which diagram to create): `skills/diagram-authoring/references/diagram-type-standards.md`
- Diagram format and placement (read before writing or placing a Mermaid diagram): [diagram-conventions.md](references/diagram-conventions.md)
- Merging toolkit rules with repo-local instruction files (read when the repo has its own `AGENTS.md`/`CLAUDE.md` that may conflict with toolkit rules): [repository-context-layers.md](references/repository-context-layers.md) (mirrors `rules/repository-context-layers.md`)
