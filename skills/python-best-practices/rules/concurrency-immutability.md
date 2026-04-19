---
title: Immutability as First Defense Against Race Conditions
impact: CRITICAL
impactDescription: Eliminates entire class of concurrency bugs
tags: python, concurrency, immutability, frozen, dataclass, thread-safety
---

## Immutability as First Defense Against Race Conditions

If state can't change, it can't be corrupted by concurrent access. No locking needed.

**Incorrect (mutable, unsafe to share across threads):**

```python
class OrderSnapshot:
    def __init__(self, order_id, total, item_ids):
        self.order_id = order_id
        self.total = total
        self.item_ids = item_ids  # mutable list — caller can modify
```

**Correct (frozen dataclass, tuple for collections):**

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class OrderSnapshot:
    order_id: str
    total: float
    item_ids: tuple[str, ...]  # tuple, not list — immutable

# Create new instead of mutating
def update_total(snapshot: OrderSnapshot, new_total: float) -> OrderSnapshot:
    return OrderSnapshot(
        order_id=snapshot.order_id,
        total=new_total,
        item_ids=snapshot.item_ids,
    )
```

Key rules:
- `frozen=True` — prevents attribute assignment after creation
- Use `tuple` instead of `list` for collection fields
- Create new objects instead of mutating existing ones
- `NamedTuple` is also immutable by default
- Rule of thumb: shared across threads → make immutable. Can't be immutable → use a lock.
