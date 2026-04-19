# Bilingual Documentation Rules (Template)

> **This is a template.** Copy and fill in your repository's source-of-truth language, paired paths, and translation conventions.

## Source of Truth

- **Primary language:** [English / Portuguese / other]
- **Mirrored languages:** [locale codes such as pt-BR, es-ES, fr-FR]
- **Who consumes each version:** [engineering, academic review, local stakeholders, public docs]

## Paired Files

| Primary file | Mirrored file | Notes |
|--------------|---------------|-------|
| `README.md` | `README.[locale].md` | [structure should stay aligned] |
| `docs/[topic].md` | `docs/[topic].[locale].md` | [any accepted divergence] |
| `notebooks/[name].ipynb` | `notebooks/[name].[locale].ipynb` | [narrative only or full parity] |

## Translation Rules

- Keep code identifiers, dataset keys, schema names, and command examples in their canonical form.
- Translate narrative text, report titles, axis labels, and user-facing explanations.
- When the repo uses translation helpers, list them here:
  - `[path/to/translation-map.py]`
  - `[path/to/localized-loader.py]`

## Update Policy

- Update both language versions in the same change when possible.
- If a mirrored file intentionally lags, add a note and open a follow-up task.
- Decide whether notebook conclusions must stay identical across languages or can vary by audience.
