# Integrations

Guides for connecting LLM agents to external tools and services. These integrations provide context and capabilities that enhance the workflows and skills.

## Available Integrations

| Integration | File | Purpose |
|-------------|------|---------|
| **Jira** | `jira.md` | Fetch ticket details, search issues, manage sprints |
| **Confluence** | `confluence.md` | Search and read documentation, project wikis |
| **GitHub** | `github.md` | Read code, PRs, branches, issues across repos |
| **AWS CLI** | `aws-cli.md` | Manage cloud infrastructure, deploy, inspect resources |
| **Jenkins** | `jenkins.md` | Check job/build status, read console logs, trigger builds |
| **Slack CLI** | `slack-cli.md` | Build and deploy Slack apps with a pinned, checksum-verified CLI |

## Client Preference Order

When an integration offers multiple access options, agents MUST prefer, in this order:

1. **Local CLI client** (`acli`, `gh`, `aws`, `jenkins-cli.jar`) — lowest context use, reuses the developer's existing authenticated session and permissions, and behaves identically across all agents (Claude, Codex, Windsurf, Cursor, Copilot, Gemini).
2. **MCP server** — fallback when no CLI covers the capability, when the CLI is unavailable and cannot be installed/authenticated, or when the task genuinely needs MCP-only tools.
3. **User paste** — last resort when neither is available.

Detect before falling back: run the CLI's version/auth check first (e.g. `acli --version`, `gh auth status`, `aws sts get-caller-identity`) and offer install/login steps before switching to MCP.

## How Integrations Are Used

Workflows reference integrations when they need external context:

- **ticket-research** → Jira (ticket details) + Confluence (documentation) + GitHub (PRs, branches)
- **review** → Jira (ticket ACs) + GitHub (PR comments, CI status)
- **task-starter** → Jira (ticket details) + Confluence (related docs)
- **project-discovery** → Confluence (architecture docs) + GitHub (repo structure)

## Setup Priority

1. **Jira** — required for ticket-based workflows (task-starter, ticket-research, review)
2. **Confluence** — recommended for documentation-aware workflows
3. **GitHub** — recommended for multi-repo projects and PR workflows
4. **AWS CLI** — optional, for infrastructure and deployment tasks
5. **Jenkins** — optional, for CI/CD status checks and build automation
6. **Slack CLI** — optional, for Slack application development; not general message-posting authorization
