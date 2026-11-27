---
title: re.sub with a Windows path as the replacement string raises bad escape
category: toolchain
created: 2026-10-22
tags: [python, re.sub, regex, windows, path, backslash, replacement, bulk-edit]
---

# Problem
A script rewrote old paths to a new Windows path across many files with
`re.sub(pattern, new_path, text)`. The call raised `re.error: bad escape \o` because the
replacement string contained `C:\out\...`.

# Failed Approaches
- Passing the Windows path straight in as the replacement: `re.sub` parses the replacement as a
  template, so `\o` is an unknown escape and the call fails.
- Not tried in this session (general guidance): `re.escape(new_path)` is meant for patterns, not
  replacement templates, and escapes more than backslashes.

# Solution
Pass a function, whose return value is used literally, or skip the regex when none is needed:

```python
new = r"C:\out\data"
text = re.sub(r"old/dir", lambda m: new, text)   # replacement is not parsed
text = text.replace("old/dir", new)               # plain substring, no regex at all
```

General guidance, not observed in this session: a path with `\n` or `\t` in a replacement
template does not raise, it silently becomes a newline or tab, so check the result of any bulk
rewrite that touches Windows paths.

# Why
In a `re.sub` replacement string, backslash sequences such as `\n`, `\1` and `\g<name>` are
processed, and unknown ASCII-letter escapes are errors. A callable replacement bypasses that.
