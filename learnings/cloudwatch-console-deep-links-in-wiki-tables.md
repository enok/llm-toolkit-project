---
title: CloudWatch console deep links in wiki tables — formats, encoding, and the account caveat
category: toolchain
created: 2026-08-19
tags: [cloudwatch, console-url, confluence, deep-link, dashboards, alarms, metrics]
---

# Problem

A central Confluence index page (Metrics / Alarms / Dashboards tables) needed
every resource name to link to the AWS console, with separate STAGE and PROD
columns — but CloudWatch console URLs are awkward to deep-link and carry no
account identity.

# Failed Approaches

- Writing the page in Markdown: CloudWatch metrics URLs contain balanced
  parentheses (`#metricsV2?graph=~()&query=~'...`) and `~'` sequences that
  Markdown link syntax mangles or truncates at the first `)`.
- Hoping for per-account URLs: the console URL does not encode the AWS account,
  so a "STAGE link" and a "PROD link" to same-named resources are byte-identical.

# Solution

Author the page in HTML content format, escaping `&` as `&amp;` inside hrefs.
Working link shapes (example region `us-west-2`):

- Dashboard:
  `https://<region>.console.aws.amazon.com/cloudwatch/home?region=<region>#dashboards/dashboard/<Name>`
- Alarm prefix search: `...#alarmsV2:?search=<name-prefix>`
- Metrics search: `...#metricsV2?graph=~()&query=~'<term>`, with `/` encoded as
  `*2f` — e.g. `~'MyApp*2fUpstream`.

State the caveat on the page itself: a link opens in whichever account the
reader is signed into, so the reader must sign into the matching account
(`<stage-account-id>` vs `<prod-account-id>`) before clicking.

# Why

The CloudWatch console keeps its state in the URL fragment using a custom
`~`-based encoding rather than standard percent-encoding, so generic URL
escaping breaks it while the raw characters break Markdown. Authoring in HTML
sidesteps the Markdown parser entirely. Account identity lives in the session
cookie, not in the URL, so a per-environment link is impossible without an SSO
portal deep link — a documented sign-in convention is the practical fix.
