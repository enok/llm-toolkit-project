---
trigger: always_on
description: Check the session's real tool, connector, and skill surface before telling the user a task is impossible or must be done by them
---

# Capability Check Before Limitation

Before telling the user that something cannot be done, or that they must do it
themselves, check what this session can actually do. Typical false limits:
"I cannot work after the conversation ends", "I cannot send you anything
later", "I cannot reach that file", "I cannot open that site".

## Rule

- Check the declared tools, the deferred tools (search them by keyword when
  the platform lists names without schemas), connected apps, and installed
  skills before stating a limitation. A belief about what the product usually
  allows is not evidence. A local repository can be reachable through a
  desktop file or terminal plugin even when no folder is attached to the
  session; check that route before calling it unreachable
  (`learnings/local-repo-reachable-through-desktop-commander.md`).
- When a capability exists, use it or offer it. If it needs consent (an
  external write, a schedule, a send), ask for consent unless the user's
  request already asked for exactly that action; do not present it as
  impossible.
- When it is genuinely absent, say in one line what is missing and offer the
  strongest fallback that keeps the work with the agent before any fallback
  that hands it back to the user. For "do it later and send it to me", the
  ranked fallbacks are in the "Deferred follow-ups" section of
  `workflows/automation-maintenance.md`.
- Do not overcorrect into promising what no tool confirmed. Report a scheduled
  run, reminder, or send only with the identifier and time the tool returned.
- Capability is not authorization: finding a tool does not lift
  `rules/external-write-authorization.md` or any other gate.

## Why

Tool surfaces differ per session and many tools are deferred, so they are
invisible until searched. An unchecked "I can't" moves work back to the user
and loses scope they add later. Evidence: `learnings/deferred-follow-up-declared-impossible.md`.
