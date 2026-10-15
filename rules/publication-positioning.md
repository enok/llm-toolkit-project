---
trigger: always_on
description: Apply whenever an agent drafts, reviews, edits, or replaces a public article or social post for the user; profile-first positioning, AIDA, budgets, sourced claims, NOT POSTED drafts, publication-reviewer gate
---

# Publication Positioning

Use this rule whenever an agent drafts, reviews, edits, or replaces a public
article (blog, Medium, or similar) or a social post (LinkedIn or similar) on
the user's behalf. A correct, complete draft can still miss its purpose; the
positioning profile turns that purpose into limits a script and a reviewer can
check.

## Contract

1. **Profile first.** Before writing, read the consumer's positioning profile:
   `PUBLICATION-PROFILE.md` at the project root, or the path the project
   instructions name. When none exists, ask the user for the target role and
   primary focus; if that goes unanswered, use the toolkit defaults in
   `skills/medium-publishing/references/positioning-profile.md` and say so
   with the draft.
2. **AIDA order.** Every piece moves through Attention, Interest, Desire, and
   Action, in that order (`skills/medium-publishing/references/aida-narrative.md`).
   A short system-design article includes one sentence naming the main
   principles it applies; in the teaser post that sentence is optional.
3. **Position at the profile's level.** The title, subtitle, and hook (a
   post's first paragraph, before the first blank line, within the profile's
   hook budget, default 200 characters, as the script measures it) name a
   concept at the profile's target-role level and primary focus. A lower-level detail (for example a class-level
   pattern name) stays out of them and appears in the body as the mechanism,
   unless the profile allows it. Every noun in the title and hook is
   delivered by the body.
4. **Budgets from the profile.** Length, hook length, code blocks and lines,
   images, and hashtags follow the profile and are enforced by
   `skills/medium-publishing/scripts/check_publication.py`. A non-zero exit
   means the draft is not ready. Detail beyond the budget stays in the source
   repo and is linked.
5. **Sourced claims.** Every fact, number, result, and hashtag topic is backed
   by the source repo or its fact table. An interpretation the source does not
   state is labelled as the author's reading. A claim that fails the check is
   dropped, not softened.
6. **Reviewer gate.** Every draft goes through the read-only
   `tool-subagents/publication-reviewer.md` and is shown as ready only after a
   `pass`. On `fail`, fix the listed defects; on `blocked` (it cannot judge:
   the profile, the sources, or a draft is missing), supply the missing input.
   Then run it again; neither outcome is shown as ready.
7. **Drafts are shown NOT POSTED.** Show the exact text labelled `NOT POSTED`
   with the profile used (path and budgets), an AIDA stage map (one line per
   stage naming what carries it), the checker output, and the reviewer verdict.
8. **Approval mode from the profile**, exactly one of two. `gated` (the
   default): every external write, including creating a platform draft, needs
   explicit approval of that action. `drafts-only`: creating the article draft
   and the post draft is pre-approved, and nothing else is. In both modes each
   publish, post, edit, delete, pointer, and unlist needs explicit approval of
   that action (`rules/external-write-authorization.md`,
   `rules/human-comment-reply-gate.md`); `drafts-only` is not an exemption.
9. **Edits and replacements** of a published piece follow the same contract.
   An edit in place follows the retrofit section of `aida-narrative.md`; a new
   piece that replaces an old one follows
   `skills/medium-publishing/references/replace-published-story.md`. Check the
   public page and every back-link afterwards.

Keep person, company, and project specifics in the consumer's profile, never in
shared toolkit surfaces.
