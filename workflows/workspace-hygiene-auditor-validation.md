---
description: Run the Workspace Hygiene Auditor specialist validation workflow
---

# Workspace Hygiene Auditor Validation

Use this workflow when the Workspace Hygiene Auditor specialist should validate a change or
artifact before implementation, approval, merge, or handoff.

## Steps

1. Establish repo, base/head, dirty-tree ownership, scope, and relevant evidence.
2. Load only the rules, skills, docs, and source files needed for the specialist.
3. Invoke or follow `tool-subagents/workspace-hygiene-auditor.md`.
4. Reduce findings locally: accept only evidence-backed, in-scope findings.
5. Implement the smallest safe change only when the user requested fixes.
6. Run the narrowest meaningful validation.
7. Report findings, validation, residual risk, and reusable learning.

---

## Evolution

If this specialist misses a recurring issue or is too noisy, run
`workflows/workspace-hygiene-auditor-evolution.md`.
