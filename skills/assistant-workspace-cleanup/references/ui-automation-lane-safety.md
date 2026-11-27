---
trigger: model_decision
description: Load when dispatching any agent or lane that drives a browser or desktop UI (owned tabs only, stable-ID allow-lists, live re-read before acting, named concurrent lanes, no sign-in for the user)
---

# UI automation lane safety

A lane driving a browser or desktop UI works inside the user's own profile,
beside tabs, windows, and sessions it did not create. What it sees there is
shared live state: other sessions, scheduled tasks, or the user can change it
between a snapshot and a click, and look-alike items (repeated titles,
"Untitled" entries) are common. These constraints add to
`rules/external-write-authorization.md` (authority for each mutation) and
`rules/command-safety.md` (credential handoff); they do not replace them.
Procedures that apply them: `skills/assistant-workspace-cleanup/SKILL.md` and
`skills/linkedin-profile-maintenance/references/browser-session-notes.md`.

## Scope of touch

- Record the ID of every tab or window the lane creates, and navigate, reuse,
  or close only those. Pre-existing tabs, even empty ones, are never cleanup
  targets.
- On a cookie or consent prompt, choose the most privacy-preserving option
  offered (reject non-essential cookies); never accept tracking to clear a
  banner.

## Destructive and configuration steps

- Act only on an explicit allow-list of stable IDs (for example the UUID in
  the item's URL) supplied by the dispatch. Never pick a target by title,
  position, or search hit. The dispatch also names known look-alikes as a
  deny-list; a deny-list match stops that item.
- Re-read live state immediately before each destructive or configuration
  step: open the item, confirm its ID matches the allow-list entry, and confirm
  the precondition the plan relied on (empty, paused, finished, unpinned) still
  holds. A snapshot from inventory or approval time is a hint, not evidence.
  The root applies the same re-read to state its plan depends on when it
  presents that plan for approval.
- If live state contradicts the plan, an ID is not on the allow-list, or an
  unexpected dialog appears, skip the item and report it. Never adapt the
  action to the new state.
- Sliding or animated panels move under the pointer: wait for them to settle,
  take a fresh screenshot, click again, and confirm the result from a state
  summary, not from the click. A setting can live both in the operating system
  and in a vendor app; check both before reporting it changed.

## Concurrent lanes

- Every dispatch of a UI lane names the other lanes, sessions, or scheduled
  tasks known to be active on the same account or browser profile, with their
  scope, so observed side effects are attributed correctly. Changes inside a
  named scope are expected; changes outside every named scope are reported,
  never assumed benign.
- Split concurrent UI lanes by disjoint ID sets, per
  `rules/multi-agent-orchestration.md`.

## Sign-in

- Never sign in, enter credentials, approve a second factor, or trust a new
  device on the user's behalf. If the browser in use is not signed in (for
  example it redirects to a login page), stop and ask which signed-in browser
  to use, or ask the user to sign in.

## Return

- Report per ID: the live state confirmed just before acting, the action, and
  the result.
- Report every deviation explicitly: a tab or window touched that the lane did
  not create, an item skipped or changed outside the allow-list, a changed
  precondition, an unattributed change in shared state. With none, state
  `deviations: none`.
