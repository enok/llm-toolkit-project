# Jira Integration

Fetch ticket details, search issues, and manage work items from any LLM agent.

---

## Option 1: Atlassian CLI (Recommended — lower context use)

The Atlassian CLI (`acli`) is lightweight and keeps LLM context small.

### Install

- **macOS (Homebrew):** `brew tap atlassian/homebrew-acli && brew install acli`
- **Other platforms:** See [Install Atlassian CLI (ACLI)](https://developer.atlassian.com/cloud/acli/guides/install-acli/)

Verify: `acli --version`

### Authenticate

```bash
acli jira auth login --web
```

Complete the browser flow. For token-based login see [acli jira auth](https://developer.atlassian.com/cloud/acli/reference/commands/jira-auth-login/).

### Common Commands

```bash
# Fetch a single issue (what the agent typically uses)
acli jira workitem view <ISSUE_KEY> --json --fields summary,description,comment

# Search issues
acli jira workitem list --jql "project = PROJ AND status = 'In Progress'" --json

# Add a comment
acli jira workitem comment add <ISSUE_KEY> --body "Implementation complete"
```

Limiting `--fields` keeps context small. The agent parses the JSON for summary, description, and comments.

### Agent Detection and Setup

When the agent needs Jira and CLI is not available:

1. **Detect:** Run `acli --version`. If not found, CLI is not installed.
2. **Install if missing:** Offer the appropriate install command for the user's OS.
3. **Authenticate if needed:** If fetch fails with auth error, run `acli jira auth login --web`.
4. **Fallback:** If CLI is not an option, suggest Jira MCP or ask the user to paste ticket content.

---

## Option 2: Jira MCP (Native tools, more context)

MCP (Model Context Protocol) provides native tool access in supported IDEs. Uses more tokens but offers richer interaction.

### IDE Configuration

#### Windsurf / Cursor / Claude Code

Add to your MCP config file:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote@latest",
        "https://mcp.atlassian.com/v1/sse"
      ]
    }
  }
}
```

**Config file locations:**
- **Windsurf:** `~/.codeium/windsurf/mcp_config.json`
- **Cursor:** `~/.cursor/mcp.json`
- **Claude Code:** `~/.claude/mcp.json`

Save the file, complete the OAuth flow, and verify tools appear in your IDE's MCP settings.

### Available MCP Tools

When connected via MCP, the agent can use tools like:
- `jira_get_issue` — fetch issue details
- `jira_search` — search with JQL
- `jira_create_issue` — create new issues
- `jira_update_issue` — update fields
- `jira_add_comment` — add comments
- `jira_get_transitions` / `jira_transition_issue` — manage status

See [Atlassian remote MCP server](https://www.atlassian.com/platform/remote-mcp-server) for full documentation.

---

## Option 3: User Paste (No setup)

If neither CLI nor MCP is available, the agent will ask the user to paste the ticket content directly. This works but loses the ability to search and cross-reference.

---

## After Setup

In chat, say:
- **"Start this ticket: ABC-1234"** — triggers task-starter with Jira context
- **"Get details for ABC-1234"** — fetches and displays the issue
- **"Research ABC-1234"** — triggers ticket-research workflow

The agent tries **CLI first** (lower context), then **MCP** (richer tools), then asks for a paste.
