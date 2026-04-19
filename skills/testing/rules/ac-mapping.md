---
title: Map Every Acceptance Criterion to Tests Before Coding
impact: HIGH
impactDescription: Prevents untested ACs — the main driver of endless review cycles
tags: testing, acceptance-criteria, traceability, coverage, discipline
---

## AC-to-Test Traceability

Map every acceptance criterion to test(s) **before writing code**. Unmapped ACs are merge blockers.

**Template (add at top of primary test file):**

```
// AC Coverage for ABC-123:
// AC-1: "User can create order with valid items" → testCreateOrder_validItems()
// AC-2: "Order fails if no items"                → testCreateOrder_emptyItems_throwsValidation()
// AC-3: "Email sent after order"                 → testCreateOrder_sendsConfirmationEmail()
// AC-4: "Concurrent orders safe"                 → [MISSING — add before merge]
```

**Rules:**
- Each AC maps to one or more test names
- `[MISSING]` = merge blocker
- If an AC is untestable as written, flag to ticket author before starting
- E2E tests count for user-facing, integration-level ACs
