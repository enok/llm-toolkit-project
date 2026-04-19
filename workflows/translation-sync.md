---
description: Keep English and translated docs, labels, and examples synchronized after changes
---

# Translation Sync Workflow

Use when the repo maintains paired docs, bilingual reports, or translated dataset labels.

## Steps

1. Identify the source change:
   - documentation update
   - notebook narrative update
   - translated loader or display label update
2. Find the paired artifacts that represent the same concept in other languages.
3. Update both sides while preserving:
   - identical commands and paths
   - identical factual claims and time ranges
   - stable code identifiers and dataset keys
4. If translation mappings exist in code, update them together with doc text.
5. Verify that examples and screenshots or figure captions still correspond to the same output.
6. If translation is intentionally delayed, note that explicitly in the task summary or doc stub.

## Exit Criteria

- The paired materials communicate the same engineering truth.
- Code-facing identifiers remain stable.
- Any intentional lag is documented instead of being silent.
