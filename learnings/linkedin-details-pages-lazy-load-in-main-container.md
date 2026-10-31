---
title: LinkedIn details pages lazy-load inside the main container and re-render after a delete
category: environment
created: 2026-10-31
tags: [linkedin, browser-automation, lazy-load, details-page, scroll-container, bulk-edit, edit-form-url]
---

# Problem

A bulk clean-up of a long LinkedIn section (skills, certifications, courses, projects,
experience) was driven from the section's "details" page. The page lazy-loads its items
inside its own `main` scroll container, not the window, and after any delete the list
re-renders to roughly its first 50 items, so later items vanish from the DOM.

# Failed Approaches

- Scrolling the window to load more items: the items load as the `main` container scrolls.
- Working through the list by position after a delete: the list had re-rendered to about its
  first 50 items, so later items were no longer in the DOM.

# Solution

- Scroll the details page's `main` scroll container (not the window) until the item count
  stops growing, then record every item's name and its edit-form URL
  (`/in/<handle>/details/<section>/edit/forms/<id>/`) before the first delete.
- Open each item by its edit-form URL instead of by clicking its position in the list; the
  URL does not depend on what is currently rendered.
- After every delete, re-read the list rather than assuming the remaining items kept
  their positions, and reload the inventory when the count looks lower than expected.

Durable guidance: skills/linkedin-profile-maintenance/references/details-pages.md

# Why

Observed: the details pages load items lazily as their own `main` container scrolls, and
after a delete the list re-rendered to about the first 50 items, dropping later ones from
the DOM. Inference: the front end renders a window of the list and rebuilds it on mutation,
so DOM position is not a stable identifier. The edit-form id is, which is why collecting the
URLs first removes the dependency on scroll state. The exact page size and container
selector may change; verify them before relying on either.
