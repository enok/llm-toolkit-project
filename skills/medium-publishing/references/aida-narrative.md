---
title: AIDA narrative structure for articles and posts
tags: [medium, linkedin, aida, narrative-structure, hooks, titles, positioning, engagement, retrofit]
---

# AIDA narrative structure for articles and posts

Every Medium article and every LinkedIn post of a study publication moves through four
stages, in this order: Attention, Interest, Desire, Action. The structure is there so that
people are more likely to engage: they stop, keep reading, see the value, and know what to
do next. It applies to every piece, also when the topic is not widely covered.

## The four stages

| Stage | Job | Test |
| --- | --- | --- |
| Attention | Start with something that grabs the reader. Why should they care? | Read alone, it says what the piece is about and why it matters to the reader. |
| Interest | The problem, the context, and why it matters. | A reader who has not met the topic can name the problem after it. |
| Desire | The value of the solution, including the benefits and the results. | It states what the reader gets, using only results the repo or the fact table holds. |
| Action | Finish with a clear outcome, recommendation, or next step. | The reader knows the one thing to do next. |

The stages are a flow, not headings. Do not print the words "Attention", "Interest",
"Desire", or "Action" in the piece; show them only in the stage map (see the checklist).

## AIDA and the content angle

[content-angle.md](content-angle.md) decides WHAT leads: for a widely covered topic, the
non-obvious application or the cited framework fact. AIDA decides how the piece moves
from that opening to the close. The two never conflict: the non-obvious claim IS the
Attention. The article order and the post order of content-angle.md carry the AIDA stages
item by item and agree with the mappings below; AIDA frames them.

For a topic that is not widely covered there is no non-obvious claim to lead with by
default: open with the concrete problem the reader has or the result they get, then follow
the same four stages.

## LinkedIn post mapping

| Stage | In the post |
| --- | --- |
| Attention | The first lines, inside roughly the first 200 characters before the "see more" cut: the non-obvious claim. The cut moves with device and line breaks, so check the composer preview. |
| Interest | Two or three lines: the problem, the context, why it matters. |
| Desire | Short items: the architecture use, one or two cited framework appearances, the results, and the one line naming the main principles (content-angle.md). |
| Action | One primary next step: the article link is the call to action, the repo link supports it. Add one specific question that invites a reply. |

Hashtags come after the Action, at the end of the post
(`skills/multi-language-study-repo/references/tags-and-topics.md`).

## Medium article mapping

| Stage | In the article |
| --- | --- |
| Attention | Title, subtitle, and the first paragraph together carry the hook. |
| Interest | The problem paragraph right after the hook: problem, context, why it matters. |
| Desire | A short "what you get" list, then the body in the content-angle.md order (highlights, principles, explanation, diagrams, code). |
| Action | A closing next-step section is the call to action: the outcome or recommendation first, then the repo, post, and video links. |

## Positioning rule for titles and hooks

Lead with the highest-level concept the body actually supports, at the level a reader in
the author's target role would care about: an architecture style rather than a class-level
pattern, a system capability rather than one API detail. Ask for the target role when it
is not known; do not guess it.

1. List the concepts the piece covers, from the lowest level to the highest.
2. Pick the highest one that the body backs with a diagram, a worked example, or a cited
   claim. That concept goes in the title; the lower-level one moves to the subtitle or the body.
3. Never promise what the body does not deliver. If the body only shows a class-level
   example, the title cannot claim an architecture style: add the architecture content (diagram
   and cited claims, through the normal approval gate) or lower the title.
4. Check: every noun in the title, subtitle, and hook can be pointed to in the body.

## Retrofitting a published piece

Edit in place; do not republish as a new piece.

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
- The post hook sits inside the "see more" cut; the article hook sits in title, subtitle,
  and first paragraph.
- One primary call to action per piece, plus one specific question in a post.
- No new claims beyond the fact table and the repo content; Desire quotes results the repo
  holds and invents none.
- Title is at most 100 characters and subtitle at most 140
  ([publish-dialog.md](publish-dialog.md) section 1), counted before typing.
- The title follows the positioning rule and the body delivers everything it promises.
- Article and post agree on the claim, the principles, and the links.

Stage map shape (generic):

```text
Attention: <title / first sentence quoted>
Interest:  <the problem sentence or paragraph>
Desire:    <the benefit items, the results, the principles line>
Action:    <the next step with its links, the question>
```
