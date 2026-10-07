---
title: LinkedIn attachment-input file inputs belong to messaging, not the post composer
category: security
created: 2026-10-07
tags: [linkedin, composer, messaging-overlay, file-input, hazard, scoping, browser-automation]
---

# Problem

While attaching an image to a LinkedIn post, the file was forwarded to an
`input[id^="attachment-input"]` element. That input belongs to the MESSAGING overlay, not
to the post composer, so the image attached to an open chat draft. It was removed unsent
with that draft's "remove attachment" button.

# Failed Approaches

- Forwarding the file to `input[id^="attachment-input"]`: it attached to a messaging
  draft instead of the post.

# Solution

- Scope every query to the "Create post" dialog. Never query the whole document for
  `input[type=file]` and use the first hit.
- Never forward a file to a pre-existing file input. Create your own temporary light-DOM
  input and use only that as the upload target (the working recipe then fills it with the
  browser tool's file upload and drops the file onto the composer editor):

```js
// Illustrative: the dialog scoping happens where you look up the composer editor.
const input = document.createElement('input');
input.type = 'file';
input.accept = 'image/png';
input.id = 'tmp-upload-proxy';
document.body.appendChild(input);
```

- Never click Send in messaging.
- If an attachment lands in a chat draft anyway: click that draft's "remove attachment"
  control so nothing is sent, confirm the draft no longer shows it, and tell the user.
- Remove the proxy input when done, also after a failed attempt.

Durable guidance: skills/linkedin-publishing/references/image-attach-recipe.md

# Why

The session recorded that these inputs belong to the messaging overlay; the composer
editor itself sits in a shadow DOM, which is a separate fact about the editor, not about
these inputs. Inference: a document-wide query for file inputs does not know which
dialog the user cares about, so it can return the messaging input. General guidance, not
observed in this session: a chat draft that holds an attachment is one click on Send away
from going to another person, which is why this is a security hazard and not only a
cosmetic bug.
