---
title: Content angle for well-known topics
tags: [medium, linkedin, content-angle, non-obvious-applications, citations, fact-table, design-patterns, aida, full-tutorial, teaser, positioning-profile]
---

# Content angle for well-known topics

Use this when the topic is widely covered: design patterns, common
algorithms, standard data structures, textbook protocols. Readers have met
the standard explanation many times and most posts repeat it, so a piece that repeats it
earns no attention.

The publication profile ([positioning-profile.md](positioning-profile.md)) decides which shape
applies:

- Default, system-design-first: the article is a short system design story with the study topic
  inside it ([system-design-article.md](system-design-article.md)) and the post is a short teaser
  (post order below). Non-obvious applications and cited framework facts are supporting evidence in
  the body, never the hook, and the standard explanation, diagrams and code stay in the repo.
- Full tutorial, only when the profile asks for it: the article and the post lead with what is
  rarely posted (the non-obvious application or the cited framework fact), and the standard
  explanation, diagrams and code follow (article order below). Nothing is removed; the order changes.

AIDA (Attention, Interest, Desire, Action) frames how the article and the post move from the
opening to the close. Both orders below are marked with their AIDA stage and agree with the
mappings in [aida-narrative.md](aida-narrative.md).

## Article order (full-tutorial profile only)

Use this order only when the profile asks for a full tutorial. The default article is
[system-design-article.md](system-design-article.md).

1. Attention: title, subtitle and opening paragraph promise the non-obvious
   part: one concrete architecture-level use, or one surprising "it hides
   inside `<framework>`" fact. Not "what is `<topic>`". The title names the
   highest-level concept the body supports (`aida-narrative.md`).
2. Interest: the problem paragraph, right after the hook: the problem, the
   context, why it matters.
3. Desire: a short "what you get" list (benefits and results the repo holds),
   then the body below.
