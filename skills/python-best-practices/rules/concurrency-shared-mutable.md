---
title: Lock All Access to Shared Mutable Objects
impact: CRITICAL
impactDescription: Prevents stale reads and data corruption
tags: python, concurrency, lock, threading, race-condition
---

## Lock All Access to Shared Mutable Objects

When an object's attributes are modified by multiple threads, every access (read AND write) must be protected by the same lock.

**Incorrect (unsynchronized — Thread B may see stale or partial values):**

```python
class OrderProcessor:
    def __init__(self):
        self.status = "NEW"
        self.errors = []
    def set_status(self, s): self.status = s
    def get_status(self): return self.status
    def add_error(self, e): self.errors.append(e)
    def get_errors(self): return self.errors  # caller can mutate
```

**Correct (lock protects all access, defensive copies on reads):**

```python
import threading

class OrderProcessor:
    def __init__(self):
        self._lock = threading.Lock()
        self._status = "NEW"
        self._errors = []

    def set_status(self, s):
        with self._lock: self._status = s
    def get_status(self) -> str:
        with self._lock: return self._status
    def add_error(self, e):
        with self._lock: self._errors.append(e)
    def get_errors(self) -> tuple:
        with self._lock: return tuple(self._errors)  # defensive copy
```

Key rules:
- Lock both reads and writes — locking only writes is a bug
- Return defensive copies (`tuple(list)`) from locked getters
- Use `with lock:` — never manual `acquire()`/`release()`
- One lock per shared resource
