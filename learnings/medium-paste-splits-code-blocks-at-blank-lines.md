---
title: Medium splits one pasted code file into several boxes at empty lines
category: toolchain
created: 2026-10-07
tags: [medium, code-blocks, blank-lines, paste, html, editor]
---

# Problem

Pasting an article into the Medium editor with each file inside
`<pre data-code-block-mode="2" data-code-block-lang="java">` worked, except that
an empty line inside a `<pre>` split that one file into several code boxes.

# Failed Approaches

- Replacing the newlines inside the `<pre>` with `<br>` did not stop the split.

# Solution

In the paste HTML only, make every empty line inside a `<pre>` a line that holds
exactly one space character (U+0020). The repository source files keep their real
empty lines.

```python
def space_blank_lines(code: str) -> str:
    lines = code.rstrip("\n").split("\n")
    return "\n".join(line if line else " " for line in lines)
```

The same transform is built into the paste-HTML tool, which also sets the language
attributes. Run it, then lint the result:

```bash
python3 skills/medium-publishing/scripts/medium_paste_html.py build article.html -o article.paste.html
python3 skills/medium-publishing/scripts/medium_paste_html.py check article.paste.html
```

After pasting, confirm the editor's `pre` count equals the number of `<pre>` tags in the
paste HTML. Keep the byte-identity hash check: it normalises trailing whitespace on both
sides, so the single-space lines still compare equal to the source file. Pasted code
stays valid; Python ignores whitespace-only lines.

Durable guidance: skills/medium-publishing/references/paste-recipe.md

# Why

Observed: an empty line inside `<pre>` produced a new code box, `<br>` did not help,
and a line holding one space did not split. The session did not establish how Medium
decides where one box ends (inference: its paste handling treats an empty line as a
block boundary). The single-space line is safe because it only adds trailing
whitespace, which the hash check already normalises away.
