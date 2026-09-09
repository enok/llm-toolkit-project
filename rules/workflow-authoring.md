---
trigger: always_on
description: Size limits and structure rules for workflow files
---

# Workflow Authoring

Rules for writing and maintaining workflow files in `workflows/`.

## Size Limit

- Every workflow file MUST be **≤ 12,000 characters**.
- Workflow creation, updates, and validation MUST check this limit before handoff.
- If a workflow exceeds this limit, split it into multiple files at a natural boundary (e.g., a reusable phase, a self-contained procedure).
- Do not delete useful detail just to fit the limit. Preserve the detail in a smaller reusable workflow and call it from the original workflow.
- The parent workflow references the extracted file with: `Run the **<name>** workflow (workflows/<name>.md) in full.`

## When to Split

- A phase or procedure is **reused by multiple workflows** (e.g., commit-and-push, test gates).
- The workflow has **clearly independent sections** that make sense as standalone references.
- The file is approaching the 12K limit and has a natural seam.
- The workflow mixes multiple responsibilities that can be dynamically loaded only when needed.

## Split Conventions

- Extracted workflows get their own file in `workflows/` with a descriptive name.
- The extracted file must be self-contained — it should work if invoked directly.
- The parent file keeps the high-level flow and delegates to the extracted file by path reference.
- Both files must independently stay ≤ 12K characters.
- Update `workflows/README.md`, `AGENTS.md`, `README.md`, and `INTENTS.md` when a new reusable workflow becomes user-addressable.

## Single Responsibility

- Keep each workflow focused on one task, gate, or reusable phase.
- Keep rules as compact constraints, skills as specialized capabilities, and agents as focused lanes.
- Compose larger behaviors by reference instead of copying the same instructions into multiple files.
- Move supporting detail into references, templates, scripts, or companion workflows when it is not needed for every invocation.

## Composition Pattern

Workflows that compose other workflows (e.g., `ticket-research-and-implementation-and-validation`) should:
- Reference each sub-workflow by path, not inline the content.
- Define gates between sub-workflows (e.g., "do not proceed until user approves").
- Include a comparison table showing when to use the composed vs. individual workflows.
