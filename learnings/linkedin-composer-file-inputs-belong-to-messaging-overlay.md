---
title: LinkedIn attachment-input file inputs belong to messaging, not the post composer
category: security
created: 2026-10-07
tags: [linkedin, composer, messaging-overlay, file-input, hazard, scoping, browser-automation]
---

# Solution
- Create your own temporary `input` (`type=file`, distinct id), append it to the page, let the
  browser tool's upload fill it, then move the file onto the composer editor in the "Create post"
  dialog with a drop or paste event. Never use a pre-existing input (those belong to messaging).
- Remove the temporary input at the end, also on failure (`finally`).
- Never click Send or other messaging controls. After attaching, check the image shows in the
  Create post dialog, not a chat bubble. If it lands in a chat draft: remove that draft's
  attachment, confirm it is gone, tell the user, do not send.

# Why
A chat draft holding the file is one click from reaching another person.
