---
description: Keep English and localized documentation or notebooks aligned during code and analysis changes
---

# Bilingual documentation sync workflow

Use when a repository maintains technical docs, reports, or notebooks in English plus one or more localized counterparts.

## Steps

1. Start from the English source document or notebook unless the project states a different source-of-truth policy.
2. Update the closest localized counterpart in the same change whenever the content is meant to stay in sync.
3. Keep code snippets, commands, dataset identifiers, and schema terms stable unless the project intentionally exposes translated names.
4. If the project uses translation dictionaries, glossaries, or helper loaders, update them together with the narrative docs.
5. Verify paired links, headings, captions, and file references across language variants.
6. If a localized version must lag, note that drift explicitly in the doc or change summary instead of leaving a silent mismatch.
