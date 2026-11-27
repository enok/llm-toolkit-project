# Learnings Index

Fast-scan index of **pending learning intake items**: lessons captured before their owning skill, rule or workflow was clear. It is normally empty, because a lesson whose owner is clear goes straight into that owner (`rules/error-driven-learning.md`). Read it at session start, after the owning assets' `## Known pitfalls` (per `skills/error-driven-learning/SKILL.md`).

**Format:** one line per pending item — link, one-sentence summary, and tags for keyword matching.

**Update rule:** a new intake file `learnings/<kebab-topic>.md` gets its line here in the same commit. When the item is migrated into its owner, the file and its line are deleted in that change, at the latest in the next toolkit maintenance pass. A migrated learning never keeps its file.

---

## Pending intake

_None._

---

## Scanning Tips

- Match by **tags** first (grep the tags line) — fastest filter.
- Match by **title** second.
- If multiple items match, read the newest (`created:` date) first.
- If nothing matches, proceed normally and watch for capture triggers (see `skills/error-driven-learning/SKILL.md` § Phase 2).

## Hygiene Checklist When Adding An Intake Item

- [ ] The owner is genuinely unclear; otherwise write the lesson into the owner instead (`workflows/capture-learning.md` §3).
- [ ] File created under `learnings/<kebab-topic>.md` following the template in `learnings/README.md`.
- [ ] Frontmatter has `title`, `category`, `created`, `tags`.
- [ ] Body has `# Problem`, `# Failed Approaches`, `# Solution`, `# Why` sections.
- [ ] Line added under "Pending intake" above (replacing `_None._`).
- [ ] User approval gate passed (per `workflows/capture-learning.md` §7).
- [ ] Committed with a descriptive message.
