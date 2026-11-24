---
title: py_compile writes bytecode even when bytecode writing is disabled
category: toolchain
created: 2026-11-24
tags: [python, py_compile, bytecode, pycache, read-only-review, clean-tree]
---

# Problem

A compile check with `python -m py_compile <file>` is a common cheap syntax
gate. In one recorded session a read-only review lane ran it and left
`__pycache__` folders in the reviewed tree. The original record held this single
observation and the explanation that writing the compiled file is what
`py_compile` does. That record gave no interpreter version.

Reproduced in a fresh temporary directory (Python 3.13.18, one-line `m.py`):

- `python3 -B -m py_compile m.py` left `__pycache__/m.cpython-313.pyc`.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile m.py` left the same file.
- The in-memory check below left no new file, and still reported a
  `SyntaxError` for an unclosed bracket.

Only this one interpreter version was checked.

# Failed Approaches

- Disabling bytecode writing with `-B` or `PYTHONDONTWRITEBYTECODE=1` before
  `py_compile`: both still produced the `.pyc` file, because writing the
  compiled file is what `py_compile` does.

# Solution

Parse in memory instead of compiling to disk; nothing is written:

```bash
python3 -B -c "import sys; compile(open(sys.argv[1], 'rb').read(), sys.argv[1], 'exec'); print('syntax ok')" path/to/file.py
```

`ast.parse(source)` works the same way. If `py_compile` must be used, delete
the generated `__pycache__` folder right after and confirm the tree is clean
with `git status --porcelain` (general guidance, not tried in this run).

# Why

`py_compile` exists to produce the bytecode file, so the no-bytecode switches
do not apply to it. A clean-tree gate or read-only review must not leave
artifacts, so the check has to avoid the disk write rather than suppress it.
