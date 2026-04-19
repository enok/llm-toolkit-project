---
trigger: always_on
description: Git branch naming, commit messages, and rebase workflow
---

# Git Branch & Commit Conventions

## Branch Naming

- **Always** create feature branches using the ticket ID as the branch name.
- Format: `<TICKET-ID>` or `<TICKET-ID>-short-description`
- Examples: `ABC-123`, `ABC-123-add-user-endpoint`, `BUG-456-fix-search` (use your tracker’s real prefix)
- The ticket ID is extracted from the task context (Jira ticket, PR title, user request, etc.)
- **Never** use generic branch names like `feature/my-changes` or `fix/bug`
- **Never** commit directly to `main` or the default protected branch

## Commit Messages

- Write clear, concise commit messages describing what changed.
- If the project uses pre-commit hooks to prepend ticket IDs, write just the description.
- Otherwise, prefix with ticket ID: `ABC-123: Add user profile endpoint`
- Use imperative mood: "Add", "Fix", "Update" — not "Added", "Fixed", "Updated"

## Commit Structure (PR Organization)

When committing changes for a PR, organize commits into up to 5 categories in this order. **Only create commits for categories that have changes** — skip empty categories.

| Order | Category | What belongs here |
|-------|----------|-------------------|
| 1 | **LLM configs** | `.windsurf/`, `.cursor/`, `.agents/`, `.claude/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.gitignore` |
| 2 | **Documentation** | `README.md`, `docs/`, architecture diagrams, API specs, PlantUML |
| 3 | **Logs improvement** | Logger setup/format/level changes, log context, MDC, logging-only test files |
| 4 | **Application configs/structure** | Build config (`pom.xml`, `requirements.txt`), DI config, env config, `__init__.py`, dependency files |
| 5 | **Code changes** | Source code, business logic, tests for business logic |

**Rules:**
- Each commit is prefixed with the ticket ID: `TICKET-ID: <description>`
- Never mix categories in a single commit.
- If a source file has **both** logging and business logic changes, split them: commit logging changes (new/modified log lines, log levels, log format, log context calls, commented-out log removal) in commit 3, and remaining code changes in commit 5. Use `git add -p` for hunk-level splits or create intermediate file versions for interleaved changes.
- Tests follow their subject: logging tests → commit 3, business logic tests → commit 5.
- Restructure commits before pushing using `git reset --mixed` and selective `git add`.

## Draft PR Lifecycle (Mandatory)

- **Always** open PRs as drafts: `gh pr create --draft`
- A PR stays in draft until **all** of the following are true:
  1. All CI checks pass (green).
  2. All bot review comments are addressed (e.g., Cursor automation, linters).
  3. All human review comments are resolved or explicitly deferred with justification.
  4. The pre-PR check workflow (`workflows/pre-pr-check.md`) reports no blockers.
  5. The security check (`scripts/security-check-toolkit.sh`) passes or all failures are reviewed.
- Only then mark as ready: `gh pr ready <PR_NUMBER>`
- **Never** open a PR as ready-for-review on first push.
- **Never** mark a PR ready while unresolved comments exist — address or defer each one first.

## Duplicate-File Gate (Mandatory — Pre-Push)

Cloud-sync tools (Google Drive, OneDrive, Dropbox) silently create conflict-resolution copies named `file (1).ext`, `file (2).ext`, etc. These duplicates can contain **stale or contradictory content** and must **never** be committed.

**Before every push**, run:
```bash
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files before pushing" && exit 1
```

If duplicates are found:
1. Delete them: `git rm 'path/to/file (1).md'`
2. Verify the original file is correct.
3. Re-run `git ls-files | grep -E ' \([0-9]+\)\.'` — must return nothing.

This check is **blocking** — do not push while any duplicate exists.

## Rebase Before Push

- **Always** rebase onto the base branch before every `git push`.
- Steps (always in this order):
  1. `git fetch origin`
  2. `git rebase origin/main` (or the PR base branch)
  3. Resolve any conflicts
  4. Re-run the full test suite to ensure nothing broke
  5. Check for cloud-sync duplicates (see § Duplicate-File Gate above)
  6. `git push --force-with-lease`
- **Never** push without rebasing first — even if the branch was recently created.
- **Never** use `git merge` to integrate upstream changes — rebase only.
