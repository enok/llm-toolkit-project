---
description: Research a Jira ticket, implement it, then ticket-review-and-fix until CI is green
---

# Ticket Research, Implementation, and Validation Workflow

End-to-end workflow that **researches** a Jira ticket, **implements** it, and then **reviews, fixes, and validates** the result in a single session. This is a composition of the **ticket-research**, **ticket-implementation**, and **ticket-review-and-fix** workflows.

The user will provide a **ticket ID** (e.g., `ABC-1234`).

---

## Part 1 — Research

Run the **ticket-research** workflow (`workflows/ticket-research.md`) in full:

1. Gather context (Jira, linked tickets, duplicates, PRs, Confluence, classification).
2. Deep code analysis (read files, trace flows, check git history).
3. Generate documentation (`docs/jira/<TICKET>/README.md` and `architecture.md`).
4. Validate and present summary to the user.

**Gate:** Present the research summary and implementation plan to the user. Do not proceed to Part 2 until the user approves the plan.

If the user wants to adjust scope, modify the plan, or resolve open questions — do that now. Update the research docs with any changes before moving on.

---

## Part 2 — Implementation

Run the **ticket-implementation** workflow (`workflows/ticket-implementation.md`) in full:

1. Load and validate the research docs produced in Part 1.
2. Create or checkout the ticket branch.
3. Implement the plan step by step (code, config, docs).
4. Write tests per the testing plan, verify 100% pass.
5. **User Approval Gate** — present changes and wait for explicit approval before committing.
6. Commit using the 5-category structure, rebase, push.
7. Open a draft PR.
8. Update research docs with any deviations.
9. Present implementation summary.

**Gate:** Confirm with the user that the implementation is complete and ready for validation before proceeding to Part 3.

---

## Part 3 — Review, Fix, and Validate

Run the **ticket-review-and-fix** workflow (`workflows/ticket-review-and-fix.md`) in full:

1. **Scope and Context** — determine branch, base, ticket ID, and PR metadata.
2. **Three-Signal Inspection** — inspect against ACs (S1), unresolved PR comments (S2), and rules/skills (S3).
3. **Present Findings** — categorize and present all findings.
4. **Fix All Issues** — fix every Blocker and actionable finding (S1 → S2 → S3).
5. **Update PR and Documentation** — update PR description and related docs.
6. **Unit Tests** — run and verify 100% pass.
7. **Integration Tests** — run and verify 100% pass.
8. **Final Test Gate** — full test suite, zero failures.
9. **User Approval Gate** — present changes and wait for explicit approval before committing.
10. **Commit and Push** — 5-category commit structure, rebase, push.
11. **Monitor CI Until Green** — poll CI, diagnose and fix failures, loop until green.

**Only stop when CI is fully green.**

---

## When to Use This vs. Separate Workflows

| Scenario | Workflow |
|----------|----------|
| Research now, implement later (or in another session) | `ticket-research` alone |
| Research already done, ready to code | `ticket-implementation` alone |
| Research and implement, review later | `ticket-research-and-implementation` |
| Code already written, need review + fix loop | `ticket-review-and-fix` alone |
| Full end-to-end: research → implement → validate | **This workflow** |
| Quick task with clear scope, no deep research needed | `task-starter` skill → implement directly |

---

## Notes

- The approval gate between Part 1 and Part 2 is **mandatory** — never skip it.
- The confirmation between Part 2 and Part 3 ensures scope is stable before validation begins.
- If Part 1 reveals the ticket is too large, suggest splitting it before implementing.
- If the implementation in Part 2 uncovers issues the research missed, pause, update the research docs, and inform the user before continuing.
- If Part 3 review finds architectural issues that require redesign, pause and discuss with the user rather than patching around them.
- For multi-repo tickets, complete research across all repos first, then implement in dependency order, then validate each repo.
