---
title: Validators must scan the rendered HTML, titles included, for Markdown leftovers
category: testing
created: 2026-10-07
tags: [validation, markdown, html, converter, medium, regex, publishing]
---

# Problem

Markdown left in a title with nested brackets (`[[x] y](url)`) was not converted, and
Medium rendered it as raw text. Medium has no tables and no inline code either, so the
paste HTML needs those converted too. The converter or validator has to scan the HTML it
produced for `](http`.

# Failed Approaches

None recorded in the session notes; the default behaviour produced the failure described above.

# Solution

Scan the rendered paste HTML, including the `<h1>` title and any field typed separately
into the publish dialog, not just the Markdown source. Mask `<pre>` bodies first so code
that legitimately contains the sequence is not reported (general guidance, not observed
in this session):

```python
import re

PRE = re.compile(r"<pre\b.*?</pre>", re.S | re.I)

def mask_pre(html: str) -> str:
    # keep offsets and newlines, blank out everything inside <pre>
    return PRE.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), html)

def link_leftovers(html: str) -> list:
    masked = mask_pre(html)
    return [masked.count("\n", 0, m.start()) + 1 for m in re.finditer(r"\]\(http", masked)]
```

The paste-HTML tool already runs this rule (`markdown-leftover`) with `<pre>` masked,
next to its table and inline-code checks; run it before every paste and fix every issue it
lists:

```bash
python3 skills/medium-publishing/scripts/medium_paste_html.py check article.paste.html
```

After pasting, scan the editor text for `](http` as well and require a count of 0 plus a
plain-text title.

Durable guidance: skills/medium-publishing/references/editor-verification.md

# Why

The session observed one concrete failure: Markdown with brackets left in a title and
rendered as raw text. Inference: a check that reads the Markdown source cannot see
text the converter failed to convert, so the check has to read the converter's output.
Scanning the title along with the body matters because that is where the leftover was
seen.
