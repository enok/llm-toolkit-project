---
title: Change one link in a published Medium story with the toolbar link button, then read the anchor back
category: toolchain
created: 2026-10-07
tags: [medium, edit-published-story, link, toolbar, browser-automation, save-and-publish]
---

# Problem

A published Medium story held a link that had to point somewhere else (for example a
back-link to a new LinkedIn post). An earlier note in
`skills/medium-publishing/references/publish-dialog.md` says Ctrl+K on already linked text did
not open the link editor; the session that found the sequence below did not re-test it
(unverified here).

# Failed Approaches

None recorded in the session notes. (Earlier note, not re-tested: Ctrl+K on already linked
text did not open the link editor.)

# Solution

In the editor of the live story (Edit):

1. Select the link text.
2. Click the toolbar link button once: this removes the link.
3. Click the link button again: the "Paste or type a link" field opens.
4. Type the new URL and press Enter.
5. Read the anchor back from the DOM: its text, its new `href`, and that no anchor with the
   old URL remains:

```js
(async () => {
  const root = document.querySelector('article') || document.body;
  return [...root.querySelectorAll('a')].map(a => ({ text: a.textContent.trim(), href: a.href }));
})()
```

6. Get the user's approval of the exact change, then "Save and publish", and verify on the
   post-redirect page, not a cached fetch (`skills/medium-publishing/references/publish-dialog.md`).

Durable guidance: skills/medium-publishing/references/publish-dialog.md

# Why

The session recorded the working click sequence (one click removes the existing link, the
second opens the field) and that the anchor was read back afterwards. It did not test Ctrl+K
again and did not record how the text was selected. The last click of the
flow, "Save and publish", can be denied by the browser tool's classifier unless the user's go
names it (learnings/auto-mode-classifier-denies-final-publish-click.md).
