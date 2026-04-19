---
title: Use % Formatting in Logger Calls
impact: HIGH
impactDescription: Avoids unnecessary string construction when log level disabled
tags: python, logging, performance, lazy-evaluation
---

## Use % Formatting in Logger Calls

Never use f-strings in log statements — use `%s`/`%d` for lazy evaluation.

**Incorrect (f-string — constructed even if level disabled):**

```python
logger.debug(f"Processing user: {user_id} with {len(items)} items")
```

**Correct (% formatting — lazy evaluation):**

```python
logger.debug("Processing user: %s with %d items", user_id, len(items))
```

- Use appropriate levels: ERROR (action needed), WARNING (concerning), INFO (milestones), DEBUG (diagnostics)
- Log at function boundaries: entry (DEBUG), result (INFO/DEBUG), exceptions (ERROR/WARNING)
- Never log PII, credentials, or full request/response bodies in production
