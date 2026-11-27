---
title: LinkedIn skill name variants are the same record, and the 100-skill cap blocks adds
category: toolchain
created: 2026-10-22
tags: [linkedin, skills, profile, standardized-names, cap, endorsements, replace]
---

# Problem

A planned "replace old skill with better-named skill" step failed for many pairs
(capitalization or suffix variants) with "This skill is already on your profile".
Other requested names did not exist in the vocabulary, and the final add failed
because the profile sat at the 100-skill cap.

# Failed Approaches

- Deleting the old skill and re-adding the new name (would have lost
  endorsements for nothing).
- Typing a desired name and pressing Save without picking a suggestion.
- Planning additions without counting the final total.

# Solution

- Treat a variant that triggers "already on your profile" as a no-op replacement
  and report it; endorsements are preserved.
- Use the closest standardized suggestion and list every substitution in the
  final report ("Software Engineering" -> "Software Development").
- If a name does not exist, keep the existing near-equivalent and report it.
- Compute `current - removals + additions` before starting; if it exceeds 100,
  propose cuts first. Delete only after the replacement exists and endorsements
  are checked.

# Why

LinkedIn skills are standardized entities; labels are aliases of one record, and
the cap is enforced at save time, so planning has to happen before the first add.
