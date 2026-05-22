---
title: Use Concurrent Collections and Atomics
impact: CRITICAL
impactDescription: Thread-safe without manual synchronization
tags: java, concurrency, ConcurrentHashMap, AtomicReference, thread-safety
---

## Use Concurrent Collections and Atomics

Prefer `java.util.concurrent` over manual `synchronized`.

| Need | Use | Not |
|------|-----|-----|
| Thread-safe map | `ConcurrentHashMap` | `Collections.synchronizedMap()` |
| Thread-safe counter | `AtomicInteger` / `AtomicLong` | `synchronized` + `int` |
| Thread-safe reference swap | `AtomicReference<T>` | `synchronized` + field |
| Thread-safe list (read-heavy) | `CopyOnWriteArrayList` | `Collections.synchronizedList()` |
| Thread-safe queue | `LinkedBlockingQueue` | manual lock + ArrayList |
| Coordinating threads | `CountDownLatch` / `CyclicBarrier` | `wait()` / `notify()` |

**Example — AtomicReference for thread-safe snapshot swap:**

```java
private final AtomicReference<OrderSnapshot> currentSnapshot = new AtomicReference<>();

public void updateSnapshot(OrderSnapshot newSnapshot) {
    currentSnapshot.set(newSnapshot);  // atomic, visible to all threads
}

public OrderSnapshot getSnapshot() {
    return currentSnapshot.get();  // always sees latest value
}
```
