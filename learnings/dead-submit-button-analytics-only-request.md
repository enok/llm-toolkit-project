---
title: A Next button that only fires an analytics request is a page-side defect, not a user error
category: testing
created: 2026-10-22
tags: [web-forms, debugging, network, analytics, instrumentation, submit, workaround]
---

# Problem

An application form showed no validation errors, every field was filled and the
user clicked Next repeatedly, but the screen never changed. Browser DevTools
showed a single request per click: an analytics event.

# Failed Approaches

- Re-entering the same values and reloading.
- Assuming a server error; there was no request to the product's own API at all.
- Reading the browser console, which was empty.

# Solution

- Reproduce in a second tab and without tracking parameters in the URL.
- Hook `fetch`, XHR, `pushState`, `window.open`, `submit`, `error` and
  `unhandledrejection`, click, and read the log; read the analytics payload to see
  which step the page believes it is in.
- Compare file-upload calls: "get signed URL -> PUT to storage" without a final
  call that registers the file may leave the next step with nothing to submit.
- Rule out captcha (no script or iframe) and extensions (private window).
- If two independent sessions fail identically, stop at 15 minutes and use a
  workaround: private window, the provider's main portal, a support email
  quoting the listing reference, or move on and record "not submitted - site defect".

# Why

The handler runs (hence the analytics event) and then returns early on a state
check the user cannot see; neither the server nor the user input is at fault, so
more retries cannot fix it. See `skills/web-form-submit-debugging/SKILL.md`.
