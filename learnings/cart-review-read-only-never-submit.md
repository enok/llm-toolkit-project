---
title: "Check my cart before I buy" - read page state only and never submit
category: toolchain
created: 2026-11-26
tags: [browser, shopping, cart, checkout, read-only, installments, external-write]
---

# Problem
A user asked for a review of an online cart before purchasing. Any click that changes the cart or
advances checkout could place an order or spend money.

# Failed Approaches
- Clicking "continue" to see the next step.
- Assuming installment options without opening the selector.

# Solution
- Read page state only: items, edition or format, quantity, seller, shipping, installment options,
  total.
- Flag mismatches with the user's stated constraints (physical instead of digital, relevant topic,
  the smallest set that covers the need).
- Re-read the page after the user edits the cart.
- Installment or pay-later options depend on region and card: open the selector and report what it
  shows.
- State explicitly that nothing was changed or submitted
  (`rules/external-write-authorization.md`).

# Why
Reading is reversible, a purchase is not, and the user needs evidence of what is in the cart
rather than an assumption.
