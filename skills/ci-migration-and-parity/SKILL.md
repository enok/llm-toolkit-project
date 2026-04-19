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

## Related Skills

- **release-manager** — When CI migration affects release processes
- **shell-scripting** — CI scripts follow shell best practices
- **best-practices** — CI pipeline architecture patterns
