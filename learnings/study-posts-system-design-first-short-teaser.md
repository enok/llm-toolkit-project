---
title: Study articles are short system design stories with the pattern inside, and the post is a short teaser
category: toolchain
created: 2026-10-12
tags: [medium, linkedin, system-design, positioning, positioning-profile, article-length, teaser, hashtags, aida, guard-script, publication-reviewer, approval-gate]
---

# Problem

A first study publication passed every gate and still missed its purpose, which is to position
the author at the target role's level (for example an architect-level role) with system design as
the main focus. The article was a full tutorial of nearly 6,000 words (a 24 minute read) whose
title named a class-level pattern, so the system design story was one section among many. The
LinkedIn post repeated the tutorial in miniature: long, nineteen hashtags, several calls to
action. AIDA was present (`learnings/posts-need-aida-structure-and-role-positioning.md`), but
it only fixes the order of a piece, not its subject or length, and the role, focus, and
budgets were written nowhere the flow could read. Signature:
`spec-gap/publication-not-positioned-for-target-role`.

# Failed Approaches

- Retitling alone: a higher-level title over a 6,000 word tutorial promised more than a skim
  could confirm, and the pattern name in the subtitle still read as a class-level topic.
- Counting hashtags by topic coverage ("one per topic the post names"): with no cap the post
  tagged everything it mentioned, and the tags stopped signalling a focus.
- Keeping the repo's teaching content in the article "because the repo links it anyway": the
  reader never reached the system design story, and the article competed with the repo it linked.

# Solution

Follow `skills/medium-publishing/references/positioning-profile.md`, `system-design-article.md`,
`aida-narrative.md`, and `rules/publication-positioning.md`. The numbers below are toolkit
defaults; a consumer's profile overrides them.

1. Write the positioning down once, in the consumer's `PUBLICATION-PROFILE.md`: target role,
   focus, article and post budgets, hashtag cap, approval mode. Intake reads it or creates it
   instead of asking piecemeal (`workflows/study-repo-to-publication.md`, Phase 0).
2. The article is one short system design story: at most 1,500 words by toolkit default (1,300
   in an example consumer profile), 2-3 diagrams led by a hero system-design diagram, at most one code block of 15 lines or fewer, a title and subtitle
   that name the system design problem or capability. The full pattern explanation, class-level
   diagrams, code, and principles page stay in the repo and are linked.
3. The pattern is internal: never in the title, subtitle, or hook, introduced in the body as the
   mechanism. Framework sightings, if used, are supporting evidence and each is cited.
4. The post is a teaser for the article: at most 1,300 characters, the hook (first paragraph) at
   most 200, the article link as the single call to action (repo link optional), at most 5
   hashtags each backed by text in the post, the hero diagram as the image. Medium topics stay
   five and system-design-led.
5. Validate every draft before it is shown: `tool-subagents/publication-reviewer.md` and
   `skills/medium-publishing/scripts/check_publication.py`, results shown with the AIDA stage
   map (`workflows/study-publication-medium-linkedin.md`). Honour the profile's approval mode
   (`gated` or `drafts-only`): `drafts-only` pre-approves creating the two drafts only; publish,
   post, edit, pointer, and unlist still need explicit approval.
6. A live publication that misses the profile is replaced, not retitled: a new story and a new
   post, a pointer on the old ones (`skills/medium-publishing/references/replace-published-story.md`).

# Why

The requirement (a short, system-design-first piece that sells the article) was knowable, but
nothing in the flow measured it: the old guidance fixed the order of content and let length,
title level, and hashtag count float, so a complete, correct, cited draft satisfied every check.
A written profile makes the intent readable, and hard budgets plus a script that fails on a
pattern name in the title, an oversized article or post, or a sixth hashtag turn it into an
acceptance criterion that cannot be skipped. Retitling cannot fix a piece whose shape is wrong.
