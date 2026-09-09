---
title: JSON validity does not prove metric-math validity
category: monitoring
created: 2026-08-26
tags: [cloudwatch, json, metric-math, validation, arity, syntax]
---

# Problem

Removing a term from inside `IF()` during a dashboard edit changed its
arity. The result still parsed as valid JSON but was invalid CloudWatch
metric math, silently breaking the widget. The dashboard applied
successfully but the widget rendered no data.

# Failed Approaches

- Trusting JSON validation: `jq`, `python -m json.tool`, and Terraform's
  JSON parser all accepted the file. JSON structure was valid; the metric
  math inside was not.
- Visual inspection: the IF expression looked plausible and similar to
  working examples in other widgets.
- Assuming apply-time validation: the apply succeeded without error.
  CloudWatch accepts invalid metric math and returns success; the widget
  fails silently at render time instead.

# Solution

Validate metric math expressions beyond JSON syntax - check arity and
balance before every apply:

```python
import re

def validate_metric_math(expr):
    if expr.count('(') != expr.count(')'):
        return False, "Unbalanced parentheses"
    for m in re.finditer(r'IF\([^)]+\)', expr):
        inside, depth, commas = m.group(0)[3:-1], 0, 0
        for ch in inside:
            if ch in '([': depth += 1
            elif ch in ')]': depth -= 1
            elif ch == ',' and depth == 0: commas += 1
        if commas != 2:
            return False, f"IF() needs 3 args, found {commas + 1}"
    if re.search(r'[+\-*/]\s*[)\]]|[(\[]\s*[+\-*/]', expr):
        return False, "Dangling or consecutive operators"
    return True, "Valid"
```

Run this over every widget expression in the contract test suite before
every dashboard apply, not just once during initial authoring.

# Why

CloudWatch metric math has syntax rules beyond JSON structure: `IF()`
requires exactly 3 arguments, operators must be binary, and metric IDs must
be referenced before use. The dashboard and alarm APIs accept any
well-formed JSON and return success; invalid expressions fail silently at
render time, showing "No data available" with no error surfaced anywhere.
JSON validity is necessary but not sufficient for metric-math validity.
