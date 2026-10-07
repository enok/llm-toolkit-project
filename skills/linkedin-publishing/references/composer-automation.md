---
title: LinkedIn composer automation
tags: [linkedin, browser-automation, shadow-dom, clipboard, verification]
---

# LinkedIn composer automation

Use this reference to put approved text into the LinkedIn "Create post" composer, prove it is
correct, publish, and read back the post URL. Labels below are English; LinkedIn localizes its
UI, so labels may differ in the user's UI language; match what the screen shows. Selectors
other than `.ql-editor` may change over time: re-inspect before trusting them and adapt.

## Why ordinary tools fail

The composer is a Quill editor (`.ql-editor`) rendered inside a shadow DOM. Accessibility-tree
tools cannot see it, so read it with a JavaScript query that walks shadow roots (the method
recorded as working). Other interaction paths, such as screenshot-coordinate clicks, were not
tested for the composer; treat them as fallbacks to try, not as known-good.

## Deep query helper

Run this in the page through the browser tool's JavaScript executor, then reuse it in later
calls (re-declare it if the executor does not keep state between calls):

```js
function deep(root, sel){ const out=[]; const walk=(r)=>{ r.querySelectorAll(sel).forEach(e=>out.push(e)); r.querySelectorAll('*').forEach(e=>{ if(e.shadowRoot) walk(e.shadowRoot); }); }; walk(root); return out; }
```

`deep(document, '.ql-editor')` returns every Quill editor on the page, including ones that
are not the post composer. Prove which one is the composer before writing to it:

```js
// Walk up through shadow boundaries to the enclosing dialog.
function up(n){ return n.parentNode instanceof ShadowRoot ? n.parentNode.host : n.parentElement; }
function dialogOf(n){ for (; n; n = up(n)) if (n.matches && n.matches('[role="dialog"],dialog')) return n; return null; }

const editors = deep(document, '.ql-editor').filter(e => dialogOf(e));
// Expect exactly one editor, inside the dialog that shows the "Create post" heading.
// Confirm with a screenshot; if the count is not 1, stop and inspect.
```

Treat the dialog check as a sketch: the goal is to be sure the editor belongs to the "Create
post" dialog and not to a comment box or a messaging draft.

## Focus and paste plain text

1. Attach the image first (see [image-attach-recipe.md](image-attach-recipe.md)), then give
   the composer focus with `editors[0].focus()`. Clicking inside it by screenshot coordinates
   is an untested alternative.
2. Write the approved text to the OS clipboard as plain text with LF line breaks: use the
   clipboard tool of the computer-control bridge, or the platform's plain-text clipboard
   command. Never put HTML on the clipboard.
3. Paste with the platform shortcut (Ctrl+V, or Cmd+V on macOS) while the composer has focus.
4. Clipboard paste is the method recorded as working. Key-by-key typing was not tried here;
   if it is used instead, the hash check below is the only safeguard.

## Verify by SHA-256 before Post

Each line of the composer is a `<p>`; a blank line is an empty `<p>`. Join the paragraph texts
with `\n` and hash them:

```js
(async () => {
  const ed = editors[0];
  const paras = [...ed.querySelectorAll('p')].map(p => p.textContent);
  const text = paras.join('\n');
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text));
  return {
    paragraphs: paras.length,
    chars: text.length,
    sha256: [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, '0')).join('')
  };
})()
```

Compute the expected value from the approved text with the same normalization: UTF-8, LF line
breaks, no BOM, no trailing newline. For example save the approved text to a file and run
`sha256sum <file>` (Linux/macOS) or `Get-FileHash -Algorithm SHA256 <file>` (PowerShell,
upper-case hex: compare case-insensitively).

For a more informative check, embed the approved text as a JSON string literal (generate it
with a JSON encoder, never hand-escape it) and compare in the page:

```js
const approved = /* JSON string literal of the approved text */ "";
const text = [...editors[0].querySelectorAll('p')].map(p => p.textContent).join('\n');
({ equal: text === approved,
   firstDiff: [...approved].findIndex((c, i) => c !== text[i]),
   lengths: [approved.length, text.length] })
```

On a mismatch do not post. Possible causes (guidance, not observed): trailing newline or CRLF
in the expected text, quote or whitespace substitution, non-ASCII characters altered in the
clipboard hand-off, a leftover character from an earlier attempt. Compare with the in-page
diff, clear the composer (select all, delete), re-paste, and hash again. The hash must be re-run after any change to the composer, including
removing the link-preview card or attaching an image.

## Link-preview card

The first URL in the text makes LinkedIn add a link-preview card. While the card is shown,
LinkedIn hides the media buttons, so the image cannot be attached. Default order: attach the
image first, then paste the text, as in `SKILL.md`. Whether a card still appears when the image
goes first was not recorded; if one appears, or if the text was pasted before the image, remove
the card with its x button. The URL stays in the text either way; re-verify the hash and the
image afterwards.

## Publish and read the post URL

1. After the user has approved the exact text and the hash matches, click Post.
2. After posting, a "View post" link is offered. Read its `href` (use `deep` if the plain
   query finds nothing) and record it as `<post-url>`:

   ```js
   deep(document, 'a').filter(a => /view post/i.test(a.textContent)).map(a => a.href)
   ```

3. A paid "boost" prompt can follow. Decline it ("No thanks" or close); never enter
   payment details.
4. Open `<post-url>` and confirm the text, the image, and the article link render.

## Bot checks and sign-in

If a "verify you are human" challenge, CAPTCHA, login, or two-factor prompt appears at any
point, stop and hand it to the user. Resume only after the user says it is cleared.

## Troubleshooting

The Basis column separates what was observed from untested guidance.

| Symptom | Possible cause | Action | Basis |
| --- | --- | --- | --- |
| `.ql-editor` not found by a plain query | Composer is in a shadow DOM | Use `deep` | Observed |
| Media buttons missing | Link-preview card visible | Attach media first, or remove the card with x | Observed |
| More than one editor found | Comment box or messaging draft also present | Filter to the "Create post" dialog; screenshot | Guidance, untested |
| Hash differs from approved | Newline, quote, or encoding difference | Compare with the in-page diff; clear and re-paste | Guidance, untested |
| No "View post" link seen | Link no longer shown | Check the new post through the profile's recent activity | Guidance, untested |
