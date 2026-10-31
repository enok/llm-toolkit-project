---
title: LinkedIn experience Highlights is a contenteditable editor, project descriptions are plain textareas
category: environment
created: 2026-10-31
tags: [linkedin, browser-automation, contenteditable, textarea, react, input-event, rich-text, range]
---

# Problem

Editing text in a LinkedIn experience entry's Highlights/description and in a project
description needs a method that fits each field type. The experience Highlights field is a
contenteditable rich-text editor (one `<p>` per line), not a textarea; project descriptions
are plain textareas.

# Failed Approaches

- None recorded: the session used the two recipes below. Untested inference, not observed:
  assigning `.value` or `.innerText` on the Highlights field would not update the editor,
  because it is not a form control.

# Solution

- Highlights/description (experience): a contenteditable rich-text editor with one `<p>`
  per line. Place the caret with a DOM `Range` at the end of the target line's last text
  node, set the selection, then type with real key events.
- Project descriptions: plain `textarea`. Check that the exact old substring occurs once,
  set the value with the native `HTMLTextAreaElement` value setter, then dispatch an `input`
  event.
- Read the field back after the change and compare it with the intended text.

Durable guidance: skills/linkedin-profile-maintenance/references/details-pages.md

# Why

Observed: the two field types and the two recipes that worked. Untested inference: the form
is a React front end that keeps its own state, so only events a user would produce (key
events in a contenteditable, an `input` event after the native setter on a textarea) reach
it. Markup and field types can change, so inspect the element type first and read the result
back every time.
