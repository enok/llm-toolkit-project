---
title: Redact Sensitive Data in DEBUG Logs
impact: HIGH
impactDescription: Raw payloads logged at DEBUG can leak PII, survey responses, and model inputs
tags: security, logging, pii, debug, redaction
---

## Redact Sensitive Data in DEBUG Logs

Never log full request/response payloads — even at DEBUG level. Raw objects may contain PII, survey responses, model input values, or credentials that violate data-handling policies.

**Incorrect (full payload at DEBUG):**

```python
logger.debug("Processing request: %s", event)
logger.debug("request_payload: %s", request_payload)
logger.debug("Payload: %s", model_request_payload)
```

**Correct (metadata-only summary):**

```python
logger.debug("Processing request: messageId=%s modelId=%s", message_id, model_id)
logger.debug("request_payload: modelId=%s fieldCount=%d endpoint=%s", model_id, len(fields), endpoint)
logger.debug("Payload: featureCount=%d schemaFields=%d", len(data_array), len(schema_array))
```

- Log only structural metadata: IDs, counts, sizes, endpoints, field names — never field values.
- For payloads containing user-supplied data (`model.fields[*].value`, survey responses, form inputs), always redact or omit the values.
- Consider a helper like `safe_payload_summary(payload)` to enforce consistent redaction across the codebase.
- This applies to ALL log levels (ERROR, WARNING, INFO, DEBUG) — DEBUG is not an excuse to log raw data.
