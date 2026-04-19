---
title: GIL Does NOT Eliminate Race Conditions
impact: CRITICAL
impactDescription: Most common Python concurrency misconception
tags: python, concurrency, gil, thread-safety, race-condition
---

## GIL Does NOT Eliminate Race Conditions

Python's GIL prevents two threads from executing bytecode simultaneously, but compound operations are NOT atomic.

**Incorrect (assuming GIL makes this safe):**

```python
counter = 0
def increment():
    global counter
    counter += 1  # NOT atomic: read → add → write (3 bytecode ops)
```

**Correct (explicit lock):**

```python
import threading
counter = 0
lock = threading.Lock()
def increment():
    global counter
    with lock:
        counter += 1
```

The GIL protects against memory corruption at the C level. It does NOT protect against:
- Read-modify-write (`counter += 1`)
- Check-then-act (`if k not in d: d[k] = v`)
- Iterating + modifying a collection
- Any operation that spans multiple bytecode instructions
