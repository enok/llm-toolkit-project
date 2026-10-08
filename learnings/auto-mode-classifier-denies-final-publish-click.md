---
title: The auto-mode classifier denied the final "Save and publish" click until the user's go named it
category: environment
created: 2026-10-07
tags: [auto-mode, permission-classifier, publish-click, medium, approval-gate, browser-automation]
---

# Problem

The user had approved the exact edit to a published Medium story, and the edit was in the
editor. The browser automation's auto-mode permission classifier then denied the final
"Save and publish" click. Approving the content did not count, for the classifier, as
approving the click.

# Failed Approaches

- Clicking "Save and publish" on the strength of the content approval alone: the click was
  denied.

# Solution

- Ask for a separate, explicit go that names the click, for example "click Save and publish
  on `<story title>` now". The same click went through after such a go.
- Or hand that one click to the user and wait for their confirmation.
- General guidance, not observed: do not work around the denial with another route to the same
  action; stop and ask. The skill already requires explicit approval of that exact action for
  every publish and every edit of a public story.

Durable guidance: skills/medium-publishing/SKILL.md (Known pitfalls) and
skills/medium-publishing/references/publish-dialog.md

# Why

The session observed the denial after content approval and the success after a go that named
the click. The classifier's rules are not documented in the session, so treat its behaviour as
observed, not as a specification. Inference: the classifier judges the action about to run,
not the earlier conversation, so the wording of the go has to match the action. This is the
same gate as `rules/external-write-authorization.md`, enforced a second time by the tool.
