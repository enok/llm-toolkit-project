---
title: Browser MCP providers
tags: [ui-verify, browser, mcp, playwright]
---

# Browser MCP providers

**ui-verify** is **not tied to any single IDE**. It uses whichever browser MCP server the agent host exposes. Tool names often overlap across providers; always read that server's tool schemas before calling.

## Recommended default (non-Cursor)

**Playwright MCP** (`@playwright/mcp`) is an official Microsoft server and works in Claude Code, Windsurf, VS Code, Claude Desktop, and other MCP clients.

```json
{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}
```

Install browsers once with `npx playwright install`. See the [Playwright MCP docs](https://playwright.dev/docs/getting-started-mcp).

## Provider comparison

| Provider | Package / server id | Best for | Notes |
|----------|---------------------|----------|-------|
| **Playwright MCP** | `@playwright/mcp` | Default for local automation | Snapshot + ref model; 40+ tools; cross-browser |
| **cursor-ide-browser** | Cursor built-in | Cursor IDE only | CDP access; tab lock/unlock |
| **Browserbase MCP** | `@browserbasehq/mcp-server-browserbase` | Cloud/hosted browsers | No local browser install |
| **Browser Use MCP** | browser-use | Long sessions, saved profiles | Good for auth-heavy flows |
| **Chrome DevTools MCP** | chrome-devtools-mcp | Debugging, performance, console | Narrower; pair with Playwright for flows |

Pick **one primary** browser MCP per project. Document the choice in the consumer repo's `docs/llm/` onboarding docs under **Browser MCP**.

## Capability mapping

Map **capabilities** (what ui-verify needs) to whatever tools your server exposes:

| Capability | Typical tool names | Required? |
|------------|-------------------|-----------|
| Navigate to URL | `browser_navigate`, `navigate`, `goto` | Yes |
| Page structure for interactions | `browser_snapshot`, `snapshot`, accessibility tree | Yes |
| Click | `browser_click`, `click` | Yes |
| Type / fill | `browser_type`, `browser_fill`, `browser_fill_form`, `fill` | Yes |
| Select option | `browser_select_option`, `select_option` | If forms use `<select>` |
| Scroll | `browser_scroll`, `scroll` | Often helpful |
| Screenshot | `browser_take_screenshot`, `screenshot` | Yes (evidence + figma-compare) |
| Wait for UI | `browser_wait_for`, `wait_for` | Recommended |
| Resize viewport | `browser_resize`, `resize` | For responsive checks and figma-compare |
| Run script | `browser_evaluate`, CDP evaluate | Optional fallback; prefer snapshot/click/fill and use script evaluation only when no supported interaction tool can reach the element |
| Tab management | `browser_tabs`, `browser_close` | Optional |
| Session lock | `browser_lock` / `browser_unlock` | Provider-specific; skip if absent |

When tool names differ, read schemas via the host's MCP discovery (for example, list the tools on that server) and note the mapping in the verify report under **Browser MCP**.

## Project configuration (consumer repo)

Optional block in the consumer repo's `docs/llm/` onboarding docs:

```markdown
## Browser MCP

- **Server:** playwright (or browserbase, cursor-ide-browser, ...)
- **Config:** path to the mcp.json snippet or env notes
- **Headless:** true | false
- **Default viewport:** 1440x900
- **Auth:** login URL, test user (never commit passwords; use env var names)
```

If this section exists, the agent uses that server first.

## When no browser MCP is available

1. Report status **blocked** in `docs/jira/<TICKET>/ui-verify-report.md` (or `docs/jira/review/ui-verify-report.md` when there is no ticket).
2. Tell the user which MCP to install (recommend Playwright MCP for non-Cursor hosts).
3. Do **not** claim verification passed.
4. Optional: suggest adding a Playwright smoke test the agent can run via `npx playwright test` if the repo already has Playwright. That is a fallback, not a substitute for MCP when MCP is expected.
