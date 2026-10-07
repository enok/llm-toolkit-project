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
4. **Principles behind it** (section below): how the pattern realises the
   design and architecture principles it applies, and where it can violate them.
5. The standard explanation, in your own words, and the generic diagram.
6. The worked example: example diagram and the code (whole repo files,
   identical under the hash check of `editor-verification.md`, one block per file).
7. Links (repo, post), curated videos, one closing takeaway.

A reader new to the topic still needs steps 5 and 6, and the repo teaches
them; they just no longer open the article.

## Post order (LinkedIn or similar)

- The first lines, before the "see more" cut, state the non-obvious claim.
- Then two or three short points: one architecture use and one or two cited
  framework appearances.
- One line names the two or three main principles the pattern realises (from
  the repo's principles page).
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
7. **Snippets obey the cited doc.** Check every code snippet that uses a framework API against
   the cited official page before the approval gate: methods the page describes as
   mutually exclusive are not called together, and no source is a mirror or copy of the
   official docs (rule 1).

## Choosing the architecture applications

Look for seams where behavior is selected or plugged in: a policy chosen by
configuration at a service boundary, per-tenant or per-market rules behind
one port, interchangeable adapters behind a contract. For each one state what
varies, what must stay fixed, the gain and the cost. Boxes in the diagram are
components or services, not classes; draw it with
`skills/diagram-authoring/SKILL.md` and check it at the destination width
(`skills/image-quality-inspection/SKILL.md`).

## Principles behind it

Every study article correlates the pattern with other design and architecture
principles, also when the topic is not widely covered. The source is the repo's
`docs/06-design-principles.md`
(`skills/multi-language-study-repo/references/design-principles-doc.md`); the
article and the post quote it and add nothing the page does not hold. Place the
section after the architecture and framework sections, before or inside the
standard explanation. Contents:

| Principle | How the pattern realises it | Where it can be violated |
| --- | --- | --- |
| `<principle>` (SOLID, object-oriented, general or architecture) | `<participant or seam>` | `<misuse>` |

The table is the format of the repo page. Medium has no tables: `paste-recipe.md` (section 1) says to
convert a `<table>` to a bullet list (`Label: value`) or a mode-0 `<pre>` with aligned columns,
`medium_paste_html.py build` does not convert tables, and `check` fails on any `<table>`. So the
article renders each row as one list item, `<principle>: <how> (bends when <misuse>)`. An image of
the table is an alternative (general guidance, not observed in this toolkit's sessions; then apply
the legibility check of `skills/image-quality-inspection/references/destination-legibility.md`).

- One row per principle that holds (SRP, OCP, LSP, ISP, DIP, the
  object-oriented design principles of the study source, DRY, KISS, YAGNI,
  separation of concerns, cohesion and coupling, least knowledge, the dependency
  rule, policy vs detail, stable abstractions); a principle that does not apply
  gets a one-line reason on the page and is not forced into the table.
- One short paragraph on the tension: which principle the pattern can violate
  when misused (for example YAGNI or KISS when only two fixed variants exist)
  and the rule of thumb for when not to use it.
- In Highlight 1, name the principle each architecture application realises.
- Principle definitions are generic. Any attribution (who coined a principle) or
  quote needs a primary-source citation or is left out; never attribute from
  memory.

## Before the approval gate

- The opening promises the non-obvious angle; the standard material follows.
- Every framework claim has a fact-table row with an official source and a
  check date on the day (see rule 2).
- The "Principles behind it" section matches the repo's principles page, with
  the tension; the post names the main principles in one line.
- The post's image is the architecture diagram and reads at feed width.
- Every code snippet that uses a framework API was checked against the cited page (rule 7).
- Article and post agree.

The angle changes the order of content, not the approval gates: the full
text is still shown as `NOT POSTED` first. Changing an already published
story is an edit that needs approval; a published LinkedIn post cannot change
its media, so a new image means a new post with a "More..." pointer in the old post
(`skills/linkedin-publishing/references/repost-and-delete.md`).
