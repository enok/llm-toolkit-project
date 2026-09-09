---
title: Terraform and observability contract testing
tags: [terraform, observability, dashboards, alarms, metrics, contract-testing, evidence]
---

# Terraform and observability contract testing

Use this contract when Terraform manages runtime infrastructure, dashboards,
metrics, alarms, notifications, or externally stored configuration. Source
validation and post-apply evidence are separate gates: neither substitutes for
the other.

## Structural Terraform contract

- Keep one correspondingly named test module for every `.tf` file in each
  explicitly configured deployable Terraform root. Add a meta-test that fails
  when either side is unmatched within that declared scope.
- Each module accounts for every declared resource and important nested
  contract. When a resource owns a dashboard, keep one explicitly named test
  per widget and a meta-test that fails on an unowned widget ordinal.
- Test names and comments should identify the resource or widget they own.
  Parameterization may cover cases, but must not hide that ownership.
- Production modules are offline source contracts unless live Production
  validation is separately authorized. Never generate Production traffic,
  metrics, alarm transitions, notifications, or rendered evidence by default.

## Non-Production post-apply contract

- This reference grants no cloud-write authority. Live stimuli, metric
  publication, alarm transitions, and notification delivery require a current
  instruction that names the account, environment, authorized actions, and
  dedicated test recipient; otherwise keep validation read-only.
- Allow live execution only for an explicit non-Production environment and
  account mapping. Verify branch/context, environment, and current cloud
  identity before any stimulus or readback; unknown identity fails closed.
- Compare configuration, Terraform state, and the authoritative live API for
  every declared resource. Exact deployed dashboard bodies, remote object
  bytes, and preserved configuration blocks matter; source parsing alone is
  insufficient.
- Finalize a redacted result manifest and checksums in a `finally` path so a
  drift, API, rendering, or partial-capture failure still leaves auditable
  evidence.

## Dashboard, metric, and alarm semantics

- Verify ratios with zero-safe expressions and complete denominators. Validate
  totals, units, dimensions, thresholds, periods, and an intentional
  missing-data policy against the business meaning, not only JSON syntax.
- Detect retired dependencies in metric queries, log-group names, dimensions,
  and fields as well as widget titles. Change-log or rollout text belongs in a
  canonical runbook, not a permanent operational dashboard widget.
- Give each data-bearing widget a bounded case matrix covering every distinct
  visible or raw series or discrete outcome, plus meaningful states such as
  zero, normal, threshold edge, and breaching. Do not claim enumeration of
  every value in an unbounded continuous domain.
- Pair each controlled case with a stimulus identity and time window, metric or
  log readback, and rendered visual evidence. Static text or header widgets use
  content and layout contracts instead of fabricated data.
- Never publish fabricated data into provider-owned metric namespaces. Use a
  dedicated validation namespace with a small fixed reusable metric bank; keep
  run identifiers in artifact metadata rather than dimensions, and enforce a
  cardinality budget.
- Notification acceptance requires the expected alarm transition and an
  actually delivered, correlation-bearing message. A successful publish or
  topic invocation alone is not delivery proof. If no dedicated test recipient
  exists, report that dependency instead of notifying unrelated subscribers.
