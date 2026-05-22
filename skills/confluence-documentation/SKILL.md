---
name: confluence-documentation
description: "Create, read, update, delete, move, label, comment on, and manage Confluence documentation safely. Use for Confluence CRUD, wiki docs, page hierarchy, attachments, comments, or syncing repo docs to Confluence."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Confluence Documentation

## Use when

- Searching or reading Confluence pages for project, architecture, runbook, or ticket context.
- Creating a new Confluence page from repository documentation.
- Updating an existing page while preserving hierarchy, title, and important metadata.
- Adding labels, comments, attachments, or child pages.
- Moving or deleting Confluence pages.
- Keeping Confluence synchronized with repo source-of-truth docs.

## Safety rules

- **Read before write:** fetch the existing page, metadata, children, labels, and comments before updating, moving, or deleting.
- **Confirm destructive actions:** page deletion and attachment deletion require explicit user confirmation and page/attachment ID verification.
- **Prefer additive changes:** comments, labels, and child pages are safer than overwriting a page.
- **Use least privilege:** Confluence tools vary by provider, but read/search/write scopes should be enabled only as needed.
- **Keep source of truth clear:** repository Markdown is source of truth for code-level docs unless the user states Confluence is authoritative.
- **Avoid sensitive content:** do not publish secrets, tokens, PII, internal hostnames, or customer-specific details unless the user explicitly confirms the destination is approved for that data.
- **Preserve hierarchy:** check parent page and space before creating, moving, or updating pages.
- **Version consciously:** use minor edits for mechanical syncs; include a version comment for meaningful documentation updates when the tool supports it.

## Size and format guidance

- MCP page create/update tools are best for small or medium text-only pages.
- Large pages, image-heavy pages, and bulk syncs should use a separately reviewed REST or sync tool with a dry-run/preview mode.
- Do not download or execute third-party Confluence upload/download scripts until `skills/external-skill-intake/SKILL.md` has been completed for that source.
- For diagrams, keep Mermaid/PlantUML source in the repo when possible and attach/render generated images only when Confluence cannot render the source directly.

## CRUD playbook

| Operation | Steps |
| --- | --- |
| Create | Search for duplicates by title and topic; identify target space and parent; draft Markdown; create as child page when possible; add labels; verify URL/content. |
| Read | Search with focused terms or CQL; read top candidates; fetch children/comments/attachments only when relevant; summarize page ID, title, URL, and relevance. |
| Update | Fetch current content and metadata; produce a minimal diff; preserve existing useful sections; update with clear title/content; verify rendered content. |
| Delete | Confirm user intent, page title, page ID, and child/attachment impact; prefer archive/label/comment when possible; delete only after explicit approval. |
| Move | Verify current and target parent/space; move after confirmation; verify hierarchy after move. |
| Labels | Read existing labels; add generic discoverability/status labels; avoid labels containing secrets, customer names, or one-off branch/ticket names in shared docs. |
| Comments | Use comments for review notes, open questions, or non-authoritative updates; reply in-thread when resolving existing feedback. |
| Attachments | List existing attachments first; upload/update only intentional artifacts; delete attachments only after explicit confirmation. |

## MCP operations to look for

When a Confluence MCP server is available, prefer native tools for:

- search and CQL lookup
- get page by ID or title/space
- get children, labels, comments, versions, diffs, views, attachments, and images
- create, update, move, or delete pages
- add labels and comments
- upload, download, or delete attachments

If MCP is unavailable, use the repository’s documented Confluence CLI/manual fallback from `integrations/confluence.md`, or ask the user to paste page content.

## Verification checklist

- [ ] Page ID, title, space, and parent are correct.
- [ ] No duplicate page already exists unless intentional.
- [ ] Content renders correctly in Confluence.
- [ ] Labels/comments/attachments are correct.
- [ ] Links back to repo source, Jira, or related docs are present where appropriate.
- [ ] Destructive operations had explicit user approval.
- [ ] Relevant indexes or docs are updated so the page is reachable.

## Related

- `workflows/confluence-documentation.md`
- `integrations/confluence.md`
- `workflows/document-creation.md`
- `skills/diagram-authoring/SKILL.md`
- `skills/external-skill-intake/SKILL.md`
