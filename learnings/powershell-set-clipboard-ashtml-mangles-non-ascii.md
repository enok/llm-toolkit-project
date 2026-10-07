---
title: Windows PowerShell 5.1 Set-Clipboard -AsHtml mangles non-ASCII text
category: environment
created: 2026-10-07
tags: [powershell, clipboard, html, non-ascii, encoding, windows, medium]
---

# Problem

Rich HTML was pasted into the Medium editor through the Windows clipboard
(`Set-Clipboard -AsHtml`, then click the title, Select All, Paste). Under Windows
PowerShell 5.1 the right single quotation mark (U+2019) arrived as the replacement
character (U+FFFD). Non-ASCII text on the HTML clipboard is not reliable there.

# Failed Approaches

None recorded in the session notes; the default behaviour produced the failure described above.

# Solution

Entity-encode every non-ASCII character as `&#NNN;` before the HTML goes on the
clipboard, so the paste file is pure ASCII and encoding no longer matters. The
paste-HTML tool (`skills/medium-publishing/scripts/medium_paste_html.py`) does this for
the whole document, including `<pre>` bodies: run `build article.html -o
article.paste.html`, then `check article.paste.html`, which fails while any non-ASCII
byte is left.

Without the tool, Python's built-in handler does the same encoding, including
characters outside the Basic Multilingual Plane:

```python
import pathlib
src = pathlib.Path("article.html").read_text(encoding="utf-8")
pathlib.Path("article.paste.html").write_bytes(src.encode("ascii", "xmlcharrefreplace"))
```

On the machine, read the file back as ASCII and put it on the clipboard
(Windows PowerShell 5.1 syntax; not executed in the authoring sandbox, which has no
PowerShell):

```powershell
$path = (Resolve-Path 'article.paste.html').Path
$html = [System.IO.File]::ReadAllText($path, [System.Text.Encoding]::ASCII)
Set-Clipboard -AsHtml -Value $html
```

After pasting, look for a replacement character in the editor text (general guidance,
not observed in this session): `document.body.innerText.includes('\uFFFD')` should be
`false`.

Durable guidance: skills/medium-publishing/references/paste-recipe.md

# Why

The session observed only that Windows PowerShell 5.1 mangles non-ASCII text on the
HTML clipboard; it did not isolate which stage does it. Inference: a pure-ASCII payload
reads the same under any text encoding, so whichever stage mangles the text has
nothing left to alter.
