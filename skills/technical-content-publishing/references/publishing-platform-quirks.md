---
description: Medium and LinkedIn editor quirks met while publishing, with exact fixes - post-publish media limit and the More pointer, composer file inputs, Medium topics popover, code-block paste splitting, study-article positioning lesson
---

# Publishing Platform Quirks (Medium and LinkedIn)

Read before pasting into Medium, attaching an image on LinkedIn, or editing a published piece. The workflow `workflows/study-publication-medium-linkedin.md` (Known pitfalls) points here.

## LinkedIn: media cannot be added or swapped after publishing

The editor of a published post changes its text and its image alt text only, never the media. Every LinkedIn post in this flow should carry a high-quality diagram or visual. The session recorded the limit, not the product reason: treat it as a fixed property of LinkedIn. State the limit up front; do not propose a repost when only text or alt text must change, and do not make a text-only edit when the image must change (the old image stays). Two plans in one flow missed what the user wanted in exactly these two ways.

Prevent first:

1. Before the first Post click, check that an image preview shows inside the "Create post" composer. The first URL in the text adds a link-preview card, and LinkedIn hides the media buttons while that card is shown: attach the image first or remove the card with its x. (A pre-publish state, not the post-publish limit.)

Then, by case:

- Text-only or alt-text change: edit the existing post in place; no new post.
- Image must change (or the post is live without its image): publish a NEW post with text and image. Show the full text and the image labelled `NOT POSTED`, get approval, verify the text hash, post, read the new post URL from the "View post" link. Decline the paid boost prompt ("No thanks").
- Then edit the OLD post's text so it opens with a line `More... <new-post-url>` (text edits are allowed after publishing): show the exact edited text, get approval, save, read the old post back. Default since 2026-10-07; it replaces the earlier "repost, then delete the old post" default. Inference (the session did not record why): the old post keeps its reactions, comments and a resolving URL while the new post carries the image.
- Repoint every back-link from the old URL to the new one, each as its own approved write: edit the published Medium story (use "Save and publish") and open a README link PR. Readers should land on the post that carries the image.
- Do not delete the old post unless the user asks; a delete is a separate approval: "..." menu, Delete post, confirm, then verify the old URL shows "Post not found". General guidance, not observed: deleting also discards the old post's reactions and comments, so tell the user before asking for the delete approval.

Each external write (new post, pointer edit, each link edit) needs its own approval.

## LinkedIn: composer file inputs belong to the messaging overlay

Pre-existing file inputs on the page (including `attachment-input`) belong to messaging, not the "Create post" composer. A chat draft holding the file is one click from reaching another person.

- Create your own temporary `input` (`type=file`, distinct id), append it to the page, let the browser tool's upload fill it, then move the file onto the composer editor in the "Create post" dialog with a drop or paste event. Never use a pre-existing input.
- Remove the temporary input at the end, also on failure (`finally`).
- Never click Send or other messaging controls. After attaching, check the image shows in the Create post dialog, not a chat bubble. If it lands in a chat draft: remove that draft's attachment, confirm it is gone, tell the user, do not send.

## Medium: Change topics popover on a published story

The story editor's "..." menu has "Change topics": a popover with the current topic chips (each with a remove control), an "Add a topic..." field and Save / Cancel.

- Remove the chips to replace with their remove control (worked).
- Type the topic until the exact topic is the first suggestion; read the suggestion list before pressing anything (each suggestion shows a number). Press Enter: it adds the first suggestion. Read the chips back.
- Do not click the suggestion with the mouse: a typed-then-clicked suggestion, and a dispatched mousedown plus click on its list item, both added no chip and left the typed text in the field. (The publish dialog differs: a DOM click worked there.) Why the popover ignores clicks was not investigated.
- When the intended name is not offered as such (typing "SOLID" offered Solidity, Solid, Solid Principles, Solidarity, Solidão; "Solid" is a different topic), ask the user before adding a substitute unless the approved draft already names it. With approval, extend the text until the substitute is first (typing " Principles" after "SOLID" made "Solid Principles" first), then press Enter.
- Click the popover's Save (it closed the popover); then "Save and publish" published and the live page showed the new topics. Whether Save alone publishes the topics was not checked (inference: they go out with the publish).
- Normalise text before comparing the editor's content with approved text byte for byte: curly double quotes (U+201C, U+201D) to `"`, curly single quotes (U+2018, U+2019) to `'`, no-break space (U+00A0) to a space. Observed: a pasted paragraph's straight quotes became curly and a heading held no-break spaces; why was not investigated (inference: editor typography on paste).

## Medium: pasted code files split at empty lines

Pasting an article with each file inside `<pre data-code-block-mode="2" data-code-block-lang="java">` works, except that an empty line inside a `<pre>` splits that one file into several code boxes. Replacing newlines with `<br>` did not stop it.

In the paste HTML only, make every empty line inside a `<pre>` a line holding exactly one space (U+0020); repository source files keep their real empty lines.

```python
def space_blank_lines(code: str) -> str:
    lines = code.rstrip("\n").split("\n")
    return "\n".join(line if line else " " for line in lines)
```

Apply it while building the paste HTML (with the language attributes): `scripts/medium_paste_html.py build`, then `scripts/medium_paste_html.py check` must exit 0 before pasting. After pasting, confirm the editor's `pre` count equals the number of `<pre>` tags in the paste HTML. Keep the byte-identity hash check: it normalises trailing whitespace on both sides, so single-space lines still compare equal to the source file. Pasted code stays valid; Python ignores whitespace-only lines. Observed: an empty line produced a new box, `<br>` did not help, a one-space line did not split. How Medium decides where a box ends was not established (inference: paste handling treats an empty line as a block boundary).

## Study articles: system design first, post is a short teaser

Contract, budgets (article, post, hook, hashtags), approval modes, profile and shape checks, stage map and replacement: `rules/publication-positioning.md`. Facts the rule does not state:

- Signature `spec-gap/publication-not-positioned-for-target-role`. Incident: a first study publication passed every gate and still missed its purpose (position the author at the target role's level, system design as the main focus). The article was a ~6,000-word tutorial (24 minute read) whose title named a class-level pattern; the post repeated it in miniature (long, nineteen hashtags, several calls to action). AIDA fixes only order, not subject or length, and role, focus and budgets were written nowhere the flow could read.
- Shape: the article is one short system design story (1,300 words in an example consumer profile; the rule gives the toolkit default) led by a hero system-design diagram, with the title and subtitle naming the system design problem or capability. The full pattern explanation, class-level diagrams, code and the principles page stay in the repo, linked. The pattern is introduced in the body as the mechanism; framework sightings, if used, are supporting evidence and each is cited.
- Post: a teaser with the hero diagram as the image; the article link is the single call to action (repo link optional). Medium topics stay five and system-design-led. Intake reads or creates the profile instead of asking piecemeal.
- Do not retitle alone: a higher-level title over a 6,000-word tutorial promises more than a skim confirms. Do not count hashtags by topic coverage ("one per topic named"): uncapped, the post tagged everything and the tags stopped signalling a focus. Do not keep teaching content in the article "because the repo links it": the reader never reaches the story and the article competes with the repo.
- Why it was missed: nothing measured it. Hard budgets plus a script that fails on a pattern name in the title, an oversized article or post, or a sixth hashtag make it an acceptance criterion; retitling cannot fix a piece whose shape is wrong.
