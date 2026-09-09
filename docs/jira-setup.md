# Jira Setup For Task Starter

The `task-starter` skill (`skills/task-starter/SKILL.md`) can fetch Jira
ticket details and turn them into an implementation plan. It prefers the
**Atlassian CLI (`acli`)** (recommended - lower context and token use), and
falls back to **Jira MCP** (optional, more context-heavy, native IDE tools)
or a pasted ticket when neither is configured.

For the full command reference (search, comments, attachment replacement,
and the MCP tool list), see `integrations/jira.md`. This doc is the
one-time setup walkthrough and the agent-side detection/fallback procedure.

---

## Recommended: Atlassian CLI

**Prerequisites:** an Atlassian Cloud account and a terminal.

### Install

- **macOS (Homebrew):** `brew tap atlassian/homebrew-acli && brew install acli`
- **Other platforms:** see [Install Atlassian CLI (ACLI)](https://developer.atlassian.com/cloud/acli/guides/install-acli/).

Verify: `acli --version`

### Authenticate

```bash
acli jira auth login --web
```

Complete the browser flow. For token-based login see
[acli jira auth](https://developer.atlassian.com/cloud/acli/reference/commands/jira-auth-login/).

### Fetch one issue (what the agent uses)

```bash
acli jira workitem view <ISSUE_KEY> --json --fields summary,description,comment
```

Use a real key (for example `ABC-123`). Limiting `--fields` keeps context
small; the agent parses the JSON for summary, description, and comments.

### Going forward

- **New machine:** install `acli` and run `acli jira auth login --web` again.
- The agent runs the view command and parses the output when you say, for
  example, "Start this ticket: ABC-123."

---

## Detection And Setup (For The Agent)

When the user invokes `task-starter` with a Jira ticket ID and the fetch
fails or is unclear:

1. **Detect the CLI:** run `acli --version` (or `which acli`). If the
   command is not found, `acli` is not installed.
2. **Install if missing:** on macOS, offer to run
   `brew tap atlassian/homebrew-acli && brew install acli`. On other
   platforms, point to
   [Install ACLI](https://developer.atlassian.com/cloud/acli/guides/install-acli/)
   or run the appropriate install command if you can infer it (for example,
   a Linux curl-based binary install).
3. **Authenticate if needed:** if
   `acli jira workitem view <KEY> --json --fields summary,description,comment`
   fails with an auth error, run `acli jira auth login --web`, ask the user
   to complete the browser flow, then retry the view command.
4. **If the CLI is not an option:** suggest the user paste the ticket
   content, or set up **Jira MCP** (below) for native tools in an
   MCP-capable agent (uses more context).

Give precise, copy-pastable commands for the user's environment; run
install/auth commands on the user's behalf when the user has granted
terminal access.

---

## Alternative: Jira MCP (More Context-Heavy)

Jira MCP uses more tokens and context (full issue payloads and tool
schemas) but provides native tools in MCP-capable agents. Use it if you
prefer that over the CLI, or as the CLI's fallback.

### Where MCP is configured

Configure the server in your agent's MCP settings, then add an `atlassian`
block to the resulting config file. If other MCP servers are already
configured there, add `atlassian` inside the existing `mcpServers` object
rather than replacing it.

| Agent | Config file |
|-------|-------------|
| Cursor | `~/.cursor/mcp.json` (Settings -> Tools & Integrations -> Add New MCP Server) |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |
| Claude Code | `~/.claude/mcp.json` |

### Official Atlassian remote MCP

**Prerequisites:** Node.js v18+ and `npx` on `PATH`; an Atlassian Cloud
account with Jira access.

1. Add a server block:

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

2. **Save the file.** An Atlassian authorization window should open. If it
   does not, disable the `atlassian` server in your agent's MCP settings,
   then enable it again.
3. Complete the OAuth flow and grant the requested access.
4. Confirm the Atlassian server shows a non-zero tool count in your agent's
   MCP settings.

**Troubleshooting:** if tools do not appear, ensure Node 18+ and `npx` are
on `PATH`, then disable/enable the server. See
[Atlassian remote MCP server](https://www.atlassian.com/platform/remote-mcp-server)
and
[Getting started with the Atlassian remote MCP server](https://support.atlassian.com/rovo/docs/getting-started-with-the-atlassian-remote-mcp-server/).

If your organization self-hosts Jira, or uses a Cloud site other than the
default, the CLI and MCP server both still point at your tenant -
substitute your own `https://<your-site>.atlassian.net` site wherever a
step asks you to open Jira in a browser. Neither the CLI commands nor the
MCP block above hardcode a site.

---

## After Setup

- In chat you can say: **"Start this ticket: ABC-123"** or **"Get details
  for ABC-123."**
- The agent tries **Atlassian CLI** first (runs
  `acli jira workitem view <KEY> --json --fields summary,description,comment`
  and parses the result). If that is unavailable or fails, it uses **Jira
  MCP** when configured. If neither works, it asks you to paste the ticket
  content.
- For the broader command set (search, comments, attachment replacement)
  and the list of MCP tools, see `integrations/jira.md`.
