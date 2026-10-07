---
title: Medium editor DOM verification
tags: [medium, verification, dom, javascript, sha256, code-blocks, images]
---

# Medium editor DOM verification

After pasting, prove the editor holds what the source says before opening the
publish dialog. Run each snippet through the browser tool's JavaScript
execution on the editor tab. Selectors reflect the editor as observed
(`figure img`, `pre`, `.pre--content`); if Medium changes its markup, inspect
the live DOM and adjust the selector, not the expectation.

Every snippet below is shown complete and runs as written. Each one is an async
IIFE that returns its result, so repeated `const` names never collide and
`await` is legal. The shape they all follow:

```js
(async () => {
  const root = document.querySelector('article') || document.body;
  // ... snippet body ...
  return result;
})()
```

Keep that shape if you adapt a snippet: wrapper, `root` line, `return`.

## 1. Images and code-block counts

Expected: every article image is a `figure img` on Medium's CDN (the paste
re-hosted it), and `pre` count equals the number of code blocks in the paste
HTML.

```js
(async () => {
  const root = document.querySelector('article') || document.body;
  const imgs = [...root.querySelectorAll('figure img')];
  const onCdn = imgs.filter(i => /(^|\.)medium\.com$/.test(new URL(i.src, location.href).hostname));
  return { figures: imgs.length, onMediumCdn: onCdn.length,
           notOnCdn: imgs.filter(i => !onCdn.includes(i)).map(i => i.src),
           pre: root.querySelectorAll('pre').length };
})()
```

Compare with the source, counting tags rather than lines (the paste file may
hold several tags per line):

```bash
grep -o '<img' article.paste.html | wc -l
grep -o '<pre' article.paste.html | wc -l
```

An image not on the CDN failed to re-host (usually an unreachable or unpushed
`<sha>` URL).

## 2. Language attributes

```js
(async () => {
  const root = document.querySelector('article') || document.body;
  return [...root.querySelectorAll('pre')].map((p, i) => ({
    i, mode: p.getAttribute('data-code-block-mode'), lang: p.getAttribute('data-code-block-lang') }));
})()
```

Expected per block, in document order: the same mode and language that
`build` wrote. A missing language on a mode 2 block means the attribute was
dropped; re-paste before trying to fix it by hand. Only `java` is known to be
accepted; for any other language also look at the rendered highlighting, since
an unrecognised language name may be ignored.

## 3. SHA-256 of every code block against its source

`pre.innerText` includes an extra language-label line the editor appends, so
hash the `.pre--content` text instead. Normalise both sides identically:
`\r\n` to `\n`, non-breaking space to space, trailing whitespace removed per
line and at the end (this also erases the single-space blank-line workaround).

```js
(async () => {
  const root = document.querySelector('article') || document.body;
  const norm = s => s.replace(/\r\n/g, '\n').replace(/\u00a0/g, ' ')
    .split('\n').map(l => l.replace(/\s+$/, '')).join('\n').replace(/\s+$/, '');
  const sha256 = async s => [...new Uint8Array(await crypto.subtle.digest(
    'SHA-256', new TextEncoder().encode(s)))].map(b => b.toString(16).padStart(2, '0')).join('');
  const out = [];
  for (const [i, p] of [...root.querySelectorAll('pre')].entries()) {
    const node = p.querySelector('.pre--content') || p;
    out.push({ i, lang: p.getAttribute('data-code-block-lang'), sha: await sha256(norm(node.textContent)) });
  }
  return out;
})()
```

Source side, same normalisation, one hash per file in the order the files
appear in the article. Save as `hash_blocks.py` and run
`python hash_blocks.py File1.java file2.py ...` (use `python3` where `python`
is missing or is not Python 3):

```python
import hashlib, pathlib, sys

def norm(text: str) -> str:
    lines = text.replace("\r\n", "\n").replace("\u00a0", " ").split("\n")
    return "\n".join(line.rstrip() for line in lines).rstrip()

for name in sys.argv[1:]:
    data = pathlib.Path(name).read_text(encoding="utf-8")
    print(hashlib.sha256(norm(data).encode("utf-8")).hexdigest(), name)
```

Every pair must match exactly. A mismatch names the block (index and
language); fix the paste HTML and re-paste. Do not edit code in the editor.
Plain mode 0 blocks (logs, expected output) can be hashed the same way when
their source is a file.

## 4. Markdown leftovers and title

```js
(async () => {
  const root = document.querySelector('article') || document.body;
  const text = root.innerText;
  return { mdLinkLeftovers: (text.match(/\]\(http/g) || []).length,
           title: (document.querySelector('h1') || {}).textContent };
})()
```

Expected: `mdLinkLeftovers` is 0 and the title is the intended plain text. Also
skim the first screen for stray `**`, `##`, and backticks, which indicate
markdown that was never rendered to HTML.

## 5. Report

Report counts (figures, on CDN, pre), each language, the hash table (index,
language, first 12 hex characters, match yes/no), and the leftover scan. Only
when everything matches does the flow proceed to
[publish-dialog.md](publish-dialog.md).
