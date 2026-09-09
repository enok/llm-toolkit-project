---
name: confluence-documentation
description: "Create, read, update, delete, move, label, comment on, and manage Confluence documentation safely. Use for Confluence CRUD, wiki docs, page hierarchy, folders, attachments, comments, managed page sections, or syncing repo docs to Confluence."
license: MIT
metadata:
  author: dev-tools
  version: "1.1.0"
---

# Confluence Documentation

## Use when

- Searching or reading Confluence pages or folders for project, architecture,
  runbook, or ticket context.
- Creating a new Confluence page from repository documentation.
- Updating an existing page while preserving hierarchy, title, and important metadata.
- Adding labels, comments, attachments, or child pages.
- Moving or deleting Confluence pages or folders.
- Keeping Confluence synchronized with repo source-of-truth docs.

## Safety rules

- **Read before write:** fetch the existing page or folder, metadata, children,
  labels, and comments before updating, moving, or deleting.
- **Confirm destructive actions:** page deletion and attachment deletion require explicit user confirmation and page/attachment ID verification.
- **Prefer additive changes:** comments, labels, and child pages are safer than overwriting a page.
- **Use least privilege:** Confluence tools vary by provider, but read/search/write scopes should be enabled only as needed.
- **Keep source of truth clear:** repository Markdown is source of truth for code-level docs unless the user states Confluence is authoritative.
- **Avoid sensitive content:** do not publish secrets, tokens, PII, internal hostnames, or customer-specific details unless the user explicitly confirms the destination is approved for that data.
- **Preserve hierarchy:** check parent page and space before creating, moving, or updating pages.
- **Version consciously:** use minor edits for mechanical syncs; include a version comment for meaningful documentation updates when the tool supports it.
- **Backup before every existing-content write:** before updating, moving,
  deleting, commenting on, labeling, attaching to, or otherwise mutating an
  existing Confluence page or folder, export a rollback snapshot to the team's
  approved backup location (for example an object-storage prefix such as
  `s3://<backup-bucket>/confluence/<task-name>/`, or a repo-local
  `docs/jira/<TICKET-ID>/confluence-backup/` folder when no shared location is
  configured). Before exporting, verify the destination and the acting
  identity's effective access (for S3: `aws s3api head-bucket`), and confirm
  the source data classification permits storage there. Never substitute an
  unapproved destination or modify bucket policy/ACLs/encryption.
- **Capture mutation-complete rollback state:** always export lossless
  body/content, ID, title, version, space, ancestry/order, restrictions, labels,
  comments, and the attachment inventory. Add source/target hierarchy and
  descendants for moves, page/folder deletions, or other hierarchy changes.
  Add the bytes, version metadata, and checksums for every attachment that an
  attachment add/update/delete operation or content deletion could modify or
  remove.
- **Verify the backup before mutation:** use a task-specific prefix and a
  manifest recording destination and access evidence, source classification
  approval, mutation type, rollback inventory, formats, sizes, and SHA-256
  values. Re-read (for S3: `head-object` plus re-download) and hash every
  payload to prove its exact key, size, and bytes. Any authorization, coverage,
  upload, or readback gap blocks the Confluence mutation.

## Size and format guidance

- MCP page create/update tools are best for small or medium text-only pages.
- Large pages, image-heavy pages, and bulk syncs should use a separately reviewed REST or sync tool with a dry-run/preview mode.
- Do not download or execute third-party Confluence upload/download scripts until `skills/external-skill-intake/SKILL.md` has been completed for that source.
- For diagrams and other generated images, keep source (Mermaid/PlantUML) in the repo when possible and attach/render generated images only when Confluence cannot render the source directly. Prefer SVG/PDF attachments when supported; otherwise attach high-resolution PNG generated from current source. Apply `skills/image-quality-inspection/references/image-quality-gate.md` to 100% of generated/exported images after Confluence processing; this gate is mandatory. Fix and re-upload until acceptable, or report the exact image that cannot be inspected.

## Architecture spike guidance

- Verify Jira, Confluence, GitHub, local repo docs, and any cloud production
  evidence as distinct lanes; keep production cloud access read-only unless the
  user explicitly approves mutation.
- Ground current-state architecture in existing docs and code before drafting a
  target state.
- Include diagrams for current state, target state, and detailed flow when they
  materially improve review.
- For observability or search-replacement pages, document where ingestion,
  durable state, evaluation, metrics, alarms, and backfill/validation belong.
- Use authenticated REST as a fallback when CLI/MCP cannot create or update a
  page, but never print tokens, cookies, or auth headers.

## CRUD playbook

| Operation | Steps |
| --- | --- |
| Create | Search for duplicates by title and topic; identify target space and parent; draft Markdown; create as child page when possible; add labels; verify URL/content. |
| Read | Search with focused terms or CQL; read top candidates; fetch children/comments/attachments only when relevant; summarize page ID, title, URL, and relevance. |
| Update | Fetch current content and metadata; produce a minimal diff; preserve existing useful sections; update with clear title/content; verify rendered content. For marker-bounded/managed sections, follow the managed-section update rules below. |
| Delete | Confirm user intent, page title, page ID, and child/attachment impact; prefer archive/label/comment when possible; delete only after explicit approval. |
| Move | Verify current and target parent/space; move after confirmation; verify hierarchy after move. |
| Folder URL | Extract the ID from `/folder/<id>` URLs, verify it with a folder-capable API or tool, then inspect direct children and permitted operations before planning any move. |
| Labels | Read existing labels; add generic discoverability/status labels; avoid labels containing secrets, customer names, or one-off branch/ticket names in shared docs. |
| Comments | Use comments for review notes, open questions, or non-authoritative updates; reply in-thread when resolving existing feedback. |
| Attachments | List existing attachments first; upload/update only intentional artifacts; delete attachments only after explicit confirmation. |

