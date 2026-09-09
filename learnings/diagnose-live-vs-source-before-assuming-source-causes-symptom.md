---
title: Diagnose live-versus-source before assuming source causes the symptom
category: deployment
created: 2026-08-26
tags: [terraform, drift, live, source, cloudwatch, dashboard, root-cause]
---

# Problem

Three parallel lanes converted dashboard source files to fix reported rendering
gaps. The deployed stage dashboards had been correct all along — the repo files
were the stale side. The whole conversion effort was unnecessary and added churn
to an already-complex campaign.

# Failed Approaches

- Assuming source drives live: when a user reports gaps in a live dashboard, the
  intuitive read is that the Terraform source is wrong. That skips the
  verification step that would have redirected the work.
- Trusting last-modified timestamps in the repo: git timestamps reflect commit
  dates, not deployment dates. A stale file can carry a recent commit because
  someone touched it for an unrelated reason.
- Planning without drift detection: `terraform plan` was never run before the
  conversion started, so the drift stayed invisible.

# Solution

Compare the live artifact against source FIRST, before assuming source is the
cause:

```bash
# Fetch the live definition
aws cloudwatch get-dashboard --dashboard-name <name> --region <region> > live.json

# Normalize both sides and diff
jq -S .DashboardBody live.json > live-sorted.json
jq -S . path/to/source-dashboard.json > source-sorted.json
diff -u source-sorted.json live-sorted.json
```

If live is correct and source is stale, the fix is to codify the live state into
source (drift reconciliation) — not to "fix" source and revert live.

# Why

Dashboards, alarms, and many other resources can be edited directly in a cloud
console. When a live fix bypasses the IaC, the source becomes stale. A plan
would surface the drift as in-place updates on resources you never touched, but
only if you run it before editing. Comparing live against source first redirects
the work in minutes instead of discovering the truth at apply time.
