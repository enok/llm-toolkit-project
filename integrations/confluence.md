# Confluence Integration

Search, read, create, update, delete, move, label, comment on, and attach files to project documentation, architecture pages, and team wikis from any LLM agent.

---

## Option 1: Atlassian CLI

The same `acli` CLI used for Jira also supports Confluence.

### Prerequisites

- `acli` installed and authenticated (see `jira.md` for install steps)
- Confluence Cloud account

### Common Commands

```bash
# Search for pages
acli confluence content search "project architecture" --json --limit 5

# Read a page by ID
acli confluence content get <PAGE_ID> --json

# Read a page by title and space
acli confluence content get --space DEV --title "Architecture Overview" --json

# List child pages
acli confluence content list --parent-id <PAGE_ID> --json
```

Use `skills/confluence-documentation/SKILL.md` and `workflows/confluence-documentation.md` before mutating pages.

Some Confluence URLs point at folders, for example `/folder/<id>`, rather than
pages. If the active CLI can only read pages or spaces, use a folder-capable
REST/MCP/tool surface to verify the folder, direct children, and permitted
operations before planning a move. A page lookup that returns "not found" for a
folder ID proves only that the page endpoint cannot read that content type.

---

## Option 2: Confluence MCP (Native tools)

If using MCP (same `atlassian` server as Jira), the agent gets native Confluence tools:

### Available MCP Tools

- `confluence_search` — search pages with simple text or CQL
- `confluence_get_page` — get page content by ID, title, or space
- `confluence_get_page_children` — list child pages
- `confluence_get_comments` — read page comments
- `confluence_create_page` — create new pages
- `confluence_update_page` — update existing pages
- `confluence_move_page` / `confluence_delete_page` — move or delete pages
- `confluence_add_label` / `confluence_get_labels` — manage labels
- `confluence_add_comment` / `confluence_reply_to_comment` — manage comments
- `confluence_get_attachments` / `confluence_upload_attachment` — manage attachments

### CQL Search Examples

```
# Simple text search
"project documentation"

# Search by title
title ~ "Architecture"

# Search in specific space
type=page AND space=DEV

# Recently modified
lastModified > startOfMonth("-1M")

# Content with specific label
label=documentation
```

### Setup

Uses the same MCP server as Jira — see `jira.md` Option 2 for full details. The `atlassian` MCP server provides both Jira and Confluence tools.

