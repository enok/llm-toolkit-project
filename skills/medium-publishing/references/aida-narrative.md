---
title: AIDA narrative structure for articles and posts
tags: [medium, linkedin, aida, narrative-structure, hooks, titles, positioning, profile, teaser, system-design, engagement, retrofit]
---

# AIDA narrative structure for articles and posts

Every Medium article and every LinkedIn post of a study publication moves through four
stages, in this order: Attention, Interest, Desire, Action. The structure is there so that
people are more likely to engage: they stop, keep reading, see the value, and know what to
do next. It applies to every piece, also when the topic is not widely covered.

AIDA fixes the order of a piece. What the piece is about, how long it runs and how many hashtags
it carries come from the publication profile ([positioning-profile.md](positioning-profile.md),
rule `rules/publication-positioning.md`). By default a study article is a short system design story
([system-design-article.md](system-design-article.md)) and the post is a short teaser that sends
readers to it.

## The four stages

| Stage | Job | Test |
| --- | --- | --- |
| Attention | Start with something that grabs the reader. Why should they care? | Read alone, it says what the piece is about and why it matters to the reader. |
| Interest | The problem, the context, and why it matters. | A reader who has not met the topic can name the problem after it. |
| Desire | The value of the solution, including the benefits and the results. | It states what the reader gets, using only results the repo or the fact table holds. |
| Action | Finish with a clear outcome, recommendation, or next step. | The reader knows the one thing to do next. |

The stages are a flow, not headings. Do not print the words "Attention", "Interest",
"Desire", or "Action" in the piece; show them only in the stage map (see the checklist).

## AIDA, the profile and the content angle

The profile decides what the piece is about and how long it runs. In the default
system-design-first shape the Attention is the system design problem or capability at the target
role's level, the study topic stays inside the body, and non-obvious applications or cited
framework facts are supporting evidence in the Desire stage, never the hook.

Only when a profile asks for a full tutorial does [content-angle.md](content-angle.md) decide the
lead: the non-obvious application or the cited framework fact is then the Attention, and the
full-tutorial article order of that file carries the AIDA stages item by item. The post order of
that file is the teaser shape and applies in both cases. AIDA frames every shape and never
conflicts with them.

For a topic with no system design story and no non-obvious claim to lead with, open with the
concrete problem the reader has or the result they get, then follow the same four stages.

## LinkedIn post mapping

The post is a short teaser whose job is to send readers to the article. Its budgets come from the
profile; toolkit defaults are at most 1,300 characters in total, a hook of at most 200 characters
and at most 5 hashtags.

| Stage | In the post |
| --- | --- |
| Attention | The hook is the first paragraph of the post (the text before the first blank line), at most the profile's hook budget (default 200 characters), which keeps it before the "see more" cut: the system design problem or the lead claim, with no study-topic name under a system-design-first profile. The cut moves with device and line breaks, so check the composer preview. |
| Interest | Two or three lines: the problem, the context, why it matters. |
| Desire | Two or three short items: what the article shows (a design decision and its trade-off, a result the repo holds). A line naming the main principles is optional here; the article carries the required sentence. |
| Action | One primary call to action: the article link. The repo link is optional and secondary. Add one specific question that invites a reply. |

Hashtags come after the Action, at the end of the post: at most 5 (or the profile cap), chosen by
positioning and each named in the post text
(`skills/multi-language-study-repo/references/tags-and-topics.md`).

## Medium article mapping

| Stage | In the article |
| --- | --- |
| Attention | Title, subtitle, and the first paragraph together carry the hook: the system design problem or capability at the target role's level, never the study topic's name under a system-design-first profile. |
| Interest | The forces right after the hook: the system, its requirements and constraints, why it matters. |
| Desire | Two to four design decisions, each with the alternative not taken and the cost accepted, the hero diagram, and one short section that names the study topic as the mechanism with the one-sentence principles line ([system-design-article.md](system-design-article.md)). A full-tutorial profile uses a short "what you get" list and then the body in the content-angle.md order instead. |
| Action | A closing "Your next step" section is the call to action: the outcome or recommendation first, then the repo, post, and video links. |

## Positioning rule for titles and hooks

Lead with the highest-level concept the body actually supports, at the level a reader in
the author's target role would care about: an architecture style rather than a class-level
pattern, a system capability rather than one API detail. The role comes from the profile; when
there is none, ask once, then use the toolkit defaults and say so.
Under a system-design-first profile the study topic (for example a class-level pattern) is the
lowest-level concept: it goes in the body, never in the title, subtitle, or post hook
(`check_publication.py article --forbid-title` checks title and subtitle, `post --forbid` the hook).

1. List the concepts the piece covers, from the lowest level to the highest.
2. Pick the highest one that the body backs with a diagram, a worked example, or a cited
   claim. That concept goes in the title; the lower-level one moves to the body only (a
   system-design-first profile forbids the study topic's name in the subtitle too).
3. Never promise what the body does not deliver. If the body only shows a class-level
   example, the title cannot claim an architecture style: add the architecture content (diagram
   and cited claims, through the normal approval gate) or lower the title.
4. Check: every noun in the title, subtitle, and hook can be pointed to in the body.

## Retrofitting a published piece

Edit in place when the shape survives and only the title, subtitle, opening, or closing change.
When the shape is wrong (a long tutorial where a short system design story is wanted, a long list
post where a teaser is wanted), replace the piece instead:
[replace-published-story.md](replace-published-story.md).

- Change only the title, subtitle, opening paragraphs, and closing section of the story,
  or the text of the post. A story's title and subtitle are changed in the editor and in the
  story preview.
- Leave code blocks and figures untouched. After the edit, re-verify the image count, the
  code-block count, and the SHA-256 of each block against the repo files
  ([editor-verification.md](editor-verification.md) sections 1 and 3).
- A Medium edit follows section 5 (editing a published story, "Save and publish") of
  [publish-dialog.md](publish-dialog.md). That section covers editor content only; no
  recipe here records the story-preview fields, so change them, read them back on the
  public page, and report what did not take. A LinkedIn editor changes text and alt text only
  (`skills/linkedin-publishing/references/repost-and-delete.md`).
- Each edit is an external write: show the exact change labelled `NOT POSTED`, get approval,
  apply, and check the public page. Confirm that the story and post links still resolve and
  repoint any back-link that changed.

## Pre-approval checklist

- The stage map is shown with the `NOT POSTED` draft: one line per stage naming the sentence,
  paragraph, or section that carries it.
- Each stage is present, and they appear in order.
- The post hook (its first paragraph) is within the profile's hook budget and so sits before the
  "see more" cut; the article hook sits in title, subtitle, and first paragraph.
- One primary call to action per piece (in the post: the article link), plus one specific question
  in a post. The post carries at most 5 hashtags (or the profile cap), each named in its text.
- No new claims beyond the fact table and the repo content; Desire quotes results the repo
  holds and invents none.
- Title is at most 100 characters and subtitle at most 140
  ([publish-dialog.md](publish-dialog.md) section 1), counted before typing.
- The title follows the positioning rule and the body delivers everything it promises.
- Article and post agree on the claim, the principles, and the links.
- The profile used is named (path and budgets, or the toolkit defaults); `check_publication.py`
  exits 0 on each draft and the `publication-reviewer` verdict is `pass`
  (`tool-subagents/publication-reviewer.md`).

Stage map shape (generic):

```text
Attention: <title / first sentence quoted>
Interest:  <the problem sentence or paragraph>
Desire:    <the benefit items, the results, the principles line>
Action:    <the next step with its links, the question>
```
