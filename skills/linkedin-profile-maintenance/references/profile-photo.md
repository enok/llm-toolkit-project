---
title: Replacing the profile photo
tags: [linkedin, profile-photo, browser-automation, file-upload, rollback]
---

# Replacing the profile photo

Use when the owner asks to change the profile photo. It is an external write on
a public profile: get the owner's go on the exact image first.

1. **Use the owner's own signed-in Chrome**, not an in-app browser that is
   signed out. Check sign-in first; do not wait on a login that will not
   happen (`browser-session-notes.md`).
2. **Record a rollback.** Before replacing, save the link to the current photo
   so the owner can restore it.
3. **Attach the file to the hidden file input.** The native file picker cannot
   be driven. Open the upload dialog, catch the hidden `input[type=file]` it
   creates and attach the file to it, the same technique as
   `skills/linkedin-publishing/references/image-attach-recipe.md`.
4. **Upload the full-resolution source.** Confirm the crop-circle framing shows
   the face and shoulders as intended before saving.
5. **Verify.** Save, reload the page, and confirm the new photo and its
   visibility setting. Report the rollback link.

A HEIC source from a phone with no decoder available:
`skills/image-quality-inspection/references/heic-without-decoder.md`. Rank
several candidate photos on a contact sheet first
(`skills/image-quality-inspection/references/image-quality-gate.md`).
