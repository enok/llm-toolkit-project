---
title: Browser session notes for profile automation
tags: [browser-automation, javascript-tool, bot-check, signed-in-session, chrome-extension, linkedin]
---

# Browser session notes

Constraints of the browser tools that shaped the procedure in `SKILL.md`. They
describe observed behaviour of the tools in one set-up; re-check them before
relying on a limit or a workaround.

## 1. The JavaScript tool truncates results

A returned value was cut off at roughly 1 KB. Do not return an inventory
directly.

- Keep the data in a window variable (`window.__inventory = [...]`) and read it
  in slices (`JSON.stringify(window.__inventory.slice(0, 15))`).
- Or render the data into a `<pre>` element and read the page text with the
  page-text tool.
- Read the count first, then the slices, so you know when you have everything.

## 2. Bot checks are never passed

A verification interstitial ("Just a moment..." or "Performing security
verification") means the site wants a human. Never bypass it, retry it in a
loop, or look for another route past it.

- The tab's renderer can also freeze while such a page is up: script evaluation
  calls time out.
- Close that tab and hand the step to the owner: say which page and which step
  was reached, and what remains.

## 3. Use the browser that is already signed in

The desktop app's built-in browser keeps its own profile and may not be signed in
to a site the owner uses every day. When the owner's signed-in session is
needed, use the Chrome extension attached to the owner's own browser.

- The agent never signs in, never types a password or a code, and never asks for
  one in chat. If the page shows a sign-in form, stop and ask the owner to sign
  in themselves, or to connect the signed-in browser.
- Open work in a new tab and leave the owner's other tabs alone.

## 4. Pacing

- Wait for each dialog or page to settle before the next action; stacked dialogs
  were the cause of a mis-targeted confirm (`SKILL.md`, delete safety).
- One mutation at a time, each followed by its read-back. A batch that fails
  half-way is easier to reconcile when the last verified item is known.
