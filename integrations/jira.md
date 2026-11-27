# Jira Integration

Use the Atlassian CLI (`acli`) for Jira; it keeps context small. Install:
`brew tap atlassian/homebrew-acli && brew install acli` (macOS; other platforms: Atlassian's
ACLI install guide). Authenticate with `acli jira auth login --web`.

## Option 1: Atlassian CLI (acli) syntax

```bash
acli jira workitem view <ISSUE_KEY> --json --fields summary,description,comment
acli jira workitem list --jql "project = PROJ AND status = 'In Progress'" --json
acli jira workitem comment add <ISSUE_KEY> --body "Implementation complete"
acli jira workitem attachment list --key <ISSUE_KEY> --json
acli jira workitem attachment delete --id <OLD_ATTACHMENT_ID>
```

## Upload fallback

If the CLI cannot upload an attachment, use the Jira REST API with the active authenticated
session and the header `X-Atlassian-Token: no-check`. Never print bearer tokens or cookies.

## Local-path leak check

Before finishing, check the work item description AND the text inside attached files (for
example a generated PDF) for `file:///`, `C:/Users` or `C:\Users` paths. Flag each one and tell
the user to remove them before the update is final.

## Detection and setup (for the agent)

`acli --version`; if missing, offer the install command; on an auth error run
`acli jira auth login --web`; otherwise use Option 2 or ask the user to paste the ticket.

## Option 2: Jira MCP (alternative, more context)

`{"mcpServers":{"atlassian":{"command":"npx","args":["-y","mcp-remote@latest","https://mcp.atlassian.com/v1/sse"]}}}`
in the client's MCP config, then complete OAuth. The same server also serves Confluence.
