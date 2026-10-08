---
title: Medium publish dialog and editing a published story
tags: [medium, publish-dialog, topics, preview-image, editing, links, browser-automation]
---

# Medium publish dialog and editing a published story

Everything here prepares a story up to the publish click and covers edits
afterwards. Clicking Publish, or "Save and publish" on a live story, needs the
user's explicit approval of that exact action
(`rules/external-write-authorization.md`); report the filled dialog and stop.

## 1. Fields and limits

| Field | Limit | Notes |
| --- | --- | --- |
| Title | 100 characters | Plain text; no markdown or brackets. |
| Subtitle | 140 characters | One sentence on what the reader gets. |
| Topics | up to 5 | The five that best represent the content (`skills/multi-language-study-repo/references/tags-and-topics.md`); see section 2; verify the chips. |
| Preview image | one | Choose a diagram from the story, not a decorative image. |

Count characters before typing and keep the values in the approved draft.

## 2. Topics: autocomplete picks the wrong one

Two behaviours were observed:

- Typing a topic and pressing Enter adds the first suggestion, not the typed
  text. Typing "Java" added "JavaScript".
- Clicking a suggestion with the mouse closed the dropdown without adding
  anything.

What worked (`learnings/medium-topic-autocomplete-swaps-typed-topic.md`): type the topic (no Enter), wait for the suggestions, then
dispatch a DOM click on the exact suggestion button whose text equals the topic,
and verify the chips afterwards. The selectors below are illustrative; inspect
the live dialog (accessibility tree or `find`) for the real ones.

```js
(async () => {
  const want = 'Java';
  const options = [...document.querySelectorAll('[role="option"], li button, button')]
    .filter(b => b.offsetParent !== null);
  const hit = options.find(b => b.textContent.trim().toLowerCase() === want.toLowerCase());
  if (!hit) throw new Error('no exact suggestion for ' + want + ': ' +
    options.slice(0, 8).map(b => b.textContent.trim()).join(' | '));
  hit.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true, view: window }));
  return 'clicked ' + hit.textContent.trim();
})()
```

Verify after every topic: read the chips back and compare with the intended list.
If a wrong chip appeared, remove it with its close control and retry. If no
exact suggestion exists, do not accept the first one; tell the user and ask
for a replacement topic.

In the Change topics popover of a published story the working method differs: section 7.

## 3. Preview image

Open the preview-image control and choose one of the story's own images,
preferably the diagram that explains the idea best at small size (a class or
flow diagram). Confirm the thumbnail changed before moving on.

## 4. Before the publish click

Report: title, subtitle, topic chips, preview image, the verification summary
from [editor-verification.md](editor-verification.md). Then wait. After the
user approves, click Publish once, read the final story URL from the page the
browser lands on, and report it.

## 5. Editing a published story

1. Open the live story, choose Edit, change the content in the editor.
2. Re-run the DOM verification for anything touched.
3. Get the user's approval of the edit, then use "Save and publish" (an edit
   to a live story uses this button, not "Publish"). The browser tool's auto-mode classifier
   can deny this final click even after the content was approved; ask for an explicit go that
   names the click ("click Save and publish on `<story title>` now"), or hand the click to the
   user (`learnings/auto-mode-classifier-denies-final-publish-click.md`).
4. Verify on the post-redirect page: navigate the browser to the story URL,
   let redirects settle, and read that DOM. A quick `fetch` of the public URL
   right after saving may return a cached copy and look unchanged.

Inserting a paragraph or a section into a live story (recorded run): click at the
end of the block before the insertion point (screenshot coordinates), press End, then
Enter for an empty paragraph, and paste. Paste plain text for a single paragraph and
the section as HTML; an `<h2>` arrived with the same heading class as the story's other
section headings. Read the inserted blocks back with the normalisation in
`editor-verification.md` section 4 (the editor turned straight quotes into curly ones).

## 6. Replacing one link

Ctrl+K on text that is already linked did not open the link editor (earlier note, not
re-tested). What worked, in the editor of the live story (`learnings/medium-published-story-link-edit-via-toolbar-link-button.md`):

1. Select the link text.
2. Click the toolbar link button once. This removes the link.
3. Click the link button again. The "Paste or type a link" field opens.
4. Type the new URL and press Enter.
5. Read the anchor back: its text, its new `href`, and that no anchor with the old URL remains:

   ```js
   (async () => {
     const root = document.querySelector('article') || document.body;
     return [...root.querySelectorAll('a')].map(a => ({ text: a.textContent.trim(), href: a.href }));
   })()
   ```
6. Get the user's approval of the exact change, then "Save and publish" (section 5; the final
   click needs the go described there).

The session did not record how the link text was selected, and it is untested whether a script
selection makes the toolbar show; the toolbar must be showing for the selection. The DOM Range
below selects an anchor's text from script:

```js
(async () => {
  const root = document.querySelector('article') || document.body;
  const a = [...root.querySelectorAll('a')].find(x => x.href.startsWith('https://example.com/old'));
  if (!a) throw new Error('old link not found');
  const range = document.createRange();
  range.selectNodeContents(a);
  const sel = getSelection();
  sel.removeAllRanges();
  sel.addRange(range);
  return 'selected: ' + sel.toString();
})()
```

Fallback if the toolbar flow fails: put `<a href="https://example.com/new">same text</a>` on the
OS clipboard as `text/html` ([paste-recipe.md](paste-recipe.md), section 4), select the anchor
text, and paste with Ctrl+V (Cmd+V on macOS). This was the earlier recipe and was not
re-checked in the latest session; verify the anchor the same way (step 5).

To add a link to text that has none, select that text with a Range (`setStart` and `setEnd` on
its text node) and paste the same way (earlier recipe, not re-tested).

## 7. Changing topics of a published story

In the story editor, the "..." menu has "Change topics": a popover with the current
chips (each with a remove control), an "Add a topic..." field, and Save / Cancel.
Observed in that popover (`learnings/medium-change-topics-popover-enter-adds-first-suggestion.md`):

- A mouse click and a dispatched mousedown and click on a suggestion did not add it.
- Enter added the first suggestion.

This differs from the publish dialog (section 2): there a DOM click worked and Enter was
unsafe; here a DOM click did not work, so Enter is the only method that worked, safe only when the exact
topic is already the first suggestion.

So: remove the chips to replace, type the topic until the exact topic is the first
suggestion (read the list before pressing anything), press Enter, and read the chips back.
Then click the popover's Save and "Save and publish" (section 5); whether Save alone
publishes the topics was not checked. When the intended name is not offered as such
(typing "SOLID" offered "Solidity", "Solid" and "Solid Principles"; "Solid" is a different
topic), ask the user before substituting, unless the approved draft already names the
substitute.
