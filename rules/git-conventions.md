---
trigger: always_on
description: Git branch naming, protected-branch etiquette, semantic commit structure, PR lifecycle, and rebase workflow
---

# Git Branch & Commit Conventions

## Branches

- Name feature branches after the ticket: `<TICKET-ID>` or `<TICKET-ID>-short-description` (e.g. `ABC-123-add-user-endpoint`); never generic names like `feature/my-changes`.
- Follow the repository's documented working branch and PR base (README, CONTRIBUTING, `AGENTS.md`); when nothing is documented, ask.
- "Push this", "deploy this", "finish the work" never authorize a push or merge to `main`, `stage`, `qa`, `prod` or another protected branch. Ask which branch or PR. Protected branches change only through PRs a human merges; no self-merge (`gh pr merge`, `git push origin HEAD:<protected>`) unless the user names that PR and destination in this session.
- Never force-push, rebase, reset or rewrite a shared branch. Before a reset, checkout or clean, run `git status --porcelain=v1 --untracked-files=all`; sync a clone with `python3 scripts/git_safe_sync.py --repo <clone> --to <ref>` (refuses a dirty tree).

## Commits

- Prefix each commit `TICKET-ID: <imperative description>` unless a hook prepends the ID.
- Split every PR diff into these categories, in this order, never mixing two in one commit, skipping empty ones (no empty commits), each contiguous: **Infrastructure** (Terraform, CloudFormation, dashboards, alarms) · **Configuration** (build, DI/env, logging, CI/CD, LLM client config, `.gitattributes`, `.gitignore`) · **Support + utilities** · **Business logic + related unit tests** · **Integration tests** (integration, component, contract, system, e2e) · **Documentation** · **Cleanup**.
- Unit tests stay with the code they verify. Split a mixed file at hunk level (`git add -p`) or in a clean dedicated worktree. Split an oversized category into named contiguous subgroups, not by line count.
- Regrouping history (authorized ticket branch only): record `git rev-parse 'HEAD^{tree}'`, create `backup/<ticket>-before-regroup-<timestamp>`, work in a clean worktree, and require an identical tree against the backup before any rebase.
- Stacked PRs: every layer passes its own build and tests; prove the final tree equals the pre-split recovery ref; reconcile each PR's base/head SHA and files against the hosting service's live PR Files API.

## PR File Change Table (Mandatory)

Every created PR body has a `## File changes` table (`| File | Status | Purpose |`) with one row per path in `git diff --name-status --find-renames origin/<base>...HEAD`, including generated, lock, binary and deleted paths, renames as `old -> new`, and a file-specific purpose; no globs or "related files". Re-sync it after every rebase or scope change. Write it with `--body-file`, read the body back through the API and require exact path coverage against the paginated PR files list; if it does not fit, split the PR.

## Draft PR Lifecycle (Mandatory)

- Always open PRs with `gh pr create --draft`.
- Mark ready (`gh pr ready <PR>`) as soon as all hold: CI green on the current head (or the repo's accepted exact-head gate); bot findings addressed; human threads resolved or explicitly deferred; `workflows/pre-pr-check.md` reports no blockers; `scripts/security-check-toolkit.sh` passes or failures are scoped as nonblocking with evidence. Leaving a validation-complete PR in draft is a violation unless the user ordered it.
- A review bot reported as disabled or skipped is a blocker, not a pass. A new actionable finding on a ready PR sends it back with `gh pr ready <PR> --undo`.
- When branch protection refuses a merge, record the exact action the user must take and never report it as merged. Do not re-sign or force-push commits because of an unsigned-commit message unless asked.

## Duplicate-File Gate (Mandatory, Pre-Push)

Cloud-sync tools create `file (1).ext` copies with stale content. Before every push, `git ls-files | grep -E ' \([0-9]+\)\.'` must print nothing; `git rm` any copy and verify the original first.

## Rebase Before Push

- On an authorized ticket branch: `git fetch origin`, `git rebase origin/<base>`, resolve, re-run the full tests, run the duplicate-file gate, then push (`--force-with-lease` only when the rebase replaced remote history). Never `git merge` upstream changes.
- A PR behind its base under strict checks is caught up with `gh pr update-branch <pr> --rebase`, then its state is read back.

## Environment Branches

Promote a reviewed ticket branch to an environment branch (e.g. `stage`) only where that remote branch exists and the user asked for that environment; never create it to match sibling repos, and never push the shared tooling repo as part of an application release. First check `git log --oneline --right-only origin/<ticket>...origin/<env>` for unique deployment fixes, advance by fast-forward, cherry-pick or non-force merge, verify the remote SHA, and return to the ticket branch.
