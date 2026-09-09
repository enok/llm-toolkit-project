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

# View PR review state, comments, and status rollup
gh pr view <PR_NUMBER> --json reviews,latestReviews,comments,statusCheckRollup

# Create a PR
git diff --name-status --find-renames origin/<base>...HEAD
gh pr create --title "TICKET-ID: Description" --body-file <pr-body.md> --draft
gh pr view --json body --jq .body

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

## PR Body Markdown Hygiene

Every PR description requires the exact per-path **File changes** table defined
by `rules/git-conventions.md § PR File Change Table`. Preserve each repository
path exactly in inline code so automated or manual reconciliation can compare it
with the live diff without normalization ambiguity:

```markdown
| `src/main/java/com/example/service/Foo.java` | Modified | Reason |
```

If paths make one table hard to scan, split the inventory into multiple tables
under semantic-category subheadings, but retain one row per path and the exact
`File | Status | Purpose` columns in every table.

Before pushing or updating the PR body, verify the table still represents the
branch diff:

```bash
git diff --name-status --find-renames origin/main...HEAD
gh pr view <PR_NUMBER> --json body --jq .body
```

For large Markdown body edits, especially from PowerShell, avoid ad hoc JSON
patch pipelines. Write the body to a temporary UTF-8 file, use the dedicated PR
command, then read the body back and verify expected headings, table headers,
commit SHAs, and validation rows are still line-oriented:

```powershell
$tmp = New-TemporaryFile
Set-Content -Path $tmp -Value $body -Encoding UTF8
gh pr edit <PR_NUMBER> --body-file $tmp
Remove-Item -LiteralPath $tmp -Force

$readBack = (gh pr view <PR_NUMBER> --json body | ConvertFrom-Json).body
$readBack -match "(?m)^## Validation$"
$readBack -match "(?m)^\| Check \| Result \| Details \|$"
```

When a branch has multiple historical PRs, list PRs for the head branch and
update the latest branch-backed PR that documents the current branch work,
rather than rewriting an older merged PR with a different scope.

---

## Automation Review State

When resolving automation review findings, inspect both inline review threads
and top-level PR reviews/comments. Some tools report all inline threads resolved
while the latest top-level review still contains actionable warnings.

Use `gh pr view <PR_NUMBER> --json reviews,latestReviews,comments,statusCheckRollup`
for top-level state, then GraphQL `reviewThreads` for inline thread status. Do
not rely on `gh pr checks` alone; a PR can have no concrete check contexts and
still have review findings in comments or reviews.

Before replying to or resolving review threads, pin the exact `owner/repo#PR`
from the user, browser URL, or task source. PR numbers and ticket branches are
not globally unique across repositories.

```powershell
$repo = '<owner>/<repo>'
$pr = <number>
gh pr view $pr --repo $repo --json number,title,headRefName,baseRefName,url
```

Query unresolved threads for that same repo and PR, keep both GraphQL thread
IDs and numeric comment IDs, reply to the original review comments after the fix
is pushed, resolve only those actual threads, and finish with a read-back that
shows zero unresolved actionable threads on the same `owner/repo#PR`.

---

## Tips

- **Use `--json` with `gh`** to get structured output the agent can parse.
- **Limit fields** in API calls to reduce context size.
- **Personal access tokens** should have minimal scope — `repo` is usually sufficient.
- Store tokens in environment variables, never in code.
