---
trigger: always_on
description: Apply whenever an agent drafts, reviews, edits, or replaces a public article or social post for the user; profile-first positioning, AIDA, budgets, sourced claims, NOT POSTED drafts, profile check, owner approval
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
   primary focus; if that goes unanswered, use the toolkit defaults and say
   so with the draft: article <= 1,500 words, 2-3 diagrams, at most one code
   block of <= 15 lines; post <= 1,300 characters, hook <= 200, <= 5
   hashtags; `gated` approval.
2. **AIDA order.** Every piece moves through Attention, Interest, Desire, and
   Action, in that order.
   A short system-design article includes one sentence naming the main
   principles it applies; in the teaser post that sentence is optional.
3. **Position at the profile's level.** The title, subtitle, and hook (a
   post's first paragraph, before the first blank line, within the profile's
   hook budget, default 200 characters) name a
   concept at the profile's target-role level and primary focus. A lower-level detail (for example a class-level
   pattern name) stays out of them and appears in the body as the mechanism,
   unless the profile allows it. Every noun in the title and hook is
   delivered by the body.
4. **Budgets from the profile.** Length, hook length, code blocks and lines,
   images, and hashtags follow the profile and are enforced by the shape
   check in `workflows/study-publication-medium-linkedin.md`. A failed check
   means the draft is not ready. Detail beyond the budget stays in the source
   repo and is linked.
5. **Sourced claims.** Every fact, number, result, and hashtag topic is backed
   by the source repo or its fact table. An interpretation the source does not
   state is labelled as the author's reading. A claim that fails the check is
   dropped, not softened.
6. **Profile check.** Before a draft is shown as ready, the drafting assistant
   (or a separate read-only validator lane, when the orchestrator dispatches
   one) checks it against the consumer's publication profile and
   `rubrics/technical-content.md` if that file exists: budgets, AIDA stage map,
   title and hook positioning, sourced claims, hashtags, article-post
   agreement. Fix every defect found; if the profile, the sources or a draft is
   missing, supply the missing input first. A draft with an open defect is not
   shown as ready, and it stays `NOT POSTED` until the owner approves.
7. **Drafts are shown NOT POSTED.** Show the exact text labelled `NOT POSTED`
   with the profile used (path and budgets), an AIDA stage map (one line per
   stage naming what carries it), the checker output, and the profile-check result.
8. **Approval mode from the profile**, exactly one of two. `gated` (the
   default): every external write, including creating a platform draft, needs
   explicit approval of that action. `drafts-only`: creating the article draft
   and the post draft is pre-approved, and nothing else is. In both modes each
   publish, post, edit, delete, pointer, and unlist needs explicit approval of
   that action (`rules/external-write-authorization.md`,
   `rules/human-comment-reply-gate.md`); `drafts-only` is not an exemption.
9. **Edits and replacements** of a published piece follow the same contract.
   An edit in place keeps the AIDA order; a new piece that replaces an old one
   follows the Replacement Path of `workflows/study-publication-medium-linkedin.md`. Check the
   public page and every back-link afterwards.

Keep person, company, and project specifics in the consumer's profile, never in
shared toolkit surfaces.
