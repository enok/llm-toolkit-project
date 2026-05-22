---
title: Immutability as First Defense Against Race Conditions
impact: CRITICAL
impactDescription: Eliminates entire class of concurrency bugs
tags: java, concurrency, immutability, thread-safety, final
---

## Immutability as First Defense Against Race Conditions

If state can't change, it can't be corrupted by concurrent access. No synchronization needed.

**Incorrect (mutable, unsafe to share across threads):**

```java
public class User {
    public String name;
    public List<String> roles;  // caller can mutate
}
```

**Correct (immutable, thread-safe by construction):**

```java
public final class OrderSnapshot {
    private final String orderId;
    private final BigDecimal total;
    private final List<String> itemIds;

    public OrderSnapshot(String orderId, BigDecimal total, List<String> itemIds) {
        this.orderId = orderId;
        this.total = total;
        this.itemIds = List.copyOf(itemIds);  // defensive copy + unmodifiable
    }

    public String getOrderId() { return orderId; }
    public BigDecimal getTotal() { return total; }
    public List<String> getItemIds() { return itemIds; }
}
```

Key rules:
- `final` class — prevents subclasses from adding mutable state
- `final` fields — set once in constructor, visible to all threads (JMM guarantee)
- `List.copyOf()` — defensive copy + unmodifiable
- No setters — once constructed, the object never changes
- Rule of thumb: shared across threads → make immutable. Can't be immutable → synchronize.
