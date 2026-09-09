---
title: Browser MCP workflow
tags: [ui-verify, browser, mcp]
---

# Browser MCP workflow

Provider-agnostic patterns for UI verification. See [browser-mcp-providers.md](browser-mcp-providers.md) for setup and server choice.

## Before interacting

1. **Discover tools**: list MCP servers and find one with navigate + snapshot + click (see the capability table in the providers doc).
2. **Read schemas**: tool names and parameters vary by server; never assume host-specific fields (for example `position` or `viewId`) exist elsewhere.
3. **Prefer project config**: the **Browser MCP** section in the consumer repo's `docs/llm/` onboarding docs overrides defaults.

## Interaction pattern

```text
navigate -> snapshot -> [click / fill / type / select] -> snapshot -> ... -> screenshot
```

Optional: **lock** the tab or session if the provider supports it; otherwise rely on a single tab/window for the whole verify run.

### Element targeting

Most snapshot-based MCP servers return **refs** on interactive nodes:

- Always take a **fresh snapshot** after navigation or a state change.
- Click and fill using refs from the **latest** snapshot; stale refs fail silently or mis-click.
- If the server uses CSS selectors instead of refs, prefer stable selectors (`data-testid`, roles, labels).

### Waiting

Avoid long blind sleeps. Prefer, in order:

1. The provider **wait** tool (`browser_wait_for`, wait for text/selector).
2. Re-snapshot until the expected text or control appears.
3. Short polls (1-2s) with a snapshot between attempts.
4. Script evaluation (if available) for `document.querySelector` or network idle.

Stop after **four** failed attempts on the same step and report the blocker with the last snapshot excerpt.

## Evidence for reports

Capture at minimum:

1. A snapshot excerpt proving key structure or copy (paste it into the report table notes).
2. A screenshot of the success state (`browser_take_screenshot` or equivalent).
3. On failure: a screenshot or snapshot showing actual versus expected.

Record **which MCP server** was used in the report header. Screenshots that become report or wiki evidence must pass the `image-quality-inspection` gate.

## Common blockers

| Symptom | Likely cause |
|---------|--------------|
| No browser tools in the MCP catalog | Server not configured; see the providers doc |
| Blank page | Wrong port, server not ready, JS error; check the terminal and snapshot |
| Element not found | Wrong route, auth wall, lazy load; scroll, wait, or navigate |
| Click has no effect | Overlay, disabled control, stale ref; take a fresh snapshot |
| Headless-only CI host | Use Playwright MCP headless or a hosted browser MCP; document it in onboarding |

## Parallel with Figma

When **figma-compare** runs next, capture a **full-viewport screenshot** at the Figma breakpoint. Use `browser_resize` (Playwright) or the provider equivalent; not all servers expose CDP emulation.
