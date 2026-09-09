---
description: Semantic commit organization, validation, rebase, and safe push procedure
---

# Commit and Push

Reusable commit/push procedure used by `ticket-review-and-fix`, `ticket-implementation`, and any workflow that ends with committing changes. Follow every step in order.

---

## Step 1 — Prepare an Isolated Regrouping Workspace

> **⚠️ Destructive operation**: this rewrites branch history. Ask the user for confirmation before proceeding unless they have already opted in (e.g., by invoking this workflow explicitly).

First choose the path explicitly:

- **Ordinary commit:** when no existing ticket commits need regrouping, do not
  reset or rewrite history. Proceed to Step 2 and stage the current in-scope
  changes selectively.
- **History regrouping:** only when the user separately authorized rewriting an
  existing ticket/feature branch, continue with the isolated procedure below.

Before any authorized history rewrite, capture the current state and create a
local recovery ref:

```bash
git status --short
git rev-parse 'HEAD^{tree}'
git branch backup/<ticket>-before-regroup-<timestamp> HEAD
```

Regroup only a ticket or feature branch. If the active worktree has unrelated
staged, unstaged, or untracked work, do not reset, stash, patch, overwrite, or
include it. Create a dedicated worktree or use an isolated temporary Git index,
or stop for user direction. A backup branch protects committed history, not
uncommitted work.

```bash
git worktree add --detach ../<repo>-<ticket>-regroup <ticket-branch>
cd ../<repo>-<ticket>-regroup
git status --short  # must produce no output before reset
git switch -c <ticket>-regroup
```

```bash
git reset --mixed origin/<base-branch>
```
Run that command only inside the clean dedicated regrouping worktree. It
unstages the branch commits while retaining their file changes for selective
re-commit. An isolated-index implementation may build the same trees without
modifying a worktree.

---

## Step 2 — Re-commit by Semantic Category

Re-commit every non-empty change using the canonical categories in
`rules/git-conventions.md`: **Infrastructure**, **Configuration**,
**Support + utilities**, **Business logic + related unit tests**,
**Integration tests**, **Documentation**, and **Cleanup**. Skip empty
categories. Use the fewest coherent commits; split an oversized category only
into contiguous, meaningful, independently reviewable subgroups.

**Commit rules:**
- Each commit prefixed with ticket ID: `TICKET-ID: <description>`
- **Never mix categories** in a single commit.
- Preserve the displayed category order, skip empty categories, and keep all
  meaningful subgroups from one category contiguous.
- Unit tests stay with the business logic or support utility they verify;
  integration, component, contract, system, end-to-end, and runtime-wiring tests
  use the separate **Integration tests** category.
- For files that cross categories, use `git add -p` or reconstruct exact
  intermediate blobs in the isolated workspace/index.
- Do not create empty, audit-only, or category-placeholder commits.

---

## Step 3 — Validate Commit Structure

```bash
git log --oneline $(git merge-base origin/<base-branch> HEAD)..HEAD
```
Verify ALL of the following — **if ANY check fails, go back to Step 1 and redo**:
- [ ] Each commit belongs to exactly one semantic category
- [ ] Every non-empty category is represented, and empty categories are skipped
- [ ] Commits from the same category are contiguous
- [ ] Each subgroup is meaningful and independently reviewable, not a mechanical line-count split
- [ ] Each commit message starts with the ticket ID
- [ ] No build output, IDE files, secrets, or linked toolkit output directories in any commit
- [ ] No cloud-sync duplicate files (see below)
- [ ] If the rewrite was intended to be history-only, the final tree hash
      matches the backup ref immediately after regrouping and before rebasing:
      `git diff --quiet backup/<ticket>-before-regroup-<timestamp> HEAD` exits
      zero, and both `^{tree}` values match. In PowerShell, quote tree
      expressions like `'HEAD^{tree}'` so braces are not parsed by the shell.

**3a. Check for cloud-sync duplicates** (blocking — see `rules/git-conventions.md § Duplicate-File Gate`):
```bash
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files before pushing" && exit 1
```
If any results appear, `git rm` each duplicate, verify the original is correct, and re-run the check.

**If validation fails, repair it only in the isolated regrouping workspace or
temporary index. Never reset the user's unrelated dirty worktree.**

For follow-up fixes that belong in an existing grouped commit, prefer
`git commit --fixup=<commit>` plus
`git rebase -i --autosquash origin/<base-branch>` over adding a new
category-breaking commit. Run that rewrite only in the clean dedicated
worktree/index established in Step 1.

---

## Step 4 — User Approval Gate (MANDATORY)

**STOP and present the commit structure to the user before pushing.**

```bash
git log --oneline $(git merge-base origin/<base-branch> HEAD)..HEAD
```

Present the commit list and ask: **"Ready to rebase and push?"**

- **Do NOT push until the user explicitly approves.**
- If the user requests changes, go back to Step 1.
- **Skip this gate** only if: (a) the calling workflow already obtained explicit user approval for these changes in the same session, or (b) the user explicitly asked to skip approval (e.g., "just push it").

---

## Step 5 — Rebase and Push

```bash
git fetch origin
git rebase origin/<base-branch>
# Resolve any conflicts
# Re-run full test suite after rebase
# Re-check for cloud-sync duplicates (rebase can resurrect them)
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED" && exit 1
# Ordinary push when remote history was not replaced:
git push
# If and only if the user-authorized rebase/regroup replaced published ticket
# history, use this instead of the normal push:
git push --force-with-lease
```

**5a. Push to stage branch** (opt-in — enables stage environment testing):
> **⚠️ Shared branch**: only push to `stage` if the project uses a stage deployment branch and the user confirms. Skip this step if the project does not use a `stage` branch. In multi-repo work, explicitly name the repositories in scope and verify `origin/stage` exists in each one before pushing.
> Do not apply an application repository's `stage` promotion step to a shared LLM/tooling repository unless the user explicitly asks to update that tooling repository's own environment branch.

```bash
git branch -r | grep -E 'origin/stage$'
git fetch origin
git log --left-right --cherry-mark --oneline origin/stage...origin/<ticket-branch>
git worktree add --detach ../<repo>-<ticket>-stage-promotion origin/stage
cd ../<repo>-<ticket>-stage-promotion
git switch -c <ticket>-stage-promotion
# Choose and execute exactly one reviewed promotion action:
git cherry-pick <missing-ticket-commit-sha>...
# Or, instead of cherry-picking, use a reviewed non-force merge:
# git merge --no-ff origin/<ticket-branch>
git push origin HEAD:stage
git rev-parse HEAD
git ls-remote origin refs/heads/stage
```
Never rebase, reset, or force-push the shared environment branch. Start from the
latest `origin/stage`, preserve its unique commits, and advance it only with a
normal fast-forward, cherry-pick, or non-force merge after checking divergence
and patch identity. The SHA printed by `git rev-parse HEAD` must equal the SHA
returned by `git ls-remote` after the normal push.

After a successful push to `stage`, return to the original application worktree
and verify it is still on the ticket branch before handing control back. Do not
try to check out the same ticket branch inside the promotion worktree because
Git normally permits a branch to be checked out in only one worktree.

```bash
cd <original-application-worktree>
git branch --show-current  # must equal <ticket-branch>
```

---

## Step 6 — Reply to PR Comments

For each addressed PR comment (S2 fixes), reply with what changed and where.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
