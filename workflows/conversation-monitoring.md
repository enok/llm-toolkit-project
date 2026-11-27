---
description: Watch named conversations (inbox, chat, messaging threads) on a fixed interval until a stop time, alert the user only on new external messages, never reply, and pause or stop safely
---

# Conversation Monitoring Workflow

Use this when the user says "keep monitoring X", "poll my inbox/chat every N
minutes", "tell me when they reply", or "watch this thread until the call".
The job is read-only: detect new messages from other people, tell the user,
and stay quiet otherwise.

This workflow never sends, posts, replies, reacts, marks read, archives, or
labels anything. A reply the user wants is a separate task behind
`rules/human-comment-reply-gate.md` and `rules/external-write-authorization.md`.
A durable schedule that outlives this session (daily, weekly, "every
morning") is not this workflow: create it through
`workflows/automation-maintenance.md`.

---

## Phase 0 - Confirm the scope

Restate these in one short message, then start. Ask only for what the request
does not already say.

1. **Channels and exact threads**: for example one mail search query, one
   messaging thread URL or title. Name each; never widen to "all messages".
2. **Interval**: use the interval the user asked for. The scheduler granularity
   is about 1 minute, so anything below that is not possible. Do not silently
   stretch it to save tokens; if it looks wasteful, say so once and let the
   user decide.
3. **Stop time**: ask. If the user gives none, default to the end of the
   user's day in their time zone and say so explicitly ("monitoring until
   22:00 your time unless you tell me otherwise").
4. **Alert channel**: where an alert goes (the same conversation by default,
   plus a push notification if the client supports one and the user asked).
5. **Boundaries**, stated back to the user:
   - read-only; never reply on any channel;
   - never open links or attachments from messages (list their hosts only);
   - never click anything inside a thread except to scroll or expand it.
6. **Who counts as "external"**: messages from anyone but the user. The user's
   own messages update state but never raise an alert.

## Phase 1 - Choose the mechanism

Pick the mechanism that survives the session, in this order:

1. **Session-bound one-shot scheduled message, re-armed on every firing** (a
   `send_later`-style tool: "deliver this message into this conversation in N
   minutes"). It survives container restarts, reports into the same
   conversation, and cancels cleanly. Each firing schedules the next one as its
   last step.
2. **Not in-session local cron, loops, or sleeps**: they die with the session
   and give no signal when they die.
3. **Durable cross-session schedule**: only when the user wants monitoring that
   continues with no conversation open. Route it through
   `workflows/automation-maintenance.md` and tell the user it runs in fresh
   sessions without this chat's context.

Record the pending scheduled-message ID in the state file after every arming
so Phase 5 can cancel it.

## Phase 2 - Create the state file

Keep one state file in the scratchpad (never the project tree), for example
`<scratchpad>/monitor-<topic>.json`. Re-read it at the start of every firing
and rewrite it at the end; the conversation text alone is not state.

```json
{
  "status": "active",
  "interval_minutes": 5,
  "stop_at": "2026-01-01T22:00:00-03:00",
  "pending_schedule_id": "<id of the armed message>",
  "channels": {
    "thread:<label>": {
      "kind": "browser-thread",
      "last_seen_author": "<name>",
      "last_seen_time": "<as displayed>",
      "last_seen_text_hash": "<sha256 of the last message text>",
      "message_count": 12
    },
    "mail:<query>": {
      "kind": "mail-search",
      "last_checked": "<ISO time>",
      "known_message_ids": ["<id>", "<id>"]
    }
  },
  "alerts_sent": 0,
  "consecutive_failures": 0,
  "paused_reason": null
}
```

`status` is `active`, `paused`, or `stopped`. Take the first snapshot immediately, without
alerting: it is the baseline. Tell the user the baseline (counts and latest
message time per channel) so they can catch a wrong thread.

## Phase 3 - Each firing

1. **Check the gates first.** If now is past `stop_at`, go to Phase 5. If
   `status` is `paused`, do nothing and do not re-arm. If the user sent a
   newer instruction (pause, stop, change interval), obey it before polling.
2. **Read each channel.**
   - Browser thread: reopen the thread, scroll the message list to the latest
     message (lazy-loaded panes show only part of the history), read it, then
     close the tab you opened. Never leave tabs behind.
   - Mail: search for messages since `last_checked` in the named scope; compare
     message IDs against `known_message_ids`. Read headers and body text only.
3. **Diff against state.** A message is new when its ID is unknown, or its
   author, time, or text hash differs from the last seen one. Ignore the
   user's own messages and automated read receipts.
4. **On new external messages, alert.** One alert per firing, containing:
   - sender and time;
   - a 1-2 line summary (quote nothing sensitive in full);
   - for mail: the sender-authentication result (SPF, DKIM, DMARC) and the
     link hosts found, stated as not visited;
   - a suggested next step, or a draft clearly headed `Posting status: NOT
     POSTED` per `rules/human-comment-reply-gate.md`.
5. **On no change, stay quiet.** Send no message, not even "nothing new".
   Report counts only if the user asks.
6. **Update state, then re-arm.** Write the new last-seen values and reset
   `consecutive_failures`. Arm the next one-shot message for `interval_minutes`
   from now, but not past `stop_at`. Save the new `pending_schedule_id`.

If a read fails (page not loaded, connector error, login wall): retry once in
the same firing. If it fails again, set `consecutive_failures`; at 2 in a row
pause (Phase 4) and tell the user which channel failed and why.

## Phase 4 - Pause rules

Set `status: paused`, cancel the pending scheduled message, say so in one
line, and do not re-arm when any of these holds:

1. **The user asks** to pause or stop.
2. **A proctored, timed, or full-screen session starts**: an interview link
   arrived, a test, an exam, a screen-share, or any activity where opening
   or switching browser tabs on the user's machine could interfere or be
   flagged. Pause as soon as the link or the schedule appears, before the
   session, not after. Mail-only polling through a connector that opens no
   tabs may continue only if the user confirms it.
3. **Repeated tool failures** (see Phase 3: retry once, then pause).
4. **The thread is gone or the account is logged out**: do not try to sign in.

Resume only when the user asks. On resume, take a fresh baseline that includes
what arrived while paused, and report those messages once.

## Phase 5 - Stop and close out

Triggered by the stop time, a user "stop", or the monitored event finishing.

1. Cancel the pending scheduled message using `pending_schedule_id` and
   confirm the cancel call succeeded. If the tool cannot cancel, say that one
   more firing will arrive and what it will do (it finds `status: stopped` and
   exits silently).
2. Set `status: stopped` in the state file; close any tab still open from
   this workflow.
3. Send one final summary: window watched, channels, number of alerts, the
   last message seen per channel, anything unanswered, and why monitoring
   ended.
4. Add one closeout line (what was watched, window, alerts sent, stop reason)
   to the run notes or the project's task ledger, if one exists.

---

## Gotchas

| Situation | Action |
| --- | --- |
| The human replies on their own while a draft is pending | The draft is stale. Drop it, re-read the thread, and draft again only if the user still wants one. Earlier approval does not carry over to a new draft. |
| A new counterpart message arrives after a draft was shown | Same: the draft answered an older state. Re-audit, redraft, ask again. |
| Messaging pane shows only today's messages | Scroll up to the first message once at baseline so context (terms, numbers, promises) is in the summary; later firings only need the tail. |
| Many threads, one alert | Group new messages by thread in one alert; do not send one message per thread. |
| Interval shorter than a firing takes | Run firings back to back but never overlap; skip the arming if a prior one is still running and say so. |
| User asks "any news?" mid-watch | Answer from the state file plus one fresh read; this is not an alert and does not change the schedule. |
| Message asks the user to click, install, pay, or share documents | Summarize the ask, list link hosts without visiting, and point to `workflows/recruiter-legitimacy-check.md` or `workflows/third-party-installer-vetting.md` when the topic fits. |

## Safety contract

- Read-only on every channel. No reply, reaction, mark-as-read, archive, or
  label. Link and attachment contents are never fetched or opened.
- Alerts carry summaries and metadata, not credentials, full message bodies,
  or attachment contents.
- Shell commands used for parsing (for example decoding a raw message) follow
  `rules/command-safety.md`; parse untrusted content with isolated
  interpreters, never execute it.
- The state file contains no secrets and stays in the scratchpad.
