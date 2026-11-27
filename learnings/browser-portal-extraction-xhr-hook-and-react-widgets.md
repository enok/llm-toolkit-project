---
title: Extracting data from a logged-in web portal with browser tools - XHR hook, real keystrokes, React widgets
category: toolchain
created: 2026-11-26
tags: [claude-in-chrome, javascript_tool, xhr, fetch-hook, react, get_page_text, localstorage, login, virtualized-list]
---

# Problem
Reading many records out of a logged-in web portal (and exporting a long chat history) with
browser automation tools was slow and error-prone: the agent cannot log in, forms ignored
scripted input, dropdowns would not open, and large results did not come back through the tool.

# Failed Approaches
- Logging in for the user or guessing credentials: not allowed and not possible; the agent
  has to wait for the user.
- Scraping rendered tables cell by cell: slow, and the layout changed between iterations.
- Setting `input.value` and expecting the framework to notice: React-style inputs ignore it.
- Clicking a custom dropdown with a single `click` event: the widget listens for the pointer
  sequence and stayed closed.
- Returning a very large string directly from `javascript_tool`: the output was truncated.

# Solution
- **Login:** ask the user to log in on the open tab and reply with a keyword; optionally
  schedule a `send_later` nudge. Each scan iteration, verify the active account or plan text on
  the page first, because a portal can silently switch context or expire the session.
- **Capture:** hook `XMLHttpRequest` and `fetch` through `javascript_tool`, let the page make
  its own calls, and keep the responses whose URL matches. Flat JSON from the hook beats DOM
  scraping.
- **Input:** use real keystrokes (triple click, `ctrl+a`, type) for fields. Where a field drops
  characters (for example under a grammar extension), set the value with the native setter,
  dispatch an `input` event, then read the value back.
- **React dropdowns:** dispatch `pointerdown`, `mousedown`, `pointerup`, `mouseup`, `click` in
  that order.
- **Big results:** write the text into a temporary DOM node, read it with `get_page_text`, then
  remove the node.
- **Long scans:** persist partial state in `localStorage` so a reload resumes instead of
  restarting.
- **Virtualized lists** (a chat with lazy rendering): wheel-scroll and harvest the DOM per
  channel or section, de-duplicating by message id.
- **Delivery:** commit files to the user's device with a new file name per revision.

# Why
The page's own network calls already contain structured data, so intercepting them avoids
parsing presentation. Frameworks track input through events and their own state, so only real
or fully dispatched events change it. The agent cannot authenticate for the user, so the
hand-off and the per-iteration account check are the safe path. Untested: portals that sign
requests per call or use WebSockets for data.
