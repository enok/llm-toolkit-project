---
trigger: always_on
description: Keep English-first documentation and localized counterparts aligned — translation scope, review checklist, and drift policy
---

# Documentation Sync

When a repository maintains documentation or notebooks in more than one language, language drift becomes a product risk.

## Source of Truth

- Treat one language version as the source of truth for structure and technical meaning (English unless the project documents a different policy).
- If a maintained localized counterpart exists, update it in the same change or explicitly note that it is temporarily behind.
- Do not silently change domain terms in one language only.
- When a repository has mirrored files such as `README.md` and `README.<locale>.md`, or English and localized notebook pairs, check both sides before concluding documentation is complete.

## Translation Scope

- Translate narrative markdown, titles, captions, and user-facing terminology.
- Keep code identifiers, dataset keys, stable API or schema names, and command names in their canonical language.
- If the project uses translation dictionaries for dataset or column names, update those mappings together with the docs that depend on them.
- Do not translate away domain-specific legal or statistical terms unless the repository already has an accepted glossary for them.

## Review Checklist

When a change affects docs or notebooks, check:

- paired `README` or localized documents
- translated notebook markdown
- glossary or translation maps
- screenshots, charts, and table labels
- cross-links between language variants

## Acceptable Drift

If the localized version must lag temporarily, say so directly in the change summary or the document itself. Do not leave readers guessing whether the mismatch is intentional.
