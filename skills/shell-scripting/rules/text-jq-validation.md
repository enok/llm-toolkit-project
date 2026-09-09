---
title: Validate JSON with jq empty — Never jq -e empty
impact: MEDIUM
impactDescription: Prevents valid JSON from failing validation gates with exit code 4
tags: jq, json, validation, exit-code, shell
---

## Validate JSON with jq empty — Never jq -e empty

The `empty` filter parses the input but emits no result. With `-e`, jq derives its exit status from the last emitted value and returns exit code 4 when there is no value to inspect — so `jq -e empty` fails on perfectly valid JSON and incorrectly stops pipelines. Without `-e`, successful parsing alone yields exit code 0.

**Incorrect (valid JSON exits 4 and blocks the workflow):**

```bash
jq -e empty payload.json && deploy   # exit 4 even when payload.json is valid
```

**Correct (parse-validate without `-e`; assert shape with a value-producing filter):**

```bash
# Parse validation only
jq empty payload.json

# Parse validation plus top-level shape assertion
jq -e 'type == "object"' payload.json
```

- Use `-e` only with filters that emit a value (booleans, objects, counts) — its exit code then reflects truthiness of the last output.
- Retrying or rewriting the same valid JSON does not change the result; the exit code comes from the filter semantics, not the input.
