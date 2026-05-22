---
description: 5-category commit structure, validation, rebase, and push procedure
---

# Commit and Push (5-Category Rule)

Reusable commit/push procedure used by `ticket-review-and-fix`, `ticket-implementation`, and any workflow that ends with committing changes. Follow every step in order.

---

## Step 1 — Reset the Branch

> **⚠️ Destructive operation**: this rewrites branch history. Ask the user for confirmation before proceeding unless they have already opted in (e.g., by invoking this workflow explicitly).

```bash
git reset --mixed origin/<base-branch>
```
This unstages ALL commits on the branch, keeping all changes in the working directory. You will now re-commit everything from scratch in the correct 5-category order.

**1a. Check `git status` for LLM config files** — look for any changes (staged or unstaged) to:
- `.windsurf/` (project-specific rules/workflows)
- `AGENTS.md`
- `.gitignore`

These MUST be committed in Category 1 even if they were not part of the review findings.

---

## Step 2 — Re-commit in 5-Category Order

Re-commit ALL changes in exactly this order. Skip categories with no changes. **Maximum 5 commits. Each category gets exactly ONE commit.**

| Order | Category | What belongs here |
|-------|----------|-------------------|
| 1 | **LLM configs** | `.windsurf/`, `.cursor/`, `.agents/`, `.claude/`, `.codex/`, `AGENTS.md`, `CLAUDE.md`, `.gitignore` |
| 2 | **Documentation** | `README.md`, `docs/`, architecture diagrams, API specs, PlantUML |
| 3 | **Logs improvement** | Logger setup/format/level changes, log context, MDC, logging-only test files |
| 4 | **Application configs/structure** | Config files, build config, DI config, env config, dependency files |
| 5 | **Code changes** | Source code, business logic, tests for business logic |

**Commit rules:**
- Each commit prefixed with ticket ID: `TICKET-ID: <description>`
- **Never mix categories** in a single commit.
- **If a source file has BOTH logging and business logic changes**, use the intermediate-file approach:
  1. Save the final version to a temp location (`cp file /tmp/file_final`)
  2. Edit the file to contain only original code + new logging changes
  3. Stage and commit in Category 3
  4. Restore the final version (`cp /tmp/file_final file`)
  5. Stage and commit in Category 5
- Tests follow their subject: logging tests → Cat 3, business logic tests → Cat 5.
- Use `git add -p` for hunk-level splits when changes are in separate, non-interleaved hunks.

---

## Step 3 — Validate Commit Structure

```bash
git log --oneline $(git merge-base origin/<base-branch> HEAD)..HEAD
```
Verify ALL of the following — **if ANY check fails, go back to Step 1 and redo**:
- [ ] Each commit belongs to exactly ONE category (1–5)
- [ ] Categories appear in ascending order — no category appears after a higher-numbered one
- [ ] No category is repeated — maximum 1 commit per category, maximum 5 commits total
- [ ] Each commit message starts with the ticket ID
- [ ] No build output, IDE files, secrets, or `.agents/` directory in any commit
- [ ] No cloud-sync duplicate files (see below)

**3a. Check for cloud-sync duplicates** (blocking — see `rules/git-conventions.md § Duplicate-File Gate`):
```bash
git ls-files | grep -E ' \([0-9]+\)\.' && echo "BLOCKED: remove duplicate files before pushing" && exit 1
```
If any results appear, `git rm` each duplicate, verify the original is correct, and re-run the check.

**If validation fails, `git reset --mixed origin/<base-branch>` and restructure again.**

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
git push --force-with-lease
```

**5a. Push to stage branch** (opt-in — enables stage environment testing):
> **⚠️ Shared branch**: only push to `stage` if the project uses a stage deployment branch and the user confirms. Skip this step if the project does not use a `stage` branch.

```bash
git push origin HEAD:stage --force-with-lease
```
If `--force-with-lease` fails (e.g., stage branch has diverged), use `--force` since stage is a transient deployment branch.

After any successful push to `stage`, always check out the ticket branch again before handing control back to the user. This applies whether `stage` was updated by direct push, cherry-pick, merge, or any other mechanism.

```bash
git checkout <ticket-branch>
```

---

## Step 6 — Reply to PR Comments

For each addressed PR comment (S2 fixes), reply with what changed and where.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
