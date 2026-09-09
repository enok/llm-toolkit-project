---
trigger: always_on
description: Git branch naming, protected-branch etiquette, semantic commit structure, PR lifecycle, and rebase workflow
---

# Git Branch & Commit Conventions

## Branch Naming

- **Always** create feature branches using the ticket ID as the branch name.
- Format: `<TICKET-ID>` or `<TICKET-ID>-short-description`
- Examples: `ABC-123`, `ABC-123-add-user-endpoint`, `BUG-456-fix-search` (use your tracker's real prefix)
- The ticket ID is extracted from the task context (Jira ticket, PR title, user request, etc.)
- **Never** use generic branch names like `feature/my-changes` or `fix/bug`
- Do not commit directly to `main` or another protected branch unless the repository's documented workflow expects it (see § Protected Branches and Target Ambiguity)

## Protected Branches and Target Ambiguity

`main` (or the repository's documented default branch) and shared environment
branches such as `stage`, `qa`, and `prod` are shared state: other people's
checkouts, deployments, and audit history depend on them.

- **Know the target before you push.** Read the repository's README,
  CONTRIBUTING, or `AGENTS.md` to find its documented working branch and PR
  base. Some repositories work directly on `main`, others use ticket branches
  with PRs, others promote through environment branches. Follow the documented
  model; when nothing is documented, ask.
- **Ambiguity resolves to asking.** "Push this", "deploy this", "make this
  live", "finish the work", and "complete the release" do not name a branch or
  a merge destination and never authorize a push or merge to a protected
  branch. Ask: "Should I push to `<ticket-branch>`, open a PR to `<base>`, or
  push to a different branch?"
- **Protected branches change through pull requests a human reviews and
  merges.** An agent does not self-merge: `gh pr merge`,
  `git push origin HEAD:<protected-branch>`, or an API merge targeting a
  protected branch requires the user to name that specific PR and destination
  in the current session. Direct commits on `main` are acceptable only where
  the repository's documented workflow expects them (for example a personal
  repository that works on `main`), and only for the change the user asked for.
- **Never force-push, rebase, reset, or rewrite a shared branch.**
  `--force-with-lease` is for the agent's own ticket/feature branch after an
  authorized rewrite (see § Ticket/Feature Branch Rebase Before Push).
- **Verify before every push or merge:** check the target
  (`git rev-parse --abbrev-ref HEAD` plus the explicit push refspec); if the
  target is protected or shared, confirm explicit authorization for this
  specific push/merge; if authorization is missing or unclear, stop and ask.

## Commit Messages

- Write clear, concise commit messages describing what changed.
- If the project uses pre-commit hooks to prepend ticket IDs, write just the description.
- Otherwise, prefix with ticket ID: `ABC-123: Add user profile endpoint`
- Use imperative mood: "Add", "Fix", "Update" — not "Added", "Fixed", "Updated"

## Commit Structure (PR Organization)

Organize every non-empty PR diff into the categories below. The first five are
the canonical implementation categories; Documentation and Cleanup complete the
PR history when those changes exist. Use the fewest coherent commits that keep
review boundaries clear; there is no fixed commit count. Keep commits from the
same category contiguous, and skip categories with no legitimate changes.

| Category | What belongs here |
|----------|-------------------|
| **Infrastructure** | Terraform, CloudFormation, deployment resources, dashboards, alarms, and other provisioned-resource definitions |
| **Configuration** | Build and dependency files, DI and environment config, logging config, CI/CD config, LLM/client config (`AGENTS.md`, `.cursor/`, `.claude/`, `.codex/`, `.windsurf/`), `.gitattributes`, and `.gitignore` |
| **Support + utilities** | Shared helpers, adapters, filters, aspects, reusable unit-test fixtures, reusable scripts, and low-level utilities that support business behavior |
| **Business logic + related unit tests** | Domain behavior, controllers/services/models that implement requirements, and the focused unit tests that verify that behavior |
| **Integration tests** | Integration, component, contract, system, end-to-end, and runtime-wiring tests, including their test-specific fixtures and configuration, that verify multiple units or external boundaries together |
| **Documentation** | `README.md`, maintained `docs/`, runbooks, learnings, architecture diagrams, API specifications, and PlantUML |
| **Cleanup** | Removal of retired code, config, documentation, generated clutter, or other obsolete assets when that removal is independently reviewable |

**Rules:**
- Each commit is prefixed with the ticket ID: `TICKET-ID: <description>`.
- Never mix categories in a single commit.
- If one category is still too large for a focused review, split it into
  contiguous, meaningful subgroups. Examples include
  `Business logic + related unit tests — request handling` and
  `Infrastructure — observability`. Do not split merely to lower line counts.
- Unit tests stay with the business logic or support utility they verify.
  Integration, component, contract, system, end-to-end, and cross-boundary
  runtime tests belong in **Integration tests** instead of being mixed into a
  production-code commit.
- A file with changes from multiple categories must be split at hunk level with
  `git add -p` or reconstructed in a clean, dedicated worktree. Do not use an
  unrelated dirty worktree as scratch space.
- Do not create empty or audit-only commits merely to represent a category.
- Preserve the displayed category order. Skip empty categories, and keep every
  meaningful subgroup contiguous within its category.

### History-regrouping safeguards

- Rewrite only a ticket or feature branch whose history the user explicitly
  authorized for rewriting. Never apply this procedure to a shared environment
  or protected branch.
- Before regrouping, record `git rev-parse 'HEAD^{tree}'` and create a local
  backup ref such as `backup/<ticket>-before-regroup-<timestamp>`.
- Use a clean, dedicated worktree or an isolated temporary Git index. If the
  active worktree contains unrelated staged, unstaged, or untracked work, do not
  reset, stash, overwrite, or include it implicitly.
- For a history-only regrouping, immediately after the regroup and before any
  base-branch rebase, require both
  `git diff --quiet backup/<ticket>-before-regroup-<timestamp> HEAD` to exit
  zero and the two refs' `^{tree}` values to match exactly.

### Stacked-PR split safeguards

- Treat commit subjects as evidence, not ownership boundaries. Classify the
  final tree by path and split mixed files at hunk level; preserve a recovery
  ref before reconstructing the stack.
- Every intermediate layer must pass the validations applicable to its files,
  including compilation and tests when it owns executable code. When moving
  an entire requested file would break an earlier layer, keep only the minimum
  dependency, wiring, or contract-test hunk required there and document the
  exception in both affected PR descriptions.
- Prove the reconstructed stack with adjacent ancestry checks and an exact
  final-tree identity check against the pre-split recovery ref. A green final
  layer does not excuse a broken intermediate PR.
- Git hosting services can retain stale comparison snapshots after lower-layer
  heads or bases change. Refresh or recreate the stack as supported, then
  reconcile every PR's base/head SHA and file table against the hosting
  service's live PR Files API; local Git diffs alone are insufficient.
- Before removing a split worktree, prove its tracked, staged, and untracked
  state is either clean or durably represented by a retained ref/artifact.
  Prune missing registrations separately; never force-remove unique dirty
  state merely to reclaim disk space.

## PR File Change Table (Mandatory)

Every created PR must include a Markdown table that accounts for every path in
the base-to-head diff. Build the inventory from
`git diff --name-status --find-renames origin/<base>...HEAD`; do not rely on
memory or a hand-maintained planning list.

```markdown
## File changes

| File | Status | Purpose |
|------|--------|---------|
| `path/to/file` | Added / Modified / Deleted / Renamed | Concise, file-specific explanation of why this path changed |
```

- Include one row for every added, modified, deleted, or renamed path. For a
  rename, show `old/path -> new/path` in one row.
- The Purpose column must explain the file's role in the PR; do not merely
  repeat the filename or use a generic phrase such as "updated file."
- Do not collapse paths into globs, directories, counts, or "and related files."
  Generated, lock, binary, and deletion-only paths still require rows.
- Keep the table synchronized after every scope-changing commit, rebase, or
  review fix. Immediately before creating or updating the PR, reconcile its
  rows against the live base-to-head diff and require exact path coverage.
- Use `--body-file` for large descriptions and read the PR body back after the
  mutation to verify that the heading, table, and row coverage survived
  rendering. If the complete table cannot fit within the hosting platform's PR
  body limit, split the change into smaller PRs before creation.
- Generate large PR bodies only from complete authoritative sources: the live
  base-to-head Git diff and a fully paginated PR-files API inventory. Do not
  reuse terminal, rendered, or tool display output that may be truncated.
  Before mutation, reject truncation markers and require the expected table
  count. After mutation, fetch the complete body through the API, compare its
  normalized content with the intended body file, and require the table paths
  to match the paginated file inventory with no missing, extra, or duplicate
  rows. Treat any mismatch as a failed update. Prepare the corrected body and
  re-confirm approval before another human-visible mutation unless the original
  authorization explicitly covered that exact idempotent retry.

## Draft PR Lifecycle (Mandatory)

- **Always** open PRs as drafts: `gh pr create --draft`
- A PR stays in draft until **all** of the following are true:
  1. All CI checks pass (green), or the repo's accepted exact-head gate equivalent (for example a successful review-automation check when GitHub Actions are absent).
  2. All bot review comments are addressed (e.g., Cursor automation, linters); actionable current-diff findings are zero.
  3. All human review comments are resolved or explicitly deferred with justification (unresolved threads = 0 unless explicitly deferred).
  4. The pre-PR check workflow (`workflows/pre-pr-check.md`) reports no blockers, or the ticket/program equivalent validation gate has independently passed.
  5. The security check (`scripts/security-check-toolkit.sh`) passes or all failures are reviewed / scoped as nonblocking with evidence.
- **When those criteria are met, immediately mark the PR ready** with `gh pr ready <PR_NUMBER>`. Leaving a validation-complete PR in Draft is a rule violation.
- Do not keep a finished PR as Draft for handoff convenience, environment rollout sequencing, or "owner will decide later" unless the user explicitly orders Draft retention.
- **Never** open a PR as ready-for-review on first push.
- **Never** mark a PR ready while unresolved actionable comments exist — address or defer each one first.
- A terminal response saying a review bot is disabled, skipped, or unavailable
  is an external review blocker, not a successful current-head review. Record
  local builds, CI, deployment/live checks, and review automation as separate
  gates, and require the review evidence to identify the current head SHA.
- If a Ready PR later gains an actionable finding, return it to Draft with `gh pr ready <PR_NUMBER> --undo`, fix, re-validate, then mark Ready again.

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

## Windows Git Lock Handling

On Windows, IDEs, file explorers, antivirus scans, and background Git processes
can hold handles under `.git/objects` or `.git/index` long enough to make
`git pull`, `git fetch`, `git gc`, or rebase cleanup fail.

Before retrying repeatedly:

1. Check for active Git processes and close duplicate terminals working in the
   same repository.
2. Close IDE or file explorer windows that are indexing or browsing the repo.
3. Enable Git filesystem caching to reduce lock contention:

```bash
git config --global core.fscache true
git config --global core.preloadindex true
```

If locks persist, stop and report the exact locked path and operation. Do not
delete `.git/objects/*`, remove index files, or run `git reset --hard` unless
the user explicitly approves the destructive recovery step.

## Ticket/Feature Branch Rebase Before Push

- For a user-authorized ticket or feature branch, rebase onto the PR base before
  pushing. This rule never applies to shared environment or protected branches.
- Steps (always in this order):
  1. `git fetch origin`
  2. `git rebase origin/main` (or the PR base branch)
  3. Resolve any conflicts
  4. Re-run the full test suite to ensure nothing broke
  5. Check for cloud-sync duplicates (see § Duplicate-File Gate above)
  6. Use `git push --force-with-lease` only when the authorized ticket-branch
     rebase or regroup replaced remote history; otherwise use a normal
     `git push`.
- **Never** push without rebasing first — even if the branch was recently created.
- **Never** use `git merge` to integrate upstream changes — rebase only.

## Environment Branch Promotion

Some projects deploy from shared environment branches (for example `stage`).
When promoting a reviewed ticket branch to such a branch, preserve the ticket
branch as the source of truth. Do not rebase or rewrite the ticket branch just
to deploy it.

For multi-repo tickets, declare the final repository scope before validating or
pushing. In each repository, verify the active branch and remote branches first:

```bash
git status --short --branch
git branch -r
```

Push an environment branch only in repositories where that remote branch already
exists and the user requested that environment update. Do not create `stage` in
one repository just because sibling repositories use it.

Do not push shared LLM/tooling repositories to an environment branch as part of
an application release flow unless the user explicitly names that tooling
repository as the target.

Before moving the environment branch, inspect whether it has unique deployment
fixes:

```bash
git fetch origin --prune
git log --oneline --right-only origin/<ticket-branch>...origin/<env-branch>
```

Never rebase, reset, or force-push a shared environment branch such as `stage`
or `prod`. Preserve its unique commits and advance it only through a normal
fast-forward, cherry-pick, or non-force merge after inspecting both divergence
and patch identity. Push the environment branch normally, verify the remote SHA,
then check out the ticket branch again before continuing.
