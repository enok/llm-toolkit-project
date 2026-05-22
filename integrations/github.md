# GitHub Integration

Read code, PRs, branches, and issues across repositories from any LLM agent.

---

## Option 1: GitHub CLI (`gh`)

The GitHub CLI is lightweight and works in any terminal.

### Install

- **macOS:** `brew install gh`
- **Windows:** `winget install --id GitHub.cli`
- **Linux:** See [cli.github.com](https://cli.github.com/)

Verify: `gh --version`

### Authenticate

```bash
gh auth login
```

Follow the prompts (browser or token-based).

### Common Commands

```bash
# View a PR
gh pr view <PR_NUMBER> --json title,body,files,reviews,comments

# List PRs
gh pr list --search "TICKET-ID" --json number,title,state

# View a file from a specific branch or commit
gh api repos/{owner}/{repo}/contents/{path}?ref={branch}

# Search code across repos
gh search code "functionName" --repo owner/repo

# List branches
gh api repos/{owner}/{repo}/branches --jq '.[].name'

# View PR checks/CI status
gh pr checks <PR_NUMBER>

# Create a PR
gh pr create --title "TICKET-ID: Description" --body "..." --draft

# Add PR labels
gh pr edit <PR_NUMBER> --add-label "review,ready"
```

---

## Option 2: GitHub MCP

GitHub provides an MCP server for native tool access in supported IDEs.

### Setup

Add to your MCP config file:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-github"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-token>"
      }
    }
  }
}
```

Create a personal access token at [github.com/settings/tokens](https://github.com/settings/tokens) with `repo` scope.

### Available MCP Tools

- `search_code` — search code across repositories
- `get_file_contents` — read files from any repo/branch
- `search_pull_requests` — find PRs by query
- `pull_request_read` — read PR details, comments, checks
- `list_commits` — view commit history
- `list_branches` — list branches in a repo

---

## Option 3: Git (Local)

For local repo operations, standard git commands work:

```bash
# View recent commits
git log --oneline -20

# View changes on a branch
git diff main..feature-branch --stat
git diff main..feature-branch

# Search code
git grep "pattern"

# View file at a specific commit
git show <commit>:<path>
```

---

## How Workflows Use GitHub

- **ticket-research** — search for existing PRs and branches related to a ticket
- **review** — read PR comments, check CI status, push changes
- **project-discovery** — explore repo structure, read key files across repos

---

## Tips

- **Use `--json` with `gh`** to get structured output the agent can parse.
- **Limit fields** in API calls to reduce context size.
- **Personal access tokens** should have minimal scope — `repo` is usually sufficient.
- Store tokens in environment variables, never in code.