## Managed-section updates

When a script or agent owns only a bounded section of a page, byte identity is
not a stable preservation contract: Confluence parses and rewrites
storage-format XML on every update, may discard HTML comments entirely, and
refreshes generated attributes such as `ri:version-at-save` even in untouched
content.

- Use **named Confluence anchor macros** as durable managed-section boundaries,
  never HTML comment markers (`<!-- BEGIN ... -->`) — comments are not reliable
  persistent boundaries in Confluence storage.
- Before updating, snapshot the current page version and full storage body.
- After updating, read the page back and validate **semantically**, not
  byte-for-byte:
  - exactly one opening and one closing anchor;
  - the managed section's required headings and links are present;
  - content outside the managed section is unchanged after normalizing known
    Confluence-generated attributes;
  - the expected version increment occurred and the rendered page retrieves
    successfully.
- Stop a batch before updating the next page when any readback check fails.

## Body round-trip artifact classes (API moves, renames, full-body updates)

When an MCP/REST update resubmits a fetched `html` body verbatim (the standard
way to move or retitle a page, since update tools require `body`), Confluence's
ADF write-canonicalization always produces three benign artifact classes on
readback — do not fail verification on them:

1. `data-local-id` attributes dropped from block elements;
2. media node filename inner text removed (`data-id`/`data-collection`
   attachment references stay intact, images still render);
3. inline mark nesting reordered (e.g. `<strong><span>` → `<span><strong>`).

Verify such updates **semantically**: title exact, text-only content identical
after tag stripping (excluding media filename text), and attribute inventories
identical for `href`, `data-id`, `data-annotation-id`, `data-collection`,
`data-card-appearance`, and `style`. One real fidelity risk exists: an
annotation (inline-comment) mark spanning a `<code>` segment can be dropped,
narrowing the comment's anchor. Pre-scan bodies for
`<code><span class="annotation"` overlaps before body-rewriting updates on
commented pages, and treat any other annotation-inventory change as a failure.

Two more hard-won rules: titles are plain text — never HTML-escape them
(`&` stays `&`, or the stored title shows a literal `&amp;`); and when copying
a fetched body into a backup file or another tool call, extract it losslessly
(e.g. `jq -j` from a spilled tool-result/transcript file) — hand transcription
silently loses non-breaking spaces and other multibyte characters.

## MCP operations to look for

When a Confluence MCP server is available, prefer native tools for:

- search and CQL lookup
- get page by ID or title/space
- get children, labels, comments, versions, diffs, views, attachments, and images
- create, update, move, or delete pages
- add labels and comments
- upload, download, or delete attachments

If MCP is unavailable, use the repository's documented Confluence CLI/manual fallback from `integrations/confluence.md`, or ask the user to paste page content.

### Atlassian CLI attachment gap

Official Atlassian CLIs (e.g. `acli`) commonly wrap only a subset of the Jira/Confluence REST surface, and attachment upload is a frequent omission — `list`/`delete` may exist while `add`/`upload`/`create` never does, in any released version. Before concluding a CLI cannot do something, call the underlying REST API directly instead of declaring a permanent gap:

```bash
# Jira Cloud
curl -u "<email>:<api-token>" -X POST -H "X-Atlassian-Token: no-check" \
  -F "file=@evidence.png" \
  https://<site>.atlassian.net/rest/api/3/issue/<KEY>/attachments

# Confluence Cloud
curl -u "<email>:<api-token>" -X POST -H "X-Atlassian-Token: no-check" \
  -F "file=@evidence.png" \
  https://<site>.atlassian.net/rest/api/content/<PAGE_ID>/child/attachment
```

`X-Atlassian-Token: no-check` bypasses the XSRF check that otherwise blocks multipart uploads on these endpoints. Verify success by re-fetching the issue/page's attachment list afterward rather than trusting the HTTP status alone.

## Verification checklist

- [ ] The approved backup destination, the acting identity's effective access, and source data-classification approval were verified before export.
- [ ] A mutation-complete pre-write snapshot and checksum manifest were stored under a task-specific prefix and verified byte-for-byte before mutation.
- [ ] Page ID, title, space, and parent are correct.
- [ ] No duplicate page already exists unless intentional.
- [ ] Content renders correctly in Confluence.
- [ ] Managed-section updates used named anchor macros (not HTML comments), snapshotted version+body before the write, and passed normalized semantic readback: exactly one anchor pair, required section content present, content outside the section unchanged, expected version increment.
- [ ] Labels/comments/attachments are correct.
- [ ] Generated/exported images and image-heavy rendered sections passed the mandatory image-quality inspection gate.
- [ ] Links back to repo source, Jira, or related docs are present where appropriate.
- [ ] Destructive operations had explicit user approval.
- [ ] Relevant indexes or docs are updated so the page is reachable.

## Related

- `workflows/confluence-documentation.md`
- `integrations/confluence.md`
- `workflows/document-creation.md`
- `skills/diagram-authoring/SKILL.md`
- `skills/image-quality-inspection/SKILL.md`
- `skills/external-skill-intake/SKILL.md`
