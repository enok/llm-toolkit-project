---
title: Avoid O(n²) — Use Dict/Set for Lookup
impact: MEDIUM
impactDescription: O(n²) to O(n) for collection matching
tags: python, performance, algorithmic-complexity, collections
---

## Avoid O(n²) — Use Dict/Set for Lookup

Never nest loops over collections. Build a lookup dict or set first.

**Incorrect (O(n²) — scans active_users for every order):**

```python
for order in orders:
    for user in active_users:
        if user.id == order.user_id:
            pass  # match
```

**Correct (O(n) — build lookup dict first):**

```python
user_by_id = {user.id: user for user in active_users}
for order in orders:
    user = user_by_id.get(order.user_id)
    if user:
        pass  # match
```

- Three levels of nesting is a red flag — extract inner loops into named functions
- Use `set` for membership checks — `O(1)` vs `list` at `O(n)`
- Batch external calls — never call a database or HTTP API inside a loop
