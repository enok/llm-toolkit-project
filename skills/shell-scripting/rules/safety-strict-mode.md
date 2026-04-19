---
title: Always Use Strict Mode
impact: CRITICAL
impactDescription: Prevents silent failures, unset variable bugs, and hidden pipe errors
tags: bash, shell, strict-mode, set, pipefail, safety
---

## Always Use Strict Mode

Every script starts with `set -euo pipefail`. No exceptions.

**Incorrect (no strict mode — errors silently ignored):**

```bash
#!/bin/bash
cd /nonexistent/dir   # fails silently
rm -rf ./*            # deletes files in WRONG directory
echo "$UNSET_VAR"     # expands to empty string
```

**Correct (strict mode — fails fast on any error):**

```bash
#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

cd /nonexistent/dir   # script exits immediately
rm -rf ./*            # never reached
echo "$UNSET_VAR"     # never reached — unset var triggers exit
```

| Flag | What it does | Without it |
|------|-------------|------------|
| `set -e` | Exit on any command failure | Script continues after errors |
| `set -u` | Exit on unset variable access | Unset vars expand to empty string |
| `set -o pipefail` | Pipe fails if ANY segment fails | Only last command's exit code matters |
| `IFS=$'\n\t'` | Split only on newlines/tabs | Spaces in filenames break loops |
