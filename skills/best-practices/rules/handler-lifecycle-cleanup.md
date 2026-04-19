---
title: Wrap Handlers in try/finally for Lifecycle Cleanup
impact: MEDIUM
impactDescription: Missing cleanup on exit can leak context, connections, or state across invocations
tags: error-handling, lifecycle, cleanup, lambda, handler
---

## Wrap Handlers in try/finally for Lifecycle Cleanup

Entry-point handlers (Lambda handlers, HTTP controllers, message consumers) should use `try/finally` to guarantee cleanup runs on both success and failure paths.

**Incorrect (cleanup only at entry — stale state on exception):**

```python
def lambda_handler(event, context):
    clear_log_context()
    # ... processing ...
    return response
# If an exception occurs, log context is never cleared
```

**Correct (try/finally guarantees cleanup):**

```python
def lambda_handler(event, context):
    clear_log_context()
    try:
        # ... processing ...
        return response
    finally:
        clear_log_context()
```

- Clear request-scoped state (log context, MDC, correlation IDs) in `finally`.
- Close connections or resources acquired during the request in `finally`.
- This prevents stale context from leaking into subsequent invocations (Lambda container reuse, thread pools, connection pools).
- Do NOT catch and swallow exceptions in the finally block — let them propagate.
