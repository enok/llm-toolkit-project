# Confluence Mutation Backup Gate (Template)

> **This is a template.** Copy it into the consuming repo's `docs/llm/` or your IDE's rules directory and fill in your approved backup destination. Shared toolkit surfaces must stay free of organization-specific folder IDs.

## Trigger Configuration

```yaml
trigger: model_decision
description: Fail-closed backup gate before mutating existing Confluence pages or folders
```

## Rule

Before mutating an existing Confluence page or folder, fail closed unless all of the following hold:

- The backup destination resolves to the approved shared backup folder configured for your deployment (for example a `Confluence-Backup` Drive folder — set the exact folder ID here: `<YOUR-BACKUP-FOLDER-ID>`).
- The acting identity already has the required read/write access.
- The source data classification explicitly permits storage in that destination.
- Record and preserve the existing destination permissions; never broaden sharing to make a backup succeed.

Export a mutation-complete rollback snapshot and manifest to a task-specific
subfolder under the approved root. Always capture lossless body/content,
page/folder ID, title, version, space, ancestry and sibling order, restrictions,
labels, comments, and an attachment inventory. Also capture descendant state
for moves, deletions, and other hierarchy operations, plus the bytes, version
metadata, and checksums of every attachment that the operation could modify or
remove. Verify the root and task-subfolder identities and re-read or download
every uploaded artifact to confirm parent, size, and SHA-256 before the
Confluence write. Any missing authorization, rollback state, or readback blocks
the mutation.

## Related

- `rules/operational-doc-required.md` requires this gate before wiki mutations.
- `rules/external-write-authorization.md` governs whether the mutation is authorized at all.
