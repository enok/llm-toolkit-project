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
| Topics | up to 5 | See section 2; verify the chips. |
| Preview image | one | Choose a diagram from the story, not a decorative image. |

Count characters before typing and keep the values in the approved draft.

## 2. Topics: autocomplete picks the wrong one

Two behaviours were observed:

- Typing a topic and pressing Enter adds the first suggestion, not the typed
  text. Typing "Java" added "JavaScript".
- Clicking a suggestion with the mouse closed the dropdown without adding
  anything.

What worked: type the topic (no Enter), wait for the suggestions, then
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
   to a live story uses this button, not "Publish").
4. Verify on the post-redirect page: navigate the browser to the story URL,
   let redirects settle, and read that DOM. A quick `fetch` of the public URL
   right after saving may return a cached copy and look unchanged.

## 6. Replacing one link

Ctrl+K on text that is already linked did not open the link editor. Replace
the whole anchor instead:

1. Select the anchor text with a DOM Range:

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
2. Put an HTML `<a href="https://example.com/new">same text</a>` on the OS
   clipboard as `text/html` ([paste-recipe.md](paste-recipe.md), section 4).
3. Paste with Ctrl+V (Cmd+V on macOS) while the selection is active.
4. Verify the anchor: its text, its new `href`, and that no old link remains.
   Then "Save and publish" with approval, as in section 5.

To add a link to text that has none, select that text with a Range
(`setStart` and `setEnd` on its text node) and paste the same way.
