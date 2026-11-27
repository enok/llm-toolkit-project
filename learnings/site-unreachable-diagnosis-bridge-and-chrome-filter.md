---
title: A site will not open for the user - diagnose in layers, and know the browser tool's URL filter
category: environment
created: 2026-11-26
tags: [network, diagnosis, curl, dns, tls, vpn, claude-in-chrome, url-filter, computer-use, request_access]
---

# Problem
A user could not open a website. The agent had three vantage points (cloud sandbox, the user's
PC through the device bridge, and a browser tool) and the first answers pointed in different
directions: one tool refused to navigate at all, and the site was slow rather than down.

# Failed Approaches
- Concluding "the site is blocked" because `claude-in-chrome` `navigate` refused the URL: that
  tool can apply a built-in URL category filter, so the refusal is a tool limit, not evidence
  about the site.
- Testing only from the sandbox: it proves the site is up from there, not from the user's
  network.
- Taking `computer_*` screenshot or click tools straight to a window: they need
  `computer_request_access` naming the app first.

# Solution
Work from the outside in and stop at the layer that fails:
1. Sandbox first (is the site up at all?).
2. The user's PC: DNS, hosts file, TCP connect, proxy and VPN settings, system clock, TLS.
3. A clean browser profile (no extensions, no sync).
- Compare `curl` with a browser user agent against plain `curl` timing. A multi-second gap on
  HTTPS usually means security software is scanning the connection. Phone-hotspot IP ranges and
  outdated browsers also trigger anti-bot challenges.
- If `claude-in-chrome` blocks the URL, report it as a tool-level block. Do not switch to another
  browser tool to open it. A reachability probe with `curl.exe` on the PC (no sign-in, no form
  data) is allowed for diagnosis only, with the user's consent.
- Before any `computer_*` action, call `computer_request_access` for the exact app.
- UI panels animate in: take a fresh screenshot before clicking an element found in an earlier one.
- A vendor driver app can override an OS setting (for example a peripheral's scroll or button
  behaviour): check both the OS settings and the vendor's own app.
- Related: a security filter can also cause local-file "Access denied".

# Why
Each vantage point answers a different question, so the order narrows the cause quickly.
Tool-level URL filters and permission gates produce failures that look like site problems.
Inference, from one case: the timing gap is a hint, not proof, so confirm by repeating with the
security software's HTTPS scanning disabled when the user agrees.
