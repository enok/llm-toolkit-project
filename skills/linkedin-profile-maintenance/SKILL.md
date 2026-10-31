---
name: linkedin-profile-maintenance
description: Use when the owner says "remove these from my LinkedIn profile" or "update my LinkedIn skills/certifications/experience", or asks to clean up, correct, or update their own LinkedIn profile through browser automation in their already-signed-in browser - bulk-delete skills, certifications, or courses against a keep-list, add skills or projects, change an experience end date or highlights - with inventory, backup, owner-approved edit list, per-item verification, and a final re-read. Not for posting (use linkedin-publishing) or for rewriting the CV.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# LinkedIn profile maintenance

Safe, owner-approved bulk maintenance of the owner's own LinkedIn profile by
driving the owner's signed-in browser. Everything personal (handle, keep-list,
target facts, dates) comes from the owner's request and files, never from this
skill. The profile is an external, public record: every edit is an external
write, and deletes cannot be undone.

- Details-page mechanics, URL patterns, inventory, editors and forms:
  `references/details-pages.md`.
- Browser and session constraints (tool output limits, bot checks, which
  browser is signed in): `references/browser-session-notes.md`.
- Posts and reposts are a different job: `skills/linkedin-publishing/SKILL.md`.
- Keeping the CV and job-search files consistent with the profile afterwards:
  `workflows/career-profile-sync.md`.

## Contract

1. **Owner's profile, owner's session.** Authentication belongs to the owner.
   Do not sign in, do not enter passwords or codes, and never pass a bot check.
   If the tab is signed out or a verification page appears, stop and hand that
   step to the owner (`references/browser-session-notes.md`).
2. **Approval binds to an exact list.** Follow
   `rules/external-write-authorization.md`: the owner approves named items and
   named actions; anything outside the list needs fresh approval.
3. **One writer.** The root owns the browser tab and every write. Other lanes
   are read-only (evidence mining, comparing files); two agents never drive the
   same profile at once.
4. **Fixed order.** Inventory, backup, owner keep-list or approval, edits one
   item at a time with verification, re-read, report. Do not reorder or merge
   phases, and never report done before the re-read.

## Procedure

1. **Scope.** Name the sections in play (skills, licenses and certifications,
   courses, projects, experience, education) and the action per section
   (delete, add, correct), plus the owner's keep-list or target facts.
2. **Mine evidence before asking.** A public profile's Projects section often
   holds the richest facts (per-project dates, task lists, links). Read it, the
   experience entries, and the CV or master CV the owner points to before asking
   the owner for a fact. Propose what you found as a list; invent nothing.
3. **Inventory every place an item can live.** Scroll each details page to the
   end and record each item's name and edit-form URL
   (`references/details-pages.md`). A course or certification can sit in three
   places, so inventory all three before computing any delete set.
4. **Backup first.** Before the first delete or edit, write a backup to the
   owner's working folder as a markdown table: name, issuer/org, dates,
   credential ID, endorsement count, and decision (keep, delete, edit), plus the
   current text of every field to be edited. Tell the owner which skills carry
   endorsements, because deleting a skill drops them permanently.
5. **Present the delta and wait.** Delete set = inventory minus keep-list, plus
   adds and edits, every item named, in a plain message of its own. Flag
   ambiguous items (a degree recorded as a certification, one item listed in
   two sections) instead of deciding them. Proceed only on the owner's go.
6. **Execute one item at a time** under the hard rules below, ticking each item
   off the approved list as it is verified.
7. **Re-read.** Reopen the list and compare count and names with the expected
   result; read every edited field back; for an experience date re-read the
   details line. Mismatches are reported, not smoothed over.
8. **Report** done, skipped, and mismatched items, where the backup is, and what
   waits on the owner. If the CV or other files quote the same facts, continue
   with `workflows/career-profile-sync.md`.

## Hard rules

- **Delete safety.** Open the item's edit dialog and read its heading: it must
  be exactly "Edit <item name>" for an item on the approved list. Then click
  "Delete <section item>" and read the confirm dialog. Certification and course
  confirm dialogs repeat the name ("Delete <name>? This action cannot be
  undone."): compare it and cancel on mismatch. The skills confirm dialog does
  not repeat the name, so the heading check is its only guard. Wait for each
  dialog to settle; clicking several edit links in a row stacks dialogs and a
  confirm can belong to another item.
- **Backup and endorsements.** No delete without the backup file from step 4.
- **Late discoveries need fresh approval.** Items that appear after the owner
  approved the list (more entries loaded on scroll, a degree recorded as a
  certification) are not covered by it. Present them and ask: the auto-mode
  permission classifier blocked a batch delete of such items.
- **Experience end date.** In the role's edit form untick "I am currently
  working in this role", then set the End month and End year selects (form input
  works on these React selects). Confirm "Notify network" is off before saving.
  Re-read the details page: the entry shows the start, the end, and the duration.
- **Adding a skill.** Tick the roles or projects that evidence it and untick
  "Follow this skill" unless the owner asked; re-read the skills list afterwards
  (`references/details-pages.md`, section 4).

## Known pitfalls

- Collect every edit-form URL before the first delete; lists re-render after a
  delete. See `learnings/linkedin-details-pages-lazy-load-in-main-container.md`.
  (sig: platform-quirk/linkedin-details-pages-lazy-load)
- Check the edit heading before each confirm, one dialog at a time. See
  `learnings/linkedin-delete-dialogs-verify-item-name.md`.
  (sig: safety-near-miss/linkedin-delete-dialog-name-check)
- Highlights is a contenteditable editor, project descriptions are textareas. See
  `learnings/linkedin-highlights-editor-is-contenteditable.md`.
  (sig: platform-quirk/linkedin-highlights-contenteditable)
- Get a go that names the final click, or hand that click to the owner. See
  `learnings/auto-mode-classifier-denies-final-publish-click.md`.
  (sig: env-constraint/auto-mode-denies-publish-click)
