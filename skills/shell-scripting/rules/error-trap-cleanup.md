---
title: Trap for Guaranteed Cleanup
impact: CRITICAL
impactDescription: Prevents leaked temp files, lock files, and background processes
tags: bash, shell, trap, cleanup, error-handling, tempfiles
---

## Trap for Guaranteed Cleanup

Use `trap cleanup EXIT` to guarantee cleanup of temporary resources regardless of how the script exits.

**Incorrect (temp file left behind on error):**

```bash
TEMP_FILE=$(mktemp)
curl -o "$TEMP_FILE" https://example.com/data
process "$TEMP_FILE"
rm -f "$TEMP_FILE"  # never reached if process fails
```

**Correct (trap guarantees cleanup):**

```bash
TEMP_FILE=""
cleanup() {
  [[ -n "$TEMP_FILE" && -f "$TEMP_FILE" ]] && rm -f "$TEMP_FILE"
}
trap cleanup EXIT

TEMP_FILE=$(mktemp)
curl -o "$TEMP_FILE" https://example.com/data
process "$TEMP_FILE"
# cleanup runs automatically — on success, error, or signal
```

- `trap ... EXIT` fires on normal exit, `set -e` errors, and signals (SIGINT, SIGTERM)
- Set the trap early, before creating any resources
- Clean up temp files, lock files, PID files, and background processes
