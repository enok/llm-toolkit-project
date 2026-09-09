---
name: fix
description: Apply fixes from a prior review report using the IDE's LLM. Use when the user wants to "fix issues from review," "address findings," or apply suggestions from docs/jira/<TICKET>/review-report.json.
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Apply Fixes from Report (in-agent)

Apply or plan fixes suggested in a previous review (e.g. after **pre-pr-check**, **review**, or **ticket-review** produced `docs/jira/<TICKET>/review-report.json`). You do the fix work in-agent; no external CLI.

## When to Apply

- User says "fix the issues from the review" or "address the findings"
- There is a `docs/jira/<TICKET>/review-report.json` (or `docs/jira/review/review-report.json` when no ticket applies, or equivalent review output) and the user wants to act on it
- User wants to apply AI-suggested fixes with the IDE's LLM

## Steps

1. **Locate and understand the report.** Read `docs/jira/<TICKET>/review-report.json` (or the path the user gives); infer `<TICKET>` from the branch name, and check `docs/jira/review/` when no ticket is clear — the same locations **review**, **ticket-review**, and **pre-pr-check** write to. Parse findings (each may have type/severity: blocker, suggestion, nice-to-have; file, line, message, suggestion) and the summary; see `rubrics/code-review-checklist.md` for the report format. If no report is found or it is not valid JSON, say so and suggest running **review**, **ticket-review**, or **pre-pr-check** first to generate it; if the user has findings only in `docs/jira/<TICKET>/review.md` alongside it, use that as a fallback.
2. **Understand the code.** Open and read the relevant files cited in the findings. Do not suggest edits without having inspected the code.
3. **Produce a fix plan.** Using the IDE's LLM, create a concrete plan: address findings with type **blocker** (Red) first, then **suggestion** (Yellow), then **nice-to-have** (Green) if the user asks. For each finding (or grouped findings), what to change in which files and how. Ground the plan in the code you read. Present the plan to the user.
4. **Apply on approval.** If the user approves, implement the edits. Then suggest re-running **pre-pr-check**, **review**, or **ticket-review** to verify.

Fix is best-effort; some findings may require manual edits. Always give the LLM code context and report context before suggesting changes.
