---
name: task-starter
description: "Turn a ticket or task description into a scoped implementation plan. Use when the user mentions a Jira/ticket ID, 'start on TICKET-123,' 'pick up this ticket,' or has a task they want planned before coding. Prefer Atlassian CLI (acli); Jira MCP is an alternative."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Task Starter

Turn a ticket or task description into a clear, scoped implementation plan — before writing any code. For Jira tickets, prefer **Atlassian CLI (acli)** (lower context); if unavailable, use **Jira MCP** when configured, or the user's task description and pasted content.

## When to Apply

- User says "start on TICKET-123" or provides a ticket ID
- User describes a task and wants a plan before implementation
- User is picking up work from a ticket/task and needs scope and steps

## Steps

### 1. Get task context

When the user gives a **ticket ID** (e.g. JIRA-12345):

1. **Prefer Atlassian CLI (acli).** If you can run shell commands, try:
   ```bash
   acli jira workitem view <ISSUE_KEY> --json --fields summary,description,comment
   ```
   Parse the JSON output for summary, description, and comments; use that as task context. If the command fails (not found, auth error, etc.), follow **Detect and help set up Jira** below, then retry or fall back.
2. **Else, if Jira MCP is available:** Use MCP to fetch the ticket (summary, description, acceptance criteria, comments). For Story/Defect, request `customfield_13839` (Templated Description) if the description is empty.
3. **Else:** Use the user's message and any pasted ticket text. Ask for missing details (acceptance criteria, scope).

**Detect and help set up Jira (run on user's behalf when possible):**

- Run `acli --version` (or `which acli`) to see if acli is installed. If not:
  - **macOS:** Run `brew tap atlassian/homebrew-acli && brew install acli` (or prompt the user to approve).
  - **Other OS:** Point to [Install ACLI](https://developer.atlassian.com/cloud/acli/guides/install-acli/) or run the appropriate install command if you can infer it.
- If acli is installed but the view command fails with an auth error, run `acli jira auth login --web` and ask the user to complete the browser flow, then retry the view command.
- Give precise, copy-pastable commands for the user's environment. Prefer executing install/auth commands on the user's behalf when they have granted terminal access. See **integrations/jira.md** for full setup and the "Detection and setup (for the agent)" section.

If **no ticket ID** is given, use the user's message and any follow-up (requirements, constraints, links) as the source of truth. Ask for missing details (acceptance criteria, scope) before planning.

### 2. Clarify scope and constraints

- Identify what "done" looks like (acceptance criteria, tests, docs).
- Note stack and repo (e.g. Java/Maven, Node/pnpm) so the plan matches the project.
- If design or API contracts are referenced (Figma, specs, other tickets), note them; use Figma MCP for designs if available and relevant. Plan UI steps with `→ verify: ui-verify` and, when a Figma link exists, `→ verify: figma-compare`.
- For UI/front-end work: run **ui-verify** in the browser before saying the task is complete; if the plan or ticket includes a Figma link, run **figma-compare** after **ui-verify** passes.

### 3. Understand the target codebase

- Read relevant parts of the repo (e.g. similar features, entry points, config, conventions) so the plan matches existing structure and patterns.
- The implementation plan must be grounded in the actual codebase, not generic steps. Do not produce a plan without having inspected the relevant code.

### 4. Produce an implementation plan

Write a short, ordered plan the developer can approve:

```text
Task: <ticket ID or title>

Context:
- <key requirements or constraints>
- <designs / APIs / related work if any>

Plan:
1. [Step] → verify: [how to confirm]
2. [Step] → verify: [how to confirm]
3. [Step] → verify: [how to confirm]

Open questions (resolve before starting):
- <anything ambiguous>
```

**Save the plan to a temp markdown file** so the developer can open it, review it, and ask the agent to implement it in chat:

- Write the same plan (in markdown) to **`docs/jira/<TICKET_KEY>/implementation-plan.md`** when a ticket key exists (e.g. `docs/jira/JIRA-12345/implementation-plan.md`), or **`docs/jira/implementation-plan.md`** when there is no ticket key. Create the directory if it does not exist.
- After saving, tell the developer: open the file and review the plan (and any open questions at the bottom). To have the agent implement it, in chat **@-mention the plan file** and ask to implement it — e.g. *“please build this @docs/jira/JIRA-12345/implementation-plan.md”* or *“implement the plan in @docs/jira/JIRA-12345/implementation-plan.md”* (or *“implement step 2 from @docs/jira/JIRA-12345/implementation-plan.md”* for a single step). The agent will then implement the plan (or the chosen steps) step by step.

**Do not start implementing until the developer approves the plan.**

### 5. Hand off to implementation

After approval, implement following the plan and repo conventions. When done:

- Suggest running **pre-pr-check** (or **ticket-review** / **review** + tests) before opening a PR.
- If behavior or config changed, suggest **doc-delta** to update docs.
- If the user wants to address review findings, use the **fix** skill.

## Without Jira (CLI or MCP)

If neither Atlassian CLI nor Jira MCP is available (or both fail), ask the user to paste the ticket content (summary, description, acceptance criteria) and produce the same style of implementation plan.

## Non-Goals

- Do not start coding before the plan is approved.
- Do not produce a plan without having inspected the relevant code.
- Do not guess at requirements — surface ambiguities and ask.
- Do not add scope beyond what the task describes.

## Related

- `workflows/ticket-research.md` / `workflows/ticket-implementation.md` — the workflow forms of research and execution
- `skills/pathfinder/SKILL.md` — sequence a large plan into deliverable vertical slices
- `skills/test-plan/SKILL.md` — turn the plan's acceptance criteria into a test plan
- `skills/pre-pr-check/SKILL.md` — validations + changed-code quality gate + review before the PR
- `integrations/jira.md` — acli install/auth and the Jira MCP alternative
