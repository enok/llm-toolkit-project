---
title: LinkedIn delete dialogs must be verified against the item name before every confirm
category: environment
created: 2026-10-31
tags: [linkedin, browser-automation, delete, confirm-dialog, bulk-edit, safety, endorsements, backup]
---

# Problem

A bulk delete of profile items (skills, certifications, courses) goes through each item's
edit dialog. Deleting is irreversible, and deleting a skill drops its endorsements for good.
Clicking several edit links without waiting for each dialog stacked the dialogs, and the
confirm text named a different item than the one intended.

# Failed Approaches

- Clicking several edit links without waiting for each dialog to settle: the dialogs stacked
  and the confirm text named a different item.
- Relying on the confirm dialog alone to catch a mismatch: the skills confirm dialog does not
  repeat the skill name (certification and course confirm dialogs do).

# Solution

- Write a backup file first (names, issuers, issue dates, credential IDs, endorsement
  counts) and tell the owner which skills carry endorsements that will be lost.
- Work one item at a time: open the item's edit dialog and read its heading; it must be
  exactly "Edit <item name>" for the item on the approved delete list. On any mismatch,
  close the dialog and stop.
- Click "Delete <section item>", then read the confirm dialog. Certification and course
  confirm dialogs repeat the name ("Delete <name>? This action cannot be undone."): compare
  it and cancel on mismatch. The skills confirm dialog carries no name, so the edit heading
  check is the only guard there.
- Re-read the section after each delete and tick the item off the approved list.

Durable guidance: skills/linkedin-profile-maintenance/SKILL.md (hard rules)

# Why

Observed: stacked dialogs produced a confirm that named a different item, and the confirm
dialogs differ (skills omit the name, certifications and courses include it). Why the dialogs
stacked was not investigated. A heading check immediately before the confirm ties the click to
the right item whichever dialog is on top. The backup makes a delete recoverable, except for
endorsements, which no backup restores.
