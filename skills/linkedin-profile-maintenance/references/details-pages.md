---
title: LinkedIn details pages, edit forms, and editors
tags: [linkedin, browser-automation, details-page, edit-form-url, contenteditable, inventory, add-skill, add-project]
---

# Details pages, edit forms, and editors

Mechanics behind `SKILL.md`. Page structure changes without notice: treat every
selector and label here as a starting point, inspect the live page first, and
read results back after each step. `<handle>` is the owner's profile handle,
`<section>` is the section name as it appears in the URL of that section's
details page (for example `skills`, `certifications`, `courses`, `projects`,
`experience`, `education`).

## 1. URL patterns

| Purpose | Pattern |
| --- | --- |
| List one section in full | `/in/<handle>/details/<section>/` |
| Edit one existing item | `/in/<handle>/details/<section>/edit/forms/<id>/` |
| Add a skill | `/in/<handle>/skills/edit/forms/new/` |
| Add a project | `/in/<handle>/edit/forms/project/new/` |

These patterns were observed in one session: the add URLs from the profile's own
"Add a skill" and "Add a new project" links, the edit-form URLs from the edit
controls of projects, certifications, courses, education, experience, and
skills. Inference, not tested: the edit-form `<id>` stays the same for an item
across list changes, while its position in the list does not.

## 2. Inventory

1. **The list scrolls inside `main`, not the window.** Details pages lazy-load
   items as the page's `main` container scrolls, so a window scroll loads
   nothing. Scroll that container until the item count stops growing.
2. **Collect before you change.** Record every item's name and its edit-form URL
   for the whole section before the first delete. After any delete the list
   re-renders to roughly its first 50 items, and later items leave the DOM, so
   positions recorded earlier are wrong and edit links clicked by position hit
   the wrong item. Open each item by its URL.
3. **Keep data out of tool output.** The browser JavaScript tool truncates long
   results; store the inventory in a window variable and read it in slices
   (`browser-session-notes.md`).
4. **Three places for one keep-list.** The owner's "courses and certifications"
   can span (a) Licenses and certifications, (b) Courses, where an item may be
   associated with an education entry, and (c) free-text Education
   descriptions. The same item can sit in two of them. Inventory all three, then
   compute the delete set. Paginated sections must be scrolled to the end first.
   Education descriptions are text to edit, not items to delete.
5. **Re-inventory after changes.** After a batch of deletes reopen the list,
   count it, and compare names with the expected remainder.

Illustrative scroll-and-collect snippet (adapt the selectors to what the page
shows; keep the result in a window variable):

```js
(async () => {
  const box = document.querySelector('main');
  let last = -1;
  for (let i = 0; i < 40; i++) {
    box.scrollTop = box.scrollHeight;
    await new Promise((r) => setTimeout(r, 800));
    const n = box.querySelectorAll('li').length;
    if (n === last) break;
    last = n;
  }
  window.__inventory = [...box.querySelectorAll('a[href*="/edit/forms/"]')]
    .map((a) => ({
      name: ((a.closest('li') || a).innerText || '').split('\n')[0].trim(),
      href: a.getAttribute('href'),
    }));
  return window.__inventory.length;
})();
```

## 3. Editing text

- **Experience Highlights / description is a contenteditable rich-text editor**
  (one `<p>` per line), not a textarea. Focus the editor, put the caret with a DOM
  `Range` at the end of the target line's last text node, then type with real
  key events. (Untested inference: assigning `textContent` or `value` may not reach
  the editor's state.)

```js
const editor = document.querySelector('[contenteditable="true"]');
const p = [...editor.querySelectorAll('p')]
  .find((el) => el.textContent.includes('<unique text of the target line>'));
const walker = document.createTreeWalker(p, NodeFilter.SHOW_TEXT);
let node, lastText;
while ((node = walker.nextNode())) lastText = node;
editor.focus();
const range = document.createRange();
range.setStart(lastText, lastText.length);
range.collapse(true);
const sel = getSelection();
sel.removeAllRanges();
sel.addRange(range);
// now type the addition with the browser tool's real key events
```

- **Project descriptions are plain textareas.** Check that the exact old
  substring occurs once, set the value with the native
  `HTMLTextAreaElement` setter, and dispatch an `input` event:

```js
const ta = document.querySelector('textarea');
const oldText = '<exact old substring>';
if (ta.value.split(oldText).length !== 2) throw new Error('old text must occur exactly once');
const setValue = Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype, 'value').set;
setValue.call(ta, ta.value.replace(oldText, () => '<new text>'));
ta.dispatchEvent(new Event('input', { bubbles: true }));
```

- Before saving, read the field back and compare it with the intended text;
  after saving, reopen the item and read it again.
- Selects on these forms (months, years) are React controls: use the browser
  tool's form input rather than writing `.value`.

## 4. Adding items

- **Skill** (`/in/<handle>/skills/edit/forms/new/`): the dialog asks where the
  skill was used. Tick the roles or projects that evidence it. "Follow this
  skill" defaults to on: untick it unless the owner asked. Re-read the skills
  list afterwards (count and name).
- **Project** (`/in/<handle>/edit/forms/project/new/`): the form has no URL
  field. Add the link through Media, "Add a link" (the title auto-fills). Add
  skills through the typeahead's "Currently in your Skills section" options.
  For an ongoing project tick "currently working on this project" and give the
  start month and year. Leave "Associated with" empty for a personal project.
- Facts for a new project (dates, tasks, links) come from evidence the owner
  can see: the repository, the CV, existing project entries. State which source
  backs each date.

## 5. Read-back checklist

| Change | Read back |
| --- | --- |
| Delete | Section count and names versus the expected remainder |
| Add skill | Skills list: count and the new name; follow setting off |
| Edit text | The field's text, then the saved entry |
| End date | The details line with start, end, and duration |
| Add project | The project page: dates, link, skills, associated-with empty |
