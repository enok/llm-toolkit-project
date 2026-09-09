---
title: Confluence page archive is UI-only; verify via readback status
category: api
created: 2026-08-19
tags: [confluence, archive, mcp, ui-only, verification, rollback, browser-fallback]
---

# Problem

A superseded Confluence page (its content merged into a canonical page) needed
to be archived. No available API or MCP surface could perform the archive, yet
the operation still had to be verified and rollback-documented like any other
mutation.

# Failed Approaches

- The Atlassian remote MCP toolset: no archive operation exists for pages (the
  same limitation as for folders), and `updateConfluencePage` cannot set
  `status`.
- Browser-extension automation: the extension was not connected
  (`list_connected_browsers` returned empty).
- The in-app browser: Atlassian redirected to the identity provider's login
  page, and entering credentials is prohibited, so automation stopped there.

# Solution

Treat archive as a status-only mutation with a human-executed step:

1. Upload a lightweight rollback snapshot (page id, title, version, parent,
   restore instructions) to the approved backup location and hash-verify it. No
   full body export is needed if a verified body backup already exists, because
   archive does not touch body, version history, labels, comments, or
   attachments.
2. Hand the user the exact click path (page -> `...` more actions -> Archive ->
   confirm) instead of blocking the run.
3. Verify completion via API readback: `getConfluencePage` on the page id
   returns `status: "archived"` (read access to archived pages keeps working).
4. Record the rollback: UI Restore from the space's archived pages returns the
   page under its previous parent, so archive is fully non-destructive.

# Why

Confluence Cloud exposes archive only in the UI for this MCP surface (a v1 REST
bulk-archive endpoint exists but needs an authenticated REST client that
MCP-only sessions do not have). Because archive changes only the content status,
the pre-mutation backup burden is far lighter than for body or hierarchy
mutations — reference the existing body backups plus native version history, and
let an API readback of the `status` field serve as completion evidence for a
step a human performed.
