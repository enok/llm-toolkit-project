---
title: LinkedIn messaging history lazy-loads; a single page-text read shows only the latest day
category: toolchain
created: 2026-10-22
tags: [linkedin, messaging, lazy-load, browser-automation, get-page-text, innerText, truncation, thread-history]
---

# Problem
An agent read a LinkedIn conversation with a browser page-text tool to catch up before replying. The result contained only the most recent day's messages, so it looked like a short, complete thread. The earlier messages held the decisive context (the commercial terms). An approved reply went out on another channel before that context was read, and the user then set the rule: do not reply before seeing all LinkedIn messages.

# Failed Approaches
- **One page-text read of the open conversation.** The messaging pane lazy-loads older messages as the list is scrolled up, so the read returned only what had been rendered (the latest day). Nothing in the output said it was partial.
- **Returning the whole `innerText` of the message list in one value.** The tool output truncates long strings (about 1.2k characters per returned value was observed), so even a fully loaded list came back cut off mid-thread.
- **Reading immediately after navigation.** On a slow load the message list can come back empty; treating that as "no messages" is wrong.

# Solution
1. Use the browser profile that is already signed in. Never type or request the user's password; if the session is signed out, hand the login to the user.
2. Open the conversation and find the scrollable ancestor of the message list. Scroll it to the top repeatedly (set `scrollTop = 0`, wait a moment, repeat) until the first message or the conversation-start marker is rendered and the scroll height stops growing.
3. Extract the list text with the page-script tool, not the page-text tool:
   - Observed selector (class names are generated and change without notice): `.msg-s-message-list-content`. It may change; if it matches nothing, fall back to the whole conversation pane.
   - Read `innerText` in slices of about 1,000 characters, locating each slice with `indexOf('<anchor text>')` on the previous slice's last words, so no slice is lost to truncation.
4. If the list is empty, wait a few seconds and retry once before concluding it is empty.
5. Record the oldest message date seen. Do not draft until it reaches the conversation start, and re-read the newest messages on every channel immediately before any send.

```js
const list = document.querySelector('.msg-s-message-list-content');
let box = list; while (box && box.scrollHeight <= box.clientHeight) box = box.parentElement;
box.scrollTop = 0;                       // repeat until scrollHeight stops growing
const t = list.innerText;                // then read in slices:
t.slice(t.indexOf('<anchor>'), t.indexOf('<anchor>') + 1000);
```

# Related

- `learnings/linkedin-details-pages-lazy-load-in-main-container.md`: the same
  lazy-loading pattern on profile detail pages.

# Why
LinkedIn renders older messages on demand, so the DOM at page load is a window onto the thread, not the thread. Page-text tools return what the DOM holds at that moment, and the tool layer separately caps each returned value (about 1.2k characters observed). A partial read therefore looks like a complete one. Completeness has to be proved by reaching the first message, and long text has to be read in anchored slices. Related: `rules/external-write-authorization.md` and `rules/human-comment-reply-gate.md` govern the send itself.
