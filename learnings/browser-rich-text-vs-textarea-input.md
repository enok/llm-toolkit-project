---
title: Rich-text fields reject form-input helpers and plain textareas drop typed characters
category: toolchain
created: 2026-10-22
tags: [browser, automation, contenteditable, textarea, form-input, typing, verification]
---

# Problem

Two opposite input failures on the same site:

- Setting the value of a rich-text (contenteditable) editor with a form-input
  helper fails with "element type DIV is not a supported form input".
- Typing a paragraph into a plain textarea silently dropped characters
  ("over17", "engineerng", "projectdelivery"), producing a subtly wrong save. A
  grammar-checking browser extension on the page is one known cause of the drops.

# Failed Approaches

- Using the same method for both field types.
- Trusting the typing action's "typed" message without looking at the field.

# Solution

- Contenteditable editors: scroll to the field, click it, select all, delete,
  then type. Zoom on the field and check the character counter afterwards.
- Plain textareas and inputs: set the value with the form-input helper, then
  verify visually.
- Typeahead fields: type, wait two to three seconds, click the suggestion. If no
  suggestion list appears, wait once more and re-type the last character before clicking.
- If typing still drops characters, set the value through the native value setter
  (`Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set`), dispatch
  an `input` event so the framework sees it, and read the value back.
- Always read the saved value back; long typed text is the likeliest to corrupt.

# Related

- `learnings/linkedin-highlights-editor-is-contenteditable.md`: the same split on a
  LinkedIn profile form.
- `learnings/browser-portal-extraction-xhr-hook-and-react-widgets.md`: real keystrokes and
  pointer events for framework-controlled inputs and dropdowns.

# Why

Rich editors keep state in the DOM tree rather than a value property, while
long synthetic typing into a busy page can lose key events.
