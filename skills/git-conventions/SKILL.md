---
name: git-conventions
description: |
  Git branch naming, commit messages, PR lifecycle, and rebase workflow. Use for all
  Git operations including commits, branching, pull requests, and merges.
license: MIT
---

# Git Conventions

Branch naming, commit messages, and PR lifecycle conventions.

> **Reference**: For complete rules, see `rules/git-conventions.md`

## Quick Reference

### Branch Naming
- Format: `<TICKET-ID>` or `<TICKET-ID>-short-description`
- Examples: `ABC-123`, `ABC-123-add-user-endpoint`
- Never use generic names like `feature/my-changes`
- Never commit directly to `main`

### Commit Messages
- Use imperative mood: "Add", "Fix", "Update" (not "Added", "Fixed")
- Prefix with ticket ID: `ABC-123: Add user profile endpoint`
- Write clear, concise descriptions

### Commit Structure (PR Organization)
Organize commits in this order:
1. LLM configs (`.windsurf/`, `.cursor/`, `AGENTS.md`)
2. Documentation (`README.md`, `docs/`)
3. Logs improvement (logger setup/changes)
4. Application configs/structure (build config, DI config)
5. Code changes (source code, business logic, tests)

### Draft PR Lifecycle (Mandatory)
1. **Always** open PRs as drafts
2. PR stays draft until:
   - All CI checks pass
   - All bot review comments addressed
   - All human review comments resolved
   - Pre-PR check reports no blockers
3. Only then mark as ready

### Rebase Before Push
```bash
git fetch origin
git rebase origin/main
# Resolve conflicts
# Re-run tests
git push --force-with-lease
```

### Duplicate-File Gate (Mandatory)
Before every push, check for cloud-sync duplicates:
```bash
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files" && exit 1
```

## When to Apply

- Creating a new branch
- Writing commit messages
- Organizing commits for PR review
- Preparing to push changes
- Managing PR lifecycle

## Related

- `rules/git-conventions.md` — Complete Git rules
- `workflows/pre-pr-check.md` — PR preparation workflow
