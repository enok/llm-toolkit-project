---
title: Bash-style unquoted globs and command variables failed under zsh; quote patterns and put logic in a bash or python script
category: toolchain
created: 2026-11-24
tags: [zsh, bash, glob, shell-variables, macos, quoting, tool-misuse]
---

# Problem
Bash-style unquoted globs and command variables failed under zsh, the default shell on macOS.
The session classed this as a low-severity tool misuse.

# Failed Approaches
- Unquoted glob patterns written for bash.
- Storing a command in a variable and expanding it unquoted as if it would be split into words.

# Solution
Quote glob patterns, and put multi-step logic in a bash or python script instead of inline zsh.

# Why
Inference, not observed: zsh treats an unmatched unquoted glob as an error and does not split an
unquoted variable into words by default, unlike bash. The record states only that these two
bash-style forms failed under zsh.
