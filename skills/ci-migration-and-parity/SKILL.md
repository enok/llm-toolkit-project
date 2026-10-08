---
name: ci-migration-and-parity
description: >
    Keep parity while moving or comparing CI pipelines across systems. Trigger when the user
    is migrating from one CI system to another, validating GitHub Actions against an older
    pipeline, or trying to prevent deployment/test/release drift across CI implementations.
---

# CI Migration and Parity

Use this skill when multiple CI systems or generations must agree.

## When to Apply

- Migrating from one CI system to another (e.g., Jenkins → GitHub Actions)
- Validating a new pipeline against an existing one
- Preventing deployment/test/release drift across CI implementations
- Comparing CI behavior across environments or branches

## Workflow

1. **Inventory the current pipelines and classify them:**
   - build/test
   - deploy/release
   - code quality/security scanning
   - scheduled or manual operational jobs
2. **Compare parity dimensions:**
   - trigger conditions (push, PR, schedule, manual)
   - inputs and secrets
   - caching and artifacts
   - approval gates
   - rollback behavior
   - notifications
3. **Find drift before deleting the old pipeline.** Run both in parallel during the transition.
4. **Prefer explicit parity checklists** over "looks equivalent."
5. **If release behavior is involved**, pair with **release-manager**.

## Output

Return:
- pipeline inventory (old and new)
- parity matrix (dimension × pipeline)
- missing behavior or drift
- cutover recommendation and timeline

## Non-Goals

- Do not delete the old pipeline before parity is verified.
- Do not assume "same YAML" means "same behavior" — test the output.

## Known pitfalls

- Give every CI job that branch protection will require an explicit `name:` equal to its id, and do not use `strategy.matrix` for a required job (matrix-expanded names such as `python (3.12)` do not qualify); run several versions sequentially inside one job. Add required checks only after the first green PR run, using the names read back from it. See `learnings/branch-protection-required-checks-need-stable-job-names.md`. (sig: tool-misuse/required-check-matrix-job-name)
- When a PR removes a CI job, rewrite the required status checks to the remaining job names BEFORE merging it: a required check whose job no longer runs never reports, and the PR waits forever. See `learnings/required-checks-must-follow-removed-ci-jobs.md`. (sig: coordination/required-check-removed-job)
- Update required status checks by sending a JSON body with `--input <file>` to the PATCH `required_status_checks` endpoint; array form fields such as `gh api -f contexts[]=<check>` did not update them. See `learnings/gh-api-array-fields-for-required-checks.md`. (sig: tool-misuse/gh-api-array-fields-for-required-checks)

## Related Skills

- **release-manager** — When CI migration affects release processes
- **shell-scripting** — CI scripts follow shell best practices
- **best-practices** — CI pipeline architecture patterns
