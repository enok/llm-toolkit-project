---
title: Alarm E2E must validate the notification path, not just state transitions
category: testing
created: 2026-08-20
tags: [cloudwatch, alarms, sns, email, e2e-testing, notification, silent-failure]
---

# Problem

An E2E test tripped and recovered a set of CloudWatch alarms, validated every
state transition against the dashboard, and declared them "tested and
validated". The owner then asked whether any alarm had reached their inbox:
none had. All ten alarms had empty `AlarmActions`/`OKActions` — mirrored from a
legacy config that shipped with notifications disabled — so every transition
fired silently. State-transition evidence looked complete while the alerting
purpose of the alarms was 0% functional.

# Failed Approaches

- Treating alarm history transitions (OK -> ALARM -> OK) as full validation:
  they prove metric math and thresholds and say nothing about delivery.
- Assuming that faithfully mirroring a legacy config equals correct behavior:
  the inherited `ENABLE_*_NOTIFICATIONS=false` value was itself the defect the
  E2E should have caught.

# Solution

Validate the whole chain, in order:

1. Alarm actions are non-empty (`describe-alarms` -> `AlarmActions`/`OKActions`).
2. The target notification topic exists.
3. Subscriptions are confirmed — check protocol and endpoint, and that none sit
   in `PendingConfirmation`.
4. Trip one alarm per action family and confirm the email or page actually
   arrives.
5. Check the message content: alarm name, state change, threshold reason,
   description.

Re-read alarm descriptions against reality at the same time — one still named a
paging integration whose topic had already been deleted. Any alarm whose latest
transition predates the moment actions were attached has an unproven path;
re-trip it after the fix.

# Why

CloudWatch evaluates alarms and delivers notifications through separate,
independently configured layers. Nothing in alarm state or history reveals that
the action list is empty or that a subscription is stale. "The alarms work" is
therefore two independent claims — detection and delivery — and a test that
proves only detection passes while the pager stays silent.
