---
description: Run the Documentation Reviewer specialist validation workflow
---

# Documentation Reviewer Validation

Use this workflow when documentation created or changed by any agent, chat,
automation, script, or human should be validated before approval, merge, push,
publication, or handoff. `rules/documentation-review-required.md` makes this
mandatory for the documentation surfaces it lists.

## Steps

1. Establish repo, base/head, dirty-tree ownership, docs changed, destination,
   audience, and the source evidence each doc claims to summarize.
2. Load only the relevant rules, workflows, skills, docs, source files, linked
   tickets/threads, generated artifacts, and tool-config surfaces.
3. Invoke or follow `tool-subagents/documentation-reviewer.md`.
4. Reduce findings locally: accept only evidence-backed, in-scope issues and
   reject taste-only rewrites unless the doc is confusing for its audience.
5. Fix documentation when the user requested implementation; otherwise provide
   exact findings and draft-only human-facing replies
   (`rules/human-comment-reply-gate.md`).
6. Run the narrowest meaningful validation: index checks, link/render checks,
   workflow size checks, tool-config sync checks, artifact QA
   (`skills/image-quality-inspection/SKILL.md`), or security gates as
   applicable.
7. Report findings, changes, validation, skipped gates, residual risk, and
   reusable learning.

---

## Evolution

If this specialist misses a recurring issue or is too noisy, run
`workflows/documentation-reviewer-evolution.md`.
