---
title: Medium topic autocomplete adds the first suggestion instead of the typed topic
category: toolchain
created: 2026-10-07
tags: [medium, publish-dialog, topics, autocomplete, dom-click, browser-automation]
---

# Problem

In the Medium publish dialog (up to 5 topics), typing a topic and pressing Enter added
the first autocomplete suggestion, not the typed text. Typing "Java" added "JavaScript".

# Failed Approaches

- Pressing Enter after typing the topic: the FIRST suggestion was added (the wrong one).
- Clicking a suggestion with the mouse: the dropdown closed without adding anything.

# Solution

Type the topic without pressing Enter, wait for the suggestions, then dispatch a DOM
click on the suggestion button whose text equals the topic exactly (trimmed, case
insensitive). If there is no exact match, stop and ask the user for another topic; never
fall back to the first suggestion. Afterwards read the topic chips back and compare them
with the intended list; if a wrong chip appeared, remove it with its close control and
retry.

The selectors below are illustrative: inspect the live dialog (accessibility tree or an
element finder) for the real ones.

```js
const want = 'Java';
const options = [...document.querySelectorAll('[role="option"], li button, button')]
  .filter(b => b.offsetParent !== null);
const hit = options.find(b => b.textContent.trim().toLowerCase() === want.toLowerCase());
if (!hit) throw new Error('no exact suggestion for ' + want + ': ' +
  options.slice(0, 8).map(b => b.textContent.trim()).join(' | '));
hit.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
```

Equality, not a substring test, is what keeps "Java" from matching "JavaScript".
Clicking Publish itself still needs the user's explicit approval of that exact action.

Durable guidance: skills/medium-publishing/references/publish-dialog.md

# Why

The session observed three behaviours: Enter takes the first suggestion regardless of
the typed text, a mouse click closes the dropdown without adding, and a DOM click on the
exact suggestion button adds it. It did not establish why they differ (inference: the
dropdown handles real pointer and keyboard input differently from a dispatched click
event). So treat the suggestion list as untrusted input: match exactly, then verify the
chips.
