---
title: A question is not a change request
category: toolchain
created: 2026-11-26
tags: [intent, classification, voice-input, confirmation, status-question, misclassification]
---

# Problem
The user asked a status question ("are the tasks in the calendar?"). The agent treated it as an
instruction and created or changed calendar entries. The input came from voice dictation,
which contains false starts and half-sentences that make a question look like a command.

# Failed Approaches
- Acting on the verbs in the text: a phrase with "tasks" and "calendar" in it was read as
  "put the tasks in the calendar".
- Asking for confirmation in a long message: it buried the answer to the original question.

# Solution
- Answer a status or clarifying question first, from what is actually there (read the
  calendar, the file, the ledger) and say what you found.
- Only act when the user gives an instruction, or after an offer such as "they are not there;
  want me to add them?" that the user accepts.
- Read dictated input for its final intent: discard false starts and corrections that the
  user abandoned, and if two readings remain, ask one short question.
- Keep confirmations short: what was done, what was not, and what happens next.

# Why
Reading is free and reversible; writes are not. Misclassifying a question as a command turns a
cheap answer into an unrequested change. See also `rules/external-write-authorization.md` for
what needs explicit approval, and `learnings/calendar-event-update-replaces-description.md`
for one write that is easy to get wrong.
