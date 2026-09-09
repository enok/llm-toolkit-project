---
title: PutMetricAlarm/PutDashboard are upserts - a Terraform "create" silently overwrites a live same-name resource
category: monitoring
created: 2026-08-19
tags: [cloudwatch, alarm, dashboard, terraform, name-collision, upsert, overwrite]
---

# Problem

Terraform plans "1 to add" for a CloudWatch alarm or dashboard whose
composed name already exists live (hand-made or owned by another stack).
Apply succeeds - and silently replaces the existing resource's entire
configuration with no warning, no error, and no destroy in the plan.

# Failed Approaches

- Trusting the plan: "1 to add, 0 to destroy" reads as safe, but
  Terraform's create path calls the same upsert API, so a collision is
  invisible in the plan.
- Expecting an AlreadyExists error at apply time: CloudWatch alarms and
  dashboards have no such error - the name IS the identity and writes win.

# Solution

Before the first apply of any composed-name alarm or dashboard, verify the
names are unused:

```bash
aws cloudwatch describe-alarms --alarm-names <name>
aws cloudwatch list-dashboards --dashboard-name-prefix <prefix>
```

A hit means an explicit decision: `import` the live resource into state,
or change the composed purpose. Never let a create clobber it implicitly.

# Why

`PutMetricAlarm` and `PutDashboard` are idempotent upserts keyed only by
name. Terraform cannot detect the collision because the resource is not in
its state, and the API gives no conflict signal.
