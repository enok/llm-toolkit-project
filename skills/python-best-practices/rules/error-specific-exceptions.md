---
title: Catch Specific Exceptions with Context
impact: HIGH
impactDescription: Enables targeted recovery and clear diagnostics
tags: python, error-handling, exceptions, raise-from
---

## Catch Specific Exceptions with Context

Catch the most specific exception type. Use `raise ... from e` to preserve the cause chain.

**Incorrect (bare except, swallowed):**

```python
try:
    process(data)
except:
    pass
```

**Incorrect (too broad, no context):**

```python
try:
    process(data)
except Exception as e:
    logger.error("Failed: %s", e)
```

**Correct (specific, contextual, preserves cause):**

```python
try:
    value = int(raw_value)
except ValueError as e:
    raise ValidationException(
        f"Invalid numeric value: {raw_value}"
    ) from e
```

- Never use bare `except:` — at minimum use `except Exception:`
- Never swallow exceptions silently
- Custom exceptions should inherit from a project-specific base
