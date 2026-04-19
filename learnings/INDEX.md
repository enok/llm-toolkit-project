# Learnings Index

Fast-scan index of every committed learning. **Read this at session start** (per `skills/error-driven-learning/SKILL.md`) to skip directly to the happy path on previously-solved problems.

**Format:** one line per learning — link, one-sentence summary, and tags for keyword matching.

**Update rule:** whenever `learnings/<new>.md` is added, append a line here in the same commit. When a learning is superseded, mark the old line with `~~strikethrough~~` and note the replacement.

---

## Index

### Architecture

- [`llm-toolkit-junction-architecture.md`](./llm-toolkit-junction-architecture.md) — Multi-repo LLM tooling via Windows junctions: zero duplication, zero git traces (`llm-toolkit`, `junctions`, `gitignore`, `multi-repo`, `windows`).
- [`llm-adaptive-skill-loading.md`](./llm-adaptive-skill-loading.md) — Progressive/two-tier skill loading keeps session context under 1 KB (`skills`, `context-optimization`, `progressive-disclosure`).

### API

- [`transparency-portal-api.md`](./transparency-portal-api.md) — Portal da Transparência API auth, endpoint catalog, and pagination (`transparency-portal`, `api`, `brazil`, `cgu`, `sanctions`, `ceis`, `cnep`, `cepim`).

---

## Scanning Tips

- Match by **tags** first (grep the tags line) — fastest filter.
- Match by **title** second.
- If multiple learnings match, read the newest (`created:` date) first.
- If nothing matches, proceed normally and watch for capture triggers (see `skills/error-driven-learning/SKILL.md` § Phase 2).

## Hygiene Checklist When Adding A Learning

- [ ] File created under `learnings/<kebab-case>.md` following the template in `learnings/README.md`.
- [ ] Frontmatter has `title`, `category`, `created`, `tags`.
- [ ] Body has `# Problem`, `# Failed Approaches`, `# Solution`, `# Why` sections.
- [ ] Line appended to the appropriate category above in this INDEX.
- [ ] User approval gate passed (per `workflows/capture-learning.md` §6).
- [ ] Committed with a descriptive message.
