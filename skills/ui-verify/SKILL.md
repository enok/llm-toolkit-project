---
name: ui-verify
description: Verify front-end UI in a real browser before declaring work done. Uses any configured browser MCP (Playwright MCP recommended outside Cursor) to start or attach to the dev server, exercise acceptance criteria, and report pass/fail. Use after implementing UI changes, fixing front-end bugs, or when the user asks to verify/check/test the interface in the browser.
license: MIT
---

# UI Verify (browser)

Verify that implemented UI **actually works in a browser** before telling the user the task is finished. This skill is **mandatory for front-end changes** unless the user explicitly skips verification or no browser MCP is available.

**IDE-agnostic:** Works with any agent host that exposes a browser MCP. **Playwright MCP** (`@playwright/mcp`) is the recommended default when not on Cursor. Cursor's **cursor-ide-browser** is one supported provider, not a requirement.

## When to Apply

- After implementing or fixing React/UI code (feature, bug fix, styling that affects behavior)
- User says "verify in browser", "check the UI", "test the interface", or "make sure it works"
- At the end of a **task-starter** plan when steps touch UI (run before saying "done")
- After **fix** when findings were UI-related

## Prerequisites

| Requirement | If missing |
|-------------|------------|
| **Browser MCP** configured in the agent host | See [browser-mcp-providers.md](references/browser-mcp-providers.md); report **blocked**; do not claim verification passed |
| Dev server URL or way to start one | Infer from repo (see [dev-server.md](references/dev-server.md)); ask user if ambiguous |
| Acceptance criteria | Read from the ticket, `docs/jira/<TICKET>/implementation-plan.md`, the user message, or derive minimal checks from the change |

Optional: if a Figma URL exists for the story, run **figma-compare** after functional checks pass.

## Workflow

Copy and track progress:

```text
UI Verify:
- [ ] 1. Select browser MCP provider
- [ ] 2. Gather acceptance criteria
- [ ] 3. Ensure app is reachable (start dev server if needed)
- [ ] 4. Browser: navigate, exercise flows
- [ ] 5. Record evidence (snapshot + screenshot)
- [ ] 6. Write report; fix and re-run if failed
- [ ] 7. Only then declare work complete
```

### 1. Select browser MCP provider

1. Check the consumer repo's `docs/llm/` onboarding docs for a **Browser MCP** section; use that server if present.
2. Else discover available MCP servers and pick one that supports **navigate**, **snapshot**, **click**, and **screenshot** (see the capability table in [browser-mcp-providers.md](references/browser-mcp-providers.md)).
3. **Default when unspecified:** Playwright MCP (`@playwright/mcp`).
4. Read that server's tool schemas before the first call.

### 2. Gather acceptance criteria

Build a short checklist of **observable** behaviors (not code-level assertions):

- Happy path the user described (e.g. "click Save -> toast appears -> list updates")
- Edge cases called out in the ticket (empty state, error state, loading)
- Regression checks for adjacent UI if the change was broad

Save the checklist in the report under **Checks**.

### 3. Ensure the app is reachable

1. Read [dev-server.md](references/dev-server.md) for this repo's start command and default URL.
2. Check if something is already listening (e.g. `curl -s -o /dev/null -w "%{http_code}" http://localhost:3000`, or `Invoke-WebRequest` in PowerShell, or read active terminals).
3. If not running, start the dev server in the background from the project root; wait until HTTP responds.
4. Note auth requirements (login route, test user, env vars). If blocked, ask the user once with the exact steps needed; do not skip silently.

**Dev server lifecycle:** Leave a background dev server running after verification so the user can continue manual testing or a follow-up **figma-compare**. Do not stop it unless the user asks, the process is clearly orphaned from a prior session, or you need the port for a different command.

### 4. Browser session (browser MCP)

Follow [browser-workflow.md](references/browser-workflow.md).

Typical sequence (map to your provider's tool names):

1. Navigate to the target URL.
2. Snapshot; confirm structure and labels before interacting.
3. For each acceptance check: click, fill, type, select, scroll as needed; re-snapshot after state changes.
4. Screenshot the final state for the report (and for **figma-compare** if needed).
5. Close or leave the session per provider docs if cleanup is required.

Provider-specific notes:

- **Playwright MCP:** `browser_wait_for` for loading states; `browser_resize` for viewport; persistent auth via Playwright storage state if documented in onboarding.
- **cursor-ide-browser:** optional `browser_lock` / `browser_unlock`; omit `position` unless the user wants a visible browser.
- **Browserbase / hosted MCP:** use project credentials from onboarding; same capability mapping.

Rules:

- Do not repeat the same failing action without a new snapshot or hypothesis.
- Stop after four failed attempts and report the blocker.
- Do not substitute unrelated automation when the browser MCP is missing.

### 5. Pass / fail

| Result | Action |
|--------|--------|
| **Pass** (all checks behaved as expected) | Write report with status `pass`; suggest **figma-compare** if a design link exists; then **pre-pr-check** or **review** |
| **Fail** (wrong behavior, errors visible, blocked flow) | Fix the code, re-run this skill; do **not** tell the user the task is done |
| **Blocked** (needs credentials, API down, no browser MCP) | Report the blocker clearly; recommend Playwright MCP install for non-Cursor hosts |

### 6. Write report

Write **`docs/jira/<TICKET>/ui-verify-report.md`** when a ticket key exists (infer `<TICKET>` from the branch name or ask the user); otherwise write **`docs/jira/review/ui-verify-report.md`**. Create the directory if needed; do not write to hidden or gitignored directories.

```markdown
# UI Verify Report

**Status:** pass | fail | blocked
**Browser MCP:** playwright | cursor-ide-browser | browserbase | ...
**URL:** ...
**Date:** ...

## Checks

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | ... | pass/fail | ... |

## Evidence

- Screenshots: (describe what was captured)
- Blockers: (if any)

## Next steps

- (fix and re-verify | figma-compare | pre-pr-check)
```

Optionally mirror the status in `ui-verify-report.json` next to the Markdown report:

```json
{ "status": "pass", "browserMcp": "playwright", "url": "http://localhost:3000/...", "failedChecks": [] }
```

## Integration with other skills

| Skill | When |
|-------|------|
| **figma-compare** | Ticket or plan includes a Figma URL; run after functional pass |
| **pre-pr-check** / **review** | After UI verify (and optional figma-compare) pass |
| **fix** | If pre-pr-check finds issues after verify |
| **task-starter** | Plans should list `-> verify: ui-verify` on UI steps |
| **image-quality-inspection** | Screenshots that become report or wiki evidence must pass the image quality gate |

## Non-goals

- Do not replace unit/e2e tests; complement them with agent-driven smoke checks.
- Do not declare "done" based on code review alone when this skill applies.
- Do not require Cursor or cursor-ide-browser specifically.

## Reference

| File | Description |
|------|-------------|
| [browser-mcp-providers.md](references/browser-mcp-providers.md) | Playwright and other MCP setup; capability mapping |
| [dev-server.md](references/dev-server.md) | Detect start command and URL per stack |
| [browser-workflow.md](references/browser-workflow.md) | Interaction patterns and troubleshooting |
