---
title: Reject browser harnesses that require CDP on the user's real browser
category: security
created: 2026-08-21
tags: [external-skill-intake, browser, cdp, screenshots, evidence, cookies, telemetry, rejection]
---

# Problem

Evaluated a popular open-source browser-automation harness
(`github.com/browser-use/browser-harness`, MIT-licensed, actively maintained)
for import as a browser-interaction and screenshot skill — motivated by wanting
to screenshot a CloudWatch widget after a Terraform apply and attach it as
evidence.

# Failed Approaches

- Automated clearance: the skill-source trust lookup
  (`scripts/check-new-skill-security.sh` with `GEN_AGENT_TRUST_HUB_SKILL_URLS`)
  returned `Invalid skill URL` (HTTP 400) for the repo root, the `SKILL.md`, and
  the bundled plugin path. No `SAFE` severity is obtainable, which alone blocks
  automated intake.
- Manual source review of the version reviewed on 2026-08-21: the project is
  legitimate and professionally built, but architecturally unsafe for an agent
  environment.
  1. It requires enabling Chrome remote debugging on the user's real browser.
     Once on, the CDP endpoint exposes every logged-in session — SSO, cloud
     consoles, email — to any local process, persistently.
  2. Its profile-sync feature ships real browser cookies to a third-party cloud
     and installs an opaque binary via `curl ... | sh`.
  3. It instructs agents to use "stealth settings" and clean IPs when captchas
     or blocking are likely; bot-detection evasion conflicts with acceptable use.
  4. Telemetry is opt-out and on by default, with a persisted install id.
  5. Its trigger ("always use this for any web interaction") would hijack
     routing away from already-sanctioned browser surfaces.
  6. Agents append arbitrary Python to a helpers file that is then persisted and
     auto-executed on every later run, unreviewed.

# Solution

Reject the import and cover the motivating use cases with sanctioned paths:

- **Metric/widget evidence:** `aws cloudwatch get-metric-widget-image` produces
  a deterministic PNG from the metrics API — no browser, scriptable in a
  pipeline, attachable to a PR or wiki page. For dashboards, render each
  widget's `MetricWidget` JSON.
- **Interactive console checks:** use the agent environment's own
  permission-gated browser surface, which does not require a machine-wide debug
  endpoint.
- **Proof that traffic arrived:** metric and log queries (`get-metric-data`,
  Logs Insights) are stronger evidence than a screenshot and should accompany
  any image.

# Why

The harness's core mechanism — a standing CDP websocket into the user's real
logged-in browser — is itself the hazard, and no amount of skill-text adaptation
removes it because the value proposition depends on it. Intake rule applied:
prefer reviewed patterns over vendoring, and when the trust gate cannot return
`SAFE` and manual analysis finds structural risk, reject rather than sandbox.
Re-evaluate only if a later version offers an isolated-profile-only mode with no
real-profile CDP requirement, no cookie cloud sync, and telemetry off by default.
