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
- **Confirm destructive actions** — delete pages or attachments only after explicit user approval.
