---
description: Create, read, update, delete, move, label, comment, and manage Confluence documentation safely
---

# Confluence Documentation Workflow

Use this workflow for Confluence documentation CRUD and synchronization.

## Phase 1 — Scope and authority

1. Identify the requested operation: create, read, update, delete, move, label,
   folder management, comment, or attachment management.
2. Confirm whether the repository, Confluence, or another system is the source of truth.
3. For writes, identify target space, parent page, title, labels, and intended audience.
4. For destructive operations, stop and get explicit user confirmation before proceeding.

## Phase 2 — Discover existing content

1. Search Confluence using focused terms or CQL.
2. Read the relevant page or folder before updating, moving, deleting, or commenting.
3. Check child pages, labels, comments, attachments, or versions when they affect the operation.
4. Record page ID, title, space, parent, URL, and why it is relevant.
5. For `/folder/<id>` URLs, verify the ID with a folder-capable read path and
   include direct children and permitted operations. Do not treat page-only
   lookup failure as proof the folder is absent.

## Phase 3 — Prepare the change

1. Before any mutation of an existing Confluence page or folder, complete the
   mandatory pre-write backup gate:
   - resolve the backup destination the repository documents for this purpose
     (for example an object-storage bucket or document store recorded in the
     repo's `docs/llm/` context) and verify its identity and the acting
     identity's effective read/write access — for object storage, an existence
     and access probe such as `aws s3api head-bucket`. Do not substitute another
     destination and do not modify bucket policy, ACLs, or encryption to make a
     backup succeed;
   - confirm from the applicable owner or documented classification policy that
     the source page/folder data may be stored in that exact destination;
     stop before exporting content when approval is absent or uncertain;
   - create or reuse a task-specific prefix or folder
     (`confluence/<task-name>/`) beneath the verified destination;
   - always export lossless body/content (ADF or storage format), page/folder
     ID, title, URL, current version, space, ancestry and sibling order,
     restrictions, labels, comments, and an attachment inventory;
   - for moves, page/folder deletions, or other hierarchy changes, also export
     the current source and target ancestry, sibling ordering, descendants, and
     affected restrictions;
   - for attachment add/update/delete or any overwrite/delete that can remove
     attachments, also download every affected pre-write attachment payload
     and record its attachment ID, filename, media type, size, version history,
     and a SHA-256 for each required rollback version;
   - add a manifest containing the verified destination/prefix, access evidence,
     source classification approval, export timestamp, mutation
     type, rollback inventory, format, size, and SHA-256 for every payload;
   - upload the payloads and manifest, then stat each stored object (for
     example `aws s3api head-object`) and re-download/hash every artifact to
     verify its exact key, size, and SHA-256; availability alone is
     insufficient;
   - stop before the Confluence write if destination authorization, rollback
     coverage, upload, or byte-for-byte readback is incomplete.
2. Draft content in Markdown unless the destination requires another format.
3. Keep names, links, and diagrams evidence-based; verify against source code, repo docs, or existing Confluence pages.
4. Avoid secrets, tokens, PII, internal-only hostnames, customer-specific details, branch names, and one-off ticket names unless the destination is explicitly approved.
5. Preserve useful existing sections and minimize unrelated rewrites.
6. For diagrams and other generated images, keep source in the repo and attach SVG/PDF or high-resolution PNG generated from current source when the page cannot render source directly.
7. Apply `skills/image-quality-inspection/references/image-quality-gate.md` to every generated/exported image before upload and again after Confluence renders or processes it. If quality is unacceptable, fix, re-export, and re-upload.
8. Run `documentation-reviewer` on new or updated Confluence content, generated
   artifacts, and human-facing page comments before publication or final
   reporting. Comments remain draft-only until the user approves the exact text
   and target.

### Architecture or replacement spikes

For architecture spikes, replacement proposals, and incident follow-up pages:

- Verify Jira, Confluence, GitHub, local repository docs, and any cloud
  production context as separate evidence lanes. Keep production cloud checks
  read-only unless mutation is explicitly approved.
- Ground the current-state section in existing code and docs before proposing a
  target state.
- Include current-state and target-state diagrams when the audience needs to
  compare architecture, component boundaries, or request flow.
- For AWS observability or search-replacement proposals, distinguish stateless
  alarms from stateful evaluation needs. Document where event ingestion,
  durable state, evaluation, metrics, alarms, and backfill/validation live.
- If the CLI cannot create or update the page but an authenticated REST path is
  available, use REST without printing tokens, cookies, or authorization
  headers.
- Link the Confluence page back to the source ticket and link the ticket back to
  the Confluence page when ticket mutation is in scope.

## Phase 4 — Apply the operation

| Operation | Action |
| --- | --- |
| Create | Create under the confirmed parent page or space; add labels; verify rendered page. |
| Read | Summarize content with page URL and relevance; do not mutate anything. |
| Update | Update only the intended page; include a clear version comment when supported. |
| Delete | Verify page ID/title and child/attachment impact; delete only after explicit approval. |
| Move | Verify current and target hierarchy; move; re-read children/hierarchy after move. |
| Folder | Verify folder ID/title, parent, children, and permitted operations with a folder-capable surface before moving, emptying, or deleting anything. |
| Label/comment | Read existing labels/comments first; add the minimal intended label/comment. |
| Attachments | List attachments first; upload/update/delete only confirmed files. |

## Phase 5 — Verify and link

1. Re-read or inspect the page after mutation.
2. Confirm hierarchy, labels, comments, attachments, and rendered content, including 100% generated/exported image sharpness/readability after Confluence processing.
3. Confirm the verified backup snapshot and manifest still identify the exact
   pre-write version, the mutation-complete rollback set, unchanged backup
   permissions, and the task prefix/folder location in the evidence trail.
4. Link Confluence pages back to repository docs or other source-of-truth artifacts when appropriate.
5. Update repo documentation indexes if they should point to the Confluence page.
6. Confirm the documentation-reviewer findings are resolved or explicitly
   reported as residual risk.

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
