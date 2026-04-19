# Integrations

Guides for connecting LLM agents to external tools and services. These integrations provide context and capabilities that enhance the workflows and skills.

## Available Integrations

| Integration | File | Purpose |
|-------------|------|---------|
| **Jira** | `jira.md` | Fetch ticket details, search issues, manage sprints |
| **Confluence** | `confluence.md` | Search and read documentation, project wikis |
| **GitHub** | `github.md` | Read code, PRs, branches, issues across repos |
| **AWS CLI** | `aws-cli.md` | Manage cloud infrastructure, deploy, inspect resources |

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
