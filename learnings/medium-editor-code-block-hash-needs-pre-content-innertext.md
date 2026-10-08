---
title: Hash Medium code blocks from `pre .pre--content` innerText, normalised, not from `pre.innerText`
category: testing
created: 2026-10-07
tags: [medium, editor, code-blocks, sha256, verification, innertext, nbsp, browser-automation]
---

# Problem

After pasting an article into the Medium editor, every code block must equal its source file,
checked by hashing each editor block and its source. The editor text is not the source text
byte for byte: the language label is part of the element text, the editor can return
non-breaking spaces, and the blank-line workaround leaves lines holding a single space.

# Failed Approaches

- Hashing `pre.innerText`: it includes the language label, so the hash cannot match the
  source file.

# Solution

Hash the text of `pre .pre--content` (its `innerText`), normalised as below, and compare the
first 12 hex characters of the SHA-256 with the same prefix for each source block, stripped.
In the editor tab:

```js
(async () => {
  const root = document.querySelector('article') || document.body;
  const norm = s => s.replace(/\u00a0/g, ' ').trim()
    .split('\n').map(l => (l === ' ' ? '' : l)).join('\n');
  const sha12 = async s => [...new Uint8Array(await crypto.subtle.digest(
    'SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('').slice(0, 12);
  const out = [];
  for (const [i, p] of [...root.querySelectorAll('pre')].entries()) {
    const node = p.querySelector('.pre--content') || p;
    out.push({ i, lang: p.getAttribute('data-code-block-lang'), sha12: await sha12(norm(node.innerText)) });
  }
  return out;
})()
```

Source side, one prefix per file in article order (`text` is the file content, stripped):

```python
hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:12]
```

A mismatch names the block (index, language): fix the paste HTML and re-paste; do not edit
code in the editor. The author of this learning also checked the normalisation offline on a sample block
(single-space lines and non-breaking spaces reduce to the source text).

Durable guidance: skills/medium-publishing/references/editor-verification.md

# Why

Observed: `pre.innerText` carries the language label, and the three normalisations
(non-breaking space to space, trim, single-space lines to empty lines) make the editor hashes
equal the source hashes. The session did not establish why the editor returns non-breaking
spaces. The single-space lines are the deliberate paste workaround of
learnings/medium-paste-splits-code-blocks-at-blank-lines.md, so the check undoes it.
