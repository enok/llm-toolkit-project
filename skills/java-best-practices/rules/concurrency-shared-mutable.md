---
title: Synchronize All Access to Shared Mutable Objects
impact: CRITICAL
impactDescription: Prevents stale reads and data corruption
tags: java, concurrency, synchronized, lock, thread-safety, race-condition
---

## Synchronize All Access to Shared Mutable Objects

When an object's fields are modified by multiple threads, every access (read AND write) must be synchronized on the same lock.

**Incorrect (unsynchronized — Thread B may see stale or partial values):**

```java
public class OrderProcessor {
    private String status = "NEW";
    private List<String> errors = new ArrayList<>();

    public void setStatus(String s) { this.status = s; }
    public String getStatus() { return this.status; }
    public void addError(String e) { errors.add(e); }
    public List<String> getErrors() { return errors; }  // caller can mutate
}
```

**Correct (private lock, synchronized reads AND writes, defensive copies):**

```java
public class OrderProcessor {
    private final Object lock = new Object();
    private String status = "NEW";
    private final List<String> errors = new ArrayList<>();

    public void setStatus(String s) {
        synchronized (lock) { this.status = s; }
    }
    public String getStatus() {
        synchronized (lock) { return this.status; }
    }
    public void addError(String e) {
        synchronized (lock) { errors.add(e); }
    }
    public List<String> getErrors() {
        synchronized (lock) { return List.copyOf(errors); }
    }
}
```

Key rules:
- Never `synchronized(this)` — use a private `final Object lock`
- Synchronize both reads and writes — locking only writes is a bug
- Return defensive copies from synchronized getters
