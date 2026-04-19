---
title: Classify SDK Errors by Error Code, Not Class Name
impact: HIGH
impactDescription: Branching on class name for wrapped SDK exceptions creates unreachable code paths
tags: error-handling, sdk, aws, botocore, correctness
---

## Classify SDK Errors by Error Code, Not Class Name

When catching SDK exceptions that wrap multiple error types under a single class (e.g., `botocore.exceptions.ClientError`), branch on the **error code** from the response, not `__class__.__name__`.

**Incorrect (class name — always "ClientError", branches unreachable):**

```python
except botocore.exceptions.ClientError as err:
    err_type = err.__class__.__name__
    if err_type == "ValidationError":    # NEVER true — class is always ClientError
        raise ValidationException(...)
    if err_type == "ModelError":         # NEVER true
        raise ValidationException(...)
    raise LambdaException(...)
```

**Correct (error code from response):**

```python
except botocore.exceptions.ClientError as err:
    error_code = err.response["Error"]["Code"]
    if error_code == "ValidationError":
        raise ValidationException(...)
    if error_code == "ModelError":
        raise ValidationException(...)
    raise LambdaException(...)
```

- AWS SDK exceptions like `ClientError` wrap all API errors under one class — the actual error type is in `err.response["Error"]["Code"]`.
- Same pattern applies to other SDKs: check the error/status code, not the wrapper class name.
- Always keep a generic fallback for unexpected error codes.
- Add unit tests that inject errors with specific codes and assert the correct exception type is raised.
