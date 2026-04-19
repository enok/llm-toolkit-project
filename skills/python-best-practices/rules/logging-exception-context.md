---
title: Log Exceptions with Business Context
impact: HIGH
impactDescription: Enables diagnosis without reading full stack traces
tags: python, logging, exceptions, context, exc_info
---

## Log Exceptions with Business Context

Include enough context to diagnose the issue without reading the full stack trace.

**Incorrect (no business context):**

```python
logger.error("Operation failed", exc_info=True)
```

**Correct (business context + root cause + full traceback):**

```python
logger.error(
    "DynamoDB retrieval failed for requestId=%s [root cause: %s]",
    request_id, str(e),
    exc_info=True
)
```

Pattern: `logger.error("What failed for key=%s [root cause: %s]", key, str(e), exc_info=True)`

- `exc_info=True` appends the full traceback. Without it, only the message is logged.
- Never include PII in exception messages. Pseudonymous IDs (requestId, orderId) are OK.
