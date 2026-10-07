---
title: The changed-code quality gate blocks file types it cannot classify, so store fixtures as .txt
category: toolchain
created: 2026-10-07
tags: [quality-gate, ci, fixtures, html, mermaid, gitattributes, suffix, unrecognized-file-type]
---

# Problem

CI blocked a change because the changed-code quality gate could not classify some of the
files in it: HTML and Mermaid (`.mmd`) test fixtures and a `.gitattributes` change. The
session recorded this as a medium-severity validation-gap mistake, found by CI. The gate
treats an unrecognized changed file type as a blocker (`skills/changed-code-quality-gate/SKILL.md`,
`rules/changed-code-quality-gate-required.md`).

# Failed Approaches

None recorded beyond the first attempt described in Problem: the fixtures were committed
under their natural suffixes, and the gate blocked the change.

# Solution

- Store HTML, Mermaid and other fixtures under a non-code suffix, `.txt`, and have the test
  read them as text.
- When a fixture needs significant whitespace, put a `{{SPACE}}` marker on its own line and
  have the test expand it to a single space, as `tests/test_medium_paste_html.py` does.
- Avoid changes to files without a suffix (such as `.gitattributes`) in a change that the
  gate scans; the recorded fix was to avoid suffixless file changes. When a change must
  touch `.gitattributes` (`rules/cross-platform-scripts.md` asks for it), report the gate
  block and propose adding the name to `NON_CODE_NAMES` in
  `scripts/changed_code_quality_gate.py` through `workflows/toolkit-maintenance.md`
  instead of working around it.
- The gate is already required before commit and push
  (`rules/changed-code-quality-gate-required.md`); running
  `python scripts/changed_code_quality_gate.py --base <trusted-base>` on a change that adds
  fixtures shows the block before CI does.

# Why

The gate derives its scope from Git and fails closed: a changed file that is neither a
supported language nor a known non-code type is reported as an unrecognized changed file
type and blocks. In the gate's own code (`scripts/changed_code_quality_gate.py`) `.txt` is a
known non-code suffix, while `.html`, `.mmd` and a suffixless name like `.gitattributes` are
not listed, so they fall into the blocking case. Storing the fixture as text moves it out of
the gate's code scope without weakening the gate.
