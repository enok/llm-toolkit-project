---
name: ci-watcher
description: >
    After every git push (with an open PR), spawn a background agent to watch the CI
    workflow, investigate failures, and report findings back to the main agent for fixing.
    Use when CI monitoring should happen automatically after pushes.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# CI Watcher

Automatically monitor CI after pushing and investigate failures. The watcher is read-only — it investigates and reports back, but the main agent handles any fixes.

## When to Use

After every `git push` (including force pushes) **where a pull request (draft or otherwise) exists for the branch**. CI workflows only run on branches with open PRs, so don't spawn a watcher if there's no PR yet.

Typical flow: push → create PR → spawn watcher. Or if the PR already exists: push → spawn watcher.

**Important:** Only repos with CI workflow files (e.g., `.github/workflows/ci.yml`) have CI. Before spawning the watcher, check if CI exists. If it doesn't, skip — there's nothing to watch. The examples below use `ci.yml`; substitute the repo's actual workflow file name (`ls .github/workflows/`) when it differs.

## How to Spawn

After a push, spawn a background read-only agent:

```
subagent_type: "Explore"       # Read-only — cannot edit files or push
run_in_background: true        # Don't block the main conversation
```

Use this prompt template, filling in the variables:

- `REPO_DIR`: absolute path to the repo
- `BRANCH`: the branch that was pushed
- `BASE_BRANCH`: the branch this was based off (e.g., `main` or `develop`)

```
You are a read-only CI watcher for the repository at {REPO_DIR}.
Watch the CI workflow for branch {BRANCH} (based off {BASE_BRANCH}); a PR exists for it.

Polling:
1. From {REPO_DIR}, get the latest run:
   gh run list --workflow=ci.yml --branch={BRANCH} --limit=1 --json databaseId,status,conclusion
2. Poll job statuses:
   gh run view <run_id> --json jobs --jq '.jobs[] | {name, status, conclusion}'
3. If ANY job has conclusion "failure", investigate immediately. If ALL jobs succeed,
   report CI passed and stop. Otherwise sleep 60 seconds and poll again. Be patient —
   CI can take 5-15 minutes — and always sleep between polls to avoid hammering the API.

Investigation (on failure):
1. Get failed logs: gh run view <run_id> --log-failed 2>/dev/null | tail -300
2. Classify each error as flaky/infrastructure (annotation processing failures across many
   unrelated files, network/DNS timeouts, Docker pull or registry auth errors, runner
   out-of-memory, artifact download failures) or real (cannot find symbol, import errors,
   or test failures tied to the branch changes).
3. Check relatedness against: git diff --name-only origin/{BASE_BRANCH}...HEAD
4. If NOT related to the changes: re-run failed jobs (max 1 re-run) and report the
   unrelated failure. If related: read the relevant source files, identify the specific
   fix, and report it — do NOT edit files. If both kinds appear: focus on real errors
   and report both categories.

Rules:
- Monitor only the CI workflow; ignore other workflows.
- React to individual job failures immediately — don't wait for the full run.
- You are read-only: never edit, write, commit, or push.
- Always report back to the main agent — even if CI passes or failures are unrelated.
```

## Polling

Poll at the job level so you can react as soon as any job fails:

1. Get the run ID:
   `gh run list --workflow=ci.yml --branch={BRANCH} --limit=1 --json databaseId,status,conclusion`
2. Poll individual job statuses:
   `gh run view <run_id> --json jobs --jq '.jobs[] | {name, status, conclusion}'`
3. Evaluate:
   - If ANY job has `conclusion: "failure"`: investigate immediately.
   - If ALL jobs succeed: report CI passed, then stop.
   - If jobs are still in progress with none failed: wait 60 seconds and poll again.

## Investigation

1. Get failed job logs:
   `gh run view <run_id> --log-failed 2>/dev/null | tail -300`
2. **Separate real errors from flaky errors:**

   **Flaky/infrastructure errors (NOT caused by branch changes):**
   - Annotation processing failures across many unrelated files
   - Network timeouts, DNS resolution failures
   - Docker pull failures, registry auth errors
   - Out-of-memory errors in CI runners
   - Artifact download failures

   **Real errors (likely caused by branch changes):**
   - `cannot find symbol` for something added/removed/renamed in the diff
   - Import errors referencing changed packages
   - Test failures in tests that exercise changed code

3. **To determine if an error is real:** Run `git diff --name-only origin/{BASE_BRANCH}...HEAD` to see changed files. Check if the error directly relates to something in those changed files.
4. **If NOT related to changes:** Re-run failed jobs (max 1 re-run). Report the unrelated failure.
5. **If related to changes:** Read the relevant source files, identify the fix, and report back with the specific fix needed. Do NOT attempt to edit files — the main agent handles that.
6. **If BOTH flaky and real errors:** Focus on real errors. Report both categories.

## Rules

- Only monitor the CI workflow. Ignore other workflows.
- React to job failures immediately — don't wait for the full run.
- Be patient — CI can take 5-15 minutes.
- Use `sleep` between polls to avoid hammering the API.
- You are read-only. Investigate and report — never edit, write, or push.
- **Always report back** — even if CI passes or failures are unrelated.

## Handling Watcher Reports

**Failure related to changes:**
1. Tell the user what failed and the suggested fix
2. Apply the fix
3. Commit and push
4. Spawn a new watcher

**Failure NOT related to changes:**
1. Tell the user what failed and that it's unrelated
2. The watcher re-runs failed jobs and continues monitoring

**CI passed:**
1. Tell the user CI passed

## Related Skills

- **gh-fix-ci** workflow — Manual CI debugging when the watcher finds issues
- **ticket-pr-validation-loop** workflow — Ticket-bound automation that uses CI watching after each pushed PR head
- **review-and-fix** / **ticket-review-and-fix** workflows — Review + fix loops that benefit from CI watching
- **ci-feedback-loop** rule (`rules/ci-feedback-loop.md`) — Always-on expectation that pushed changes are followed to a green CI state
- **testing** — Test patterns and coverage strategy
