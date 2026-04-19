---
title: Always Double-Quote Variables
impact: MEDIUM
impactDescription: Prevents word splitting and glob expansion bugs
tags: bash, shell, quoting, variables, word-splitting
---

## Always Double-Quote Variables

Unquoted variables undergo word splitting and glob expansion — the #1 source of shell bugs.

**Incorrect (word splitting breaks filenames with spaces):**

```bash
file="my report (final).txt"
rm $file          # tries to rm "my", "report", "(final).txt"

for f in $(find . -name "*.txt"); do  # breaks on spaces
  echo "$f"
done
```

**Correct (double-quote preserves the value as one token):**

```bash
file="my report (final).txt"
rm "$file"        # correctly removes the single file

while IFS= read -r -d '' f; do
  echo "$f"
done < <(find . -name "*.txt" -print0)
```

- Always `"$var"` — the only exception is inside `[[ ]]` where splitting doesn't occur
- Use `"${array[@]}"` to expand arrays safely (each element as separate word)
- Use `"$@"` not `$@` to pass arguments through correctly
