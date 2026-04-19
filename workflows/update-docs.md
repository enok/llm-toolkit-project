---
description: Update README, architecture notes, or task docs to match a code or config change
---

# Update docs workflow

Use when the user asks to update docs, document a change, or keep README or runbooks in sync with code. Often pairs with the **doc-delta** skill.

## Steps

1. Establish scope: code or config change, affected user-facing behavior, and target docs.
2. Once scope is known, split independent discovery lanes **immediately by default**:
   - behavior and API changes
   - operational or runbook impact
   - README, architecture, or ticket-doc drift
3. Do not pause before internal fanout unless there is a user-visible tradeoff or risky external side effect.
4. Apply the smallest doc delta that keeps committed docs truthful and easy to use.

See `rules/multi-agent-orchestration.md` and `rules/operational-doc-required.md`.
