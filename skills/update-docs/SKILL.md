---
name: update-docs
description: |
  Update documentation from staged changes. Use to keep docs in sync with code
  changes, or when documentation needs to be aligned with implementation.
license: MIT
---

# Update Docs

Keep documentation in sync with code and configuration changes.

> **Reference**: For complete workflow, see `workflows/update-docs.md`

## Quick Reference

### Identify Doc Impact
1. Review staged changes (what's being modified)
2. Identify which docs need updates
3. Check for API changes (specs, OpenAPI, README examples)
4. Check for config changes (deployment docs, env vars)
5. Check for architecture changes (architecture docs, diagrams)

### Update Sequence
1. Update code/configuration first (committed changes)
2. Update corresponding documentation
3. Verify examples in docs still work
4. Cross-reference related docs for consistency

### Common Doc Locations
- `README.md` — quick start, examples
- `docs/` — detailed documentation
- `API.md` or `openapi.yaml` — API specs
- `CONTRIBUTING.md` — development setup
- `ARCHITECTURE.md` — design decisions

### Don't Forget
- Code examples in docs
- Environment variable documentation
- Architecture diagrams
- Changelog or release notes

## When to Apply

- After making code changes that affect public interfaces
- Adding new configuration options
- Changing deployment procedures
- Modifying architecture or data flow
- Before opening a PR (docs are part of the change)

## Related

- `workflows/update-docs.md` — Complete workflow
- `skills/document-creation` — Creating new docs
