---
title: Race Conditions in Single-Threaded JavaScript
impact: CRITICAL
impactDescription: Prevents lost updates and inconsistent state across await boundaries
tags: javascript, typescript, async, race-condition, mutex, concurrency
---

## Race Conditions in Single-Threaded JavaScript

JavaScript is single-threaded but NOT free of race conditions. Every `await` yields control, creating interleave points where shared mutable state can be read/written by other async operations.

**Incorrect (stale read across await — two concurrent calls can both deduct):**

```typescript
let balance = 100;

async function debit(amount: number): Promise<void> {
  const current = balance;          // read
  await verifyFunds(current);       // yield — another call interleaves here
  balance = current - amount;       // write stale value
}
```

**Correct (mutex for async critical sections):**

```typescript
import { Mutex } from "async-mutex";
const balanceMutex = new Mutex();

async function debit(amount: number): Promise<void> {
  const release = await balanceMutex.acquire();
  try {
    await verifyFunds(balance);
    balance -= amount;
  } finally {
    release();
  }
}
```

Key insight: Every `await` is a potential interleave point. If shared state is read before `await` and written after, another operation can modify it in between.
