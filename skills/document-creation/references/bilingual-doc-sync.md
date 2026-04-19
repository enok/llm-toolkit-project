---
trigger: always_on
description: Keep English-first documentation and maintained localized counterparts aligned
---

# Bilingual Documentation Sync

When a repository maintains documentation or notebooks in more than one language, language drift becomes a product risk.

## Source Of Truth

- Keep the primary technical source in English unless the project documents a different policy.
- If a maintained localized counterpart exists, update it in the same change or explicitly note that it is temporarily behind.
- Do not silently change domain terms in one language only.

## Translation Scope

- Translate narrative markdown, titles, captions, and user-facing terminology.
- Keep code, dataset identifiers, schema keys, and command names stable unless the project intentionally provides a translated access layer.
- If the project uses translation dictionaries for dataset or column names, update those mappings together with the docs that depend on them.

## Review Checklist

When a change affects docs or notebooks, check:

- paired `README` or localized documents
- translated notebook markdown
- glossary or translation maps
- screenshots, charts, and table labels
- cross-links between language variants

## Acceptable Drift

If the localized version must lag temporarily, say so directly in the change summary or the document itself. Do not leave readers guessing whether the mismatch is intentional.
