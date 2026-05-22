---
trigger: always_on
description: Size limits and structure rules for workflow files
---

# Workflow Authoring

Rules for writing and maintaining workflow files in `workflows/`.

## Size Limit

- Every workflow file MUST be **≤ 12,000 characters**.
- If a workflow exceeds this limit, split it into multiple files at a natural boundary (e.g., a reusable phase, a self-contained procedure).
- The parent workflow references the extracted file with: `Run the **<name>** workflow (workflows/<name>.md) in full.`

## When to Split

- A phase or procedure is **reused by multiple workflows** (e.g., commit-and-push, test gates).
- The workflow has **clearly independent sections** that make sense as standalone references.
- The file is approaching the 12K limit and has a natural seam.

## Split Conventions

- Extracted workflows get their own file in `workflows/` with a descriptive name.
- The extracted file must be self-contained — it should work if invoked directly.
- The parent file keeps the high-level flow and delegates to the extracted file by path reference.
- Both files must independently stay ≤ 12K characters.

## Composition Pattern

Workflows that compose other workflows (e.g., `ticket-research-and-implementation-and-validation`) should:
- Reference each sub-workflow by path, not inline the content.
- Define gates between sub-workflows (e.g., "do not proceed until user approves").
- Include a comparison table showing when to use the composed vs. individual workflows.
