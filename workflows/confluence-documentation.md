---
description: Create, read, update, delete, move, label, comment, and manage Confluence documentation safely
---

# Confluence Documentation Workflow

Use this workflow for Confluence documentation CRUD and synchronization.

## Phase 1 — Scope and authority

1. Identify the requested operation: create, read, update, delete, move, label, comment, or attachment management.
2. Confirm whether the repository, Confluence, or another system is the source of truth.
3. For writes, identify target space, parent page, title, labels, and intended audience.
4. For destructive operations, stop and get explicit user confirmation before proceeding.

## Phase 2 — Discover existing content

1. Search Confluence using focused terms or CQL.
2. Read the relevant page before updating, moving, deleting, or commenting.
3. Check child pages, labels, comments, attachments, or versions when they affect the operation.
4. Record page ID, title, space, parent, URL, and why it is relevant.

## Phase 3 — Prepare the change

1. Draft content in Markdown unless the destination requires another format.
2. Keep names, links, and diagrams evidence-based; verify against source code, repo docs, or existing Confluence pages.
3. Avoid secrets, tokens, PII, internal-only hostnames, customer-specific details, branch names, and one-off ticket names unless the destination is explicitly approved.
4. Preserve useful existing sections and minimize unrelated rewrites.

## Phase 4 — Apply the operation

| Operation | Action |
| --- | --- |
| Create | Create under the confirmed parent page or space; add labels; verify rendered page. |
| Read | Summarize content with page URL and relevance; do not mutate anything. |
| Update | Update only the intended page; include a clear version comment when supported. |
| Delete | Verify page ID/title and child/attachment impact; delete only after explicit approval. |
| Move | Verify current and target hierarchy; move; re-read children/hierarchy after move. |
| Label/comment | Read existing labels/comments first; add the minimal intended label/comment. |
| Attachments | List attachments first; upload/update/delete only confirmed files. |

## Phase 5 — Verify and link

1. Re-read or inspect the page after mutation.
2. Confirm hierarchy, labels, comments, attachments, and rendered content.
3. Link Confluence pages back to repository docs or other source-of-truth artifacts when appropriate.
4. Update repo documentation indexes if they should point to the Confluence page.

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
