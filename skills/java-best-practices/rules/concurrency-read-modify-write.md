---
title: Atomic Operations for Read-Modify-Write
impact: CRITICAL
impactDescription: Prevents lost updates from concurrent modifications
tags: java, concurrency, atomic, race-condition, AtomicInteger
---

## Atomic Operations for Read-Modify-Write

Two threads read the same value, both modify it, one write overwrites the other. Use atomic classes.

**Incorrect (race condition — count++ is NOT atomic):**

```java
private int count = 0;
public void increment() {
    count++;  // read count → add 1 → write count (3 ops)
}
```

**Correct (atomic operation):**

```java
private final AtomicInteger count = new AtomicInteger(0);
public void increment() {
    count.incrementAndGet();  // atomic read-modify-write
}
```

**Incorrect (check-then-act race):**

```java
if (!map.containsKey(key)) {
    map.put(key, computeValue());  // another thread can put between check and put
}
```

**Correct (atomic check-then-act):**

```java
map.computeIfAbsent(key, k -> computeValue());  // ConcurrentHashMap: atomic
```