4. **Highlight 1 - architecture applications.** Where the concept shapes a
   seam between services, modules or layers rather than between two classes.
   At least one diagram of it (the repo's architecture page is the source).
5. **Highlight 2 - where it hides in widely used frameworks and libraries.**
   Three to five appearances in `<framework>`, each cited (next section).
6. **Principles behind it** (section below): how the pattern realises the
   design and architecture principles it applies, and where it can violate them.
7. The standard explanation, in your own words, and the generic diagram.
8. The worked example: example diagram and the code (whole repo files,
   identical under the hash check of `editor-verification.md`, one block per file).
9. Action: a closing next-step section, the call to action: the outcome or
   recommendation as the closing takeaway, then the links (repo, post) and the
   curated videos.

A reader new to the topic still needs steps 7 and 8, and the repo teaches
them; they just no longer open the article.

## Post order (LinkedIn or similar): the teaser

The post is a short teaser whose job is to send readers to the article. Its budgets come from the
profile; toolkit defaults are at most 1,300 characters in total and a hook of at most 200.

- Attention: the hook is the first paragraph of the post (the text before the first blank line),
  at most the profile's hook budget (default 200 characters), and states the system design problem
  or capability (under a full-tutorial profile only: the non-obvious claim). No study-topic name in
  the hook under a system-design-first profile (`check_publication.py post --forbid <topic>`).
- Interest: two or three lines on the problem, the context, and why it matters.
- Desire: two or three short points on what the article shows: a design decision and its
  trade-off, a result the repo holds (under a full-tutorial profile: one architecture use and one or
  two cited framework appearances). A line naming the two or three main principles the pattern
  realises (from the repo's principles page) is optional here; the article carries the required
  sentence.
- Action: the article link as the one primary call to action, the repo link optional and
  secondary, and one specific question.
- After the Action, at most 5 hashtags (or the profile cap), chosen by positioning with the
  profile's primary focus first, each named in the post text, none for topics it does not mention
  (`skills/multi-language-study-repo/references/tags-and-topics.md`).
- The image is the article's hero diagram, checked at feed width (under a full-tutorial profile:
  the architecture-application diagram). The generic diagram is only a fallback when no
  architecture view exists.
- The post claims nothing the article's fact table does not hold.

## Citing "hidden in `<framework>`" claims

This section applies whenever a piece claims a framework appearance: at most two in the short
article, three to five in a full tutorial. Every such claim is a row in a fact table kept with the repo (in the
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
5. **Few and solid**: a few cited claims beat many weak ones (at most two in the short article,
   three to five in a full tutorial). A claim that fails the check is dropped, not softened.
6. Quote sparingly, with attribution, and link for the rest.
7. **Snippets obey the cited doc.** Check every code snippet that uses a framework API against
   the cited official page before the approval gate: methods the page describes as
   mutually exclusive are not called together, and no source is a mirror or copy of the
   official docs (rule 1).

## Choosing the architecture applications

Look for seams where behavior is selected or plugged in: a policy chosen by
configuration at a service boundary, per-tenant or per-market rules behind
one port, interchangeable adapters behind a contract. For each one state what
varies, what must stay fixed, the gain and the cost. In the short article these seams are the
design decisions and this view is the hero diagram. Boxes in the diagram are
components or services, not classes; draw it with
`skills/diagram-authoring/SKILL.md` and check it at the destination width
(`skills/image-quality-inspection/SKILL.md`).

## Principles behind it

Every study article correlates the pattern with other design and architecture
principles, also when the topic is not widely covered. In the short system-design article this is
REQUIRED as ONE sentence in the "where the pattern lives" section naming the main principles the
design realises, plus a link to the repo's principles page; in a teaser post it is optional; the
full section below is the full-tutorial form only. The source is the repo's
`docs/06-design-principles.md`
(`skills/multi-language-study-repo/references/design-principles-doc.md`); the
article and the post quote it and add nothing the page does not hold. In the
full-tutorial form, place the section after the architecture and framework
sections, before or inside the standard explanation. Contents:

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
- Placed before the worked example, the section must say that the participants
  are introduced further down, and every cross-reference must hold at that
  insertion point (read the draft top to bottom once).
- Merge the repo PR that adds the principles page before publishing an article
  or post that links it (the link must resolve on the default branch).
- Examples of misuse and claims such as the dependency rule or coupling follow
  the checks in `skills/multi-language-study-repo/references/design-principles-doc.md` (Known pitfalls).
- Principle definitions are generic. Any attribution (who coined a principle) or
  quote needs a primary-source citation or is left out; never attribute from
  memory.

## Before the approval gate

- The profile is named in the draft message; `check_publication.py` exits 0 on the article and on
  the post, and the `publication-reviewer` verdict is `pass`.
- The opening matches the profile: the system design problem (default) or the non-obvious angle
  (full tutorial). The standard material follows only in a full tutorial; otherwise it stays in the repo.
- Every framework claim has a fact-table row with an official source and a
  check date on the day (see rule 2).
- The principles match the repo's principles page, with the tension: the required one sentence in
  the short article, the "Principles behind it" section in a full tutorial; a teaser post may
  carry one line naming them.
- The post's image is the hero diagram (full tutorial: the architecture diagram) and reads at feed width.
- Every code snippet that uses a framework API was checked against the cited page (rule 7).
- Article and post agree.
- The stage map of [aida-narrative.md](aida-narrative.md) is shown with the draft.

The angle changes the order of content, not the approval gates: the full
text is still shown as `NOT POSTED` first. The profile's approval mode (`gated` or `drafts-only`)
decides which external writes are pre-approved: in `drafts-only` only the creation of the two
drafts is. Changing an already published
story is an edit that needs approval; a published LinkedIn post cannot change
its media, so a new image means a new post with a "More..." pointer in the old post
(`skills/linkedin-publishing/references/repost-and-delete.md`). A published piece whose shape
misses the profile is replaced, not retitled
([replace-published-story.md](replace-published-story.md)).
