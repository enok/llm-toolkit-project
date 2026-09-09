---
name: figma-compare
description: Compare implemented UI in the browser against a Figma mockup. Fetches design context via a Figma MCP server, captures live app screenshots, and reports layout, content, and visual mismatches. Use when a ticket or plan includes a Figma link, when the user asks to match the design, or after ui-verify when a mockup exists.
license: MIT
---

# Figma Compare

Compare **what is built in the browser** to **what Figma specifies**, so the user does not have to check side by side manually. Run after **ui-verify** passes: functional first, visual second.

## When to Apply

- A ticket, implementation plan, or user message includes a Figma URL.
- The user says "match the mockup", "compare to Figma", or "does this look like the design".
- **ui-verify** passed and a design link was noted in context.

Skip when there is no Figma reference or the user says design comparison is out of scope.

## Prerequisites

| Requirement | If missing |
|-------------|------------|
| Figma URL (file plus node when possible) | Ask the user once; extract it from the ticket via **task-starter** context |
| **ui-verify** result or a live app URL | Run **ui-verify** first or confirm the URL |
| Figma MCP authenticated | Complete the Figma MCP server's auth flow if tools fail; tell the user what is needed |
| Browser screenshot of the implementation | From **ui-verify**, or the screenshot tool on the same browser MCP used for verify |

## Workflow

Copy and track progress:

```text
Figma Compare:
- [ ] 1. Parse the Figma URL (file key, node id)
- [ ] 2. Fetch design context from the Figma MCP server
- [ ] 3. Capture the implementation screenshot (matching viewport)
- [ ] 4. Compare dimensions, structure, copy, states
- [ ] 5. Write the report; fix and re-run if critical mismatches exist
```

### 1. Parse the Figma URL

From URLs like `https://www.figma.com/design/<fileKey>/...?node-id=1-234`:

- **fileKey** is the design file identifier.
- **node-id** may need converting from `1-234` to `1:234` for MCP calls.

If only a file link is given, ask which frame or screen to compare, or pick the frame named in the ticket.

### 2. Fetch the design from Figma

**Read the Figma MCP tool schemas before calling.** Tool names vary by server and version; common examples:

- `get_design_context` for layout, typography, colors, and component names for a node
- `get_screenshot` for an export of the Figma frame for visual comparison
- `get_metadata` for the node tree when you need to confirm the right frame

If your host exposes a Figma plugin workflow (for example a `figma-use`-style skill), load it before making plugin calls.

Extract from the design context:

- Viewport width (mobile, tablet, or desktop breakpoint)
- Key text labels and hierarchy
- Primary colors, spacing, alignment (auto-layout direction, gaps)
- Component variants (default, hover, error, empty)
- Icon and imagery placement

### 3. Capture the implementation

1. Set the browser viewport to match the Figma breakpoint when possible (`browser_resize` on Playwright MCP, the provider-specific resize, or CDP if available).
2. Navigate to the same **route and state** as the mockup (empty list versus populated, error versus success).
3. Capture a screenshot via the browser MCP screenshot tool: the full frame of the compared region.

Use the same theme (light or dark) as the Figma frame unless the ticket says otherwise.

### 4. Compare

Evaluate in this order, critical to cosmetic:

| Severity | Examples |
|----------|----------|
| **Critical** | Missing primary action, wrong flow state, unreadable contrast, broken layout overlap |
| **Major** | Wrong copy, missing section, incorrect component variant, large spacing or alignment drift |
| **Minor** | 4px spacing delta, font weight off by one step, icon style mismatch |

Compare:

- **Structure**: sections present, order, hierarchy (headings, groups)
- **Content**: strings, placeholders, CTA labels
- **Layout**: alignment, padding, width constraints, responsive behavior
- **Visual**: color tokens, border radius, shadows (allow token naming differences if visually equivalent)

Do not fail on pixel-perfect sub-2px differences unless the design system requires it.

**Limitations:** comparison is **agent judgment** on screenshots and Figma context, not an automated pixel diff. Font rendering, anti-aliasing, and dynamic content may differ slightly, so focus on structure, copy, and token-level visual intent. Document uncertainty as minor rather than inventing false precision.

### 5. Report and loop

Write **`docs/jira/<TICKET>/figma-compare-report.md`** when a ticket key exists (infer `<TICKET>` from the branch name or ask the user); otherwise write **`docs/jira/review/figma-compare-report.md`**. Create the directory if needed; do not write to hidden or gitignored directories.

```markdown
# Figma Compare Report

**Status:** pass | fail | blocked
**Figma:** <url>
**App URL:** ...
**Viewport:** ...

## Summary

One paragraph: overall match quality.

## Findings

| Severity | Area | Figma | Implementation | Suggested fix |
|----------|------|-------|----------------|---------------|
| major | Header CTA | "Save draft" | "Save" | Update the button label in ... |

## Evidence

- Figma: (reference frame name or screenshot)
- App: (screenshot description)

## Next steps

- (fix CSS/component | re-run figma-compare | accept minor deltas as a user decision)
```

**Pass:** no critical or major findings (minor items listed as optional follow-ups).

**Fail:** fix the implementation, then re-run **figma-compare** (and **ui-verify** if behavior changed).

**Blocked:** Figma auth, wrong node, or design file access; ask the user to share the link or grant access.

## Integration

| Skill | When |
|-------|------|
| **ui-verify** | Always run first; figma-compare is visual QA on a functionally verified build |
| **task-starter** | Plans with Figma links should end with `-> verify: ui-verify then figma-compare` |
| **image-quality-inspection** | Screenshots and Figma exports used as report or wiki evidence must pass the image quality gate |
| **pre-pr-check** / **review** | After figma-compare passes or the user accepts documented deltas |

Do not mark the story done on a **figma-compare** fail unless the user accepts the documented deltas.

## Reference

| File | Description |
|------|-------------|
| [comparison-checklist.md](references/comparison-checklist.md) | Structured pass/fail criteria |
