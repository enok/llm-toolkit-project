---
description: Keep paired docs, notebooks, and deliverables synchronized across languages or presentation variants
---

# Paired Doc Sync Workflow

Use this workflow when a repository keeps multiple versions of the same content, such as English and translated docs, paired notebooks, or report and presentation variants.

---

## Step 1: Identify the artifact pairs

Find the files that should move together, for example:

- `README.md` and `README.<locale>.md`
- `docs/*.md` and `docs/*.<locale>.md`
- `notebooks/*.ipynb` and localized notebook variants
- A narrative report plus the notebook or script that produced it

List any pairs that are intentionally one-sided.

---

## Step 2: Choose the source of truth

For each pair, state which version leads the change:

- Original language first
- Generated report first
- Notebook first
- Code first

If that source of truth is unclear, decide it before editing multiple artifacts.

---

## Step 3: Sync meaning, not just text

When updating the secondary artifact, verify all of the following:

- Commands and paths
- Dataset names and metric labels
- Table and figure references
- Dates, time windows, and counts
- Terminology and domain vocabulary

Do not let one version drift on technical details while matching only the prose.

---

## Step 4: Preserve reviewability

Prefer changes that reviewers can compare directly:

- Keep section ordering aligned across versions when possible
- Reuse filenames and numbering conventions
- Add a short note when content intentionally differs by audience

---

## Step 5: Record unresolved drift explicitly

If you cannot update both sides in one pass, leave a clear note describing:

- Which files are still out of sync
- What changed in the source of truth
- What remains to translate or adapt

Silent drift is worse than an explicit TODO.