**MCP Configuration** (add to your IDE's MCP config, e.g. `.codeium/mcp_config.json` for Windsurf):

```json
{
  "mcpServers": {
    "mcp-atlassian": {
      "command": "uvx",
      "args": ["mcp-atlassian"],
      "env": {
        "CONFLUENCE_URL": "https://<COMPANY>.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "<COMPANY-EMAIL>",
        "CONFLUENCE_API_TOKEN": "<CONFLUENCE-API-TOKEN>"
      }
    }
  }
}
```

> **Note:** Replace `<COMPANY>`, `<COMPANY-EMAIL>`, and `<CONFLUENCE-API-TOKEN>` with your actual values. Generate an API token at [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens). If you already have the `mcp-atlassian` server configured for Jira, just add the `CONFLUENCE_*` env vars to the existing entry.

---

## Moving, Renaming, and Ordering Pages via Update Tools

Some MCP surfaces (e.g. the Atlassian remote MCP) have no dedicated move tool —
a move or rename is a full update call that requires `body`. Fetch the page as
`html` and resubmit the body verbatim with the new `parentId`/`title`; see
`skills/confluence-documentation/SKILL.md` ("Body round-trip artifact classes")
for the canonicalization artifacts to accept and the semantic verification
contract.

Mechanics that determine tree order:

- Setting a **different** `parentId` appends the page to the end of the new
  parent's children. Setting the **same** `parentId` does not reposition.
- To impose a custom/alphabetical order, run **out-and-back** moves (page →
  temporary parent → home parent) strictly in target order; each return append
  lands at the tail. Only pages breaking the target order need moving — a
  longest-ordered-prefix of already-correct children can stay in place.
- The v2 children API may **omit `childPosition` for freshly moved pages**;
  verify order by the move sequence/timestamps, or re-query later.
- If a sequential move batch is interrupted mid-page, resume state-check-first:
  fetch the page and both parents' children to learn whether the interrupted
  update landed before redoing anything.
- **Folders cannot be moved, archived, or deleted via the API/MCP** — those are
  UI-only operations; targeting a folder ID with a page update/move returns 404
  ("cannot find a page"). To relocate a folder's contents, create a same-named
  page at the destination, move the child pages under it, and leave the emptied
  folder for a manual UI archive/delete — document that pending manual step
  where the reorganization is tracked; do not silently drop the folder's subtree.
- Titles are plain text in update payloads — never HTML-escape them.

---

## REST Editing and Attachment Patterns

Some MCP page tools only return `html` or `markdown`, which are lossy for
round-tripping macros. For any edit that must preserve existing page content,
work in storage format via REST:

```
GET  /rest/api/content/<PAGE_ID>?expand=body.storage,version,ancestors
PUT  /rest/api/content/<PAGE_ID>   (version.number = current + 1, same title)
```

### Surgical edits to hand-maintained pages

Never regenerate a hand-maintained page body to apply a small fix — it clobbers
human edits and `ac:macro-id` attributes. Script the fix as `{Find, Replace}`
pairs and enforce gates:

1. Fetch the fresh storage body and version; never edit a cached copy.
2. Require each needle to occur **exactly once** (abort on 0 or 2+ matches);
   pick needles long enough to be unique, such as a whole `<td>...</td>` cell.
3. Enforce content invariants across the batch (for example: the count of
   ticket-id patterns must not change, so nothing forbidden is introduced).
4. PUT with `version.number = current + 1`, then read the page back and require
   every replacement string to be present.

### Generated vs hand-maintained pages

Before editing any page, check whether a repo script generates it. Fix
generated content in the generator and re-run it; hand-edits to generated
bodies are silently overwritten on the next publish. Reserve surgical REST
edits for pages with no generator.

### Attachments

- Pages embed attachments by filename (`ri:attachment ri:filename`), so
  uploading a new attachment version under the **same name** upgrades every
  embedded render with zero body edits. Publishers should fail when an expected
  name is absent rather than create a new name the body never references, and
  verify version numbers advanced after upload.
- Direct `/download/attachments/...` URLs can return 401 under basic auth even
  when the API token is valid. Download through the attachment's
  `_links.download` value from the REST attachment listing instead.

---

## How Workflows Use Confluence

- **ticket-research** — searches for related documentation pages to gather context
- **project-discovery** — reads architecture docs, onboarding guides, team wikis
- **review** — checks if documentation needs updating after code changes
- **confluence-documentation** — performs safe documentation CRUD and synchronization

---

## Tips

- **Search before reading** — use search to find the right pages, then read specific pages.
- **Limit results** — set `limit` to 3-5 for searches to keep context manageable.
- **Use CQL for precision** — CQL queries give more targeted results than simple text search.
- **Check labels** — pages with labels like `architecture`, `onboarding`, `api-docs` are usually the most useful.
- **Read before write** — fetch the page and metadata before any update, move, or delete.
- **Folder-aware reads** — verify `/folder/<id>` links with folder-capable tools,
  including children and operations, before moving ticket-scoped documentation.
- **Format-safe writes** — fetching a page as markdown **flattens** expands
  (`<details>`), panels, and layouts; updating with that markdown body destroys
  the structure permanently. For any page containing expands/panels/layout
  sections, round-trip in HTML (or storage) format: fetch as HTML, apply the
  targeted change, and send the full HTML body back. Reserve markdown round-trips
  for pages that are plain headings/paragraphs/tables end to end.
- **Confirm destructive actions** — delete pages or attachments only after explicit user approval.
