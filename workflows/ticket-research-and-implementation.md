---
description: Research a Jira ticket deeply then implement it end-to-end
---

# Ticket Research and Implementation Workflow

End-to-end workflow that **researches** a Jira ticket and then **implements** it in a single session. This is a composition of the **ticket-research** and **ticket-implementation** workflows.

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
8. Run pre-PR check or ticket-review-and-fix.
9. Update research docs with any deviations.
10. Present completion summary.

---

## When to Use This vs. Separate Workflows

| Scenario | Workflow |
|----------|----------|
| Research now, implement later (or in another session) | `ticket-research` alone |
| Research already done, ready to code | `ticket-implementation` alone |
| Research and implement in one shot | **This workflow** |
| Quick task with clear scope, no deep research needed | `task-starter` skill → implement directly |

---

## Notes

- The approval gate between Part 1 and Part 2 is **mandatory** — never skip it.
- If Part 1 reveals the ticket is too large, suggest splitting it before implementing.
- If the implementation in Part 2 uncovers issues the research missed, pause, update the research docs, and inform the user before continuing.
- For multi-repo tickets, complete research across all repos first, then implement in dependency order.
