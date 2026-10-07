---
title: Content angle for well-known topics
tags: [medium, linkedin, content-angle, non-obvious-applications, citations, fact-table, design-patterns]
---

# Content angle for well-known topics

Use this when the topic is widely covered: design patterns, common
algorithms, standard data structures, textbook protocols. Readers have met
the standard explanation many times and most posts repeat it. So the article
and the social post lead with what is rarely posted, and the standard
explanation, diagrams and code follow. Nothing is removed; the order changes.

## Article order

1. Title, subtitle and opening paragraph promise the non-obvious part: one
   concrete architecture-level use, or one surprising "it hides inside
   `<framework>`" fact. Not "what is `<topic>`".
2. **Highlight 1 - architecture applications.** Where the concept shapes a
   seam between services, modules or layers rather than between two classes.
   At least one diagram of it (the repo's architecture page is the source).
3. **Highlight 2 - where it hides in widely used frameworks and libraries.**
   Three to five appearances in `<framework>`, each cited (next section).
4. The standard explanation, in your own words, and the generic diagram.
5. The worked example: example diagram and the code (whole repo files,
   byte-identical, one block per file).
6. Links (repo, post), curated videos, one closing takeaway.

A reader new to the topic still needs steps 4 and 5, and the repo teaches
them; they just no longer open the article.

## Post order (LinkedIn or similar)

- The first lines, before the "see more" cut, state the non-obvious claim.
- Then two or three short points: one architecture use and one or two cited
  framework appearances.
- Then the article link and the repo link; at most 5 hashtags.
- The image is the architecture-application diagram, checked at feed width.
  The generic diagram is only a fallback when no architecture view exists.
- The post claims nothing the article's fact table does not hold.

## Citing "hidden in `<framework>`" claims

Every such claim is a row in a fact table kept with the repo (in the
architecture page, or a docs page of its own when the repo has no architecture
view), so the article and the post quote the same checked text:

| Claim | Type or API | Version | Official source | Checked on |
| --- | --- | --- | --- | --- |
| `<framework>` applies `<topic>` in `<type>` | `<qualified type or method>` | `<x.y>` | `<official docs, API reference, release notes or maintainers' source repo URL>` | `<YYYY-MM-DD>` |

Rules:

1. **Official source only**: the framework's own documentation, API
   reference, release notes, or the maintainers' source repository. Not
   blogs, forums, Q&A sites, books, or model memory.
2. **Checked on the day.** Open the source the day the claim is written or
   finalised, record the date and the version, and re-check when publication
   happens on a later day.
3. **Say only what the source supports.** If it names the concept, attribute
   it ("the documentation describes `<type>` as ..."). If it only shows the
   behavior (a type that accepts a pluggable algorithm), write "plays the
   `<role>` role" and mark it as your reading. Never claim internals the
   source does not state.
4. **Unreachable source** (sandbox egress block, HTTP 403): the claim is
   unverified. Check it from the user's machine or drop it. Never fill the
   gap from memory.
5. **Few and solid**: three to five cited claims beat ten weak ones. A claim
   that fails the check is dropped, not softened.
6. Quote sparingly, with attribution, and link for the rest.

## Choosing the architecture applications

Look for seams where behavior is selected or plugged in: a policy chosen by
configuration at a service boundary, per-tenant or per-market rules behind
one port, interchangeable adapters behind a contract. For each one state what
varies, what must stay fixed, the gain and the cost. Boxes in the diagram are
components or services, not classes; draw it with
`skills/diagram-authoring/SKILL.md` and check it at the destination width
(`skills/image-quality-inspection/SKILL.md`).

## Before the approval gate

- The opening promises the non-obvious angle; the standard material follows.
- Every framework claim has a fact-table row with an official source and a
  check date on the day (see rule 2).
- The post's image is the architecture diagram and reads at feed width.
- Article and post agree.

The angle changes the order of content, not the approval gates: the full
text is still shown as `NOT POSTED` first. Changing an already published
story is an edit that needs approval; a published LinkedIn post cannot change
its media, so a new image means repost plus delete
(`skills/linkedin-publishing/references/repost-and-delete.md`).
