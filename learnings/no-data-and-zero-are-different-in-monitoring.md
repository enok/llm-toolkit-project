---
title: "\"No data\" and \"zero\" are different, and conflating them silently breaks monitoring"
category: monitoring
created: 2026-08-26
tags: [cloudwatch, metrics, zero, no-data, fill, treat-missing-data, alarms]
---

# Solution
Counts/rates may be zero-filled with `notBreaching` alarms; latencies may not:
- Latency widgets (p99 and other percentiles): no `FILL(m1, 0)`, leave gaps unfilled.
  Why: a filled gap asserts 0 ms and drags the percentile down.
- Latency alarms: `treat_missing_data` = `"missing"`, `"ignore"` or `"breaching"` (breaching when
  traffic is always expected), never `"notBreaching"`.
  Why: `notBreaching` scores an empty bucket as healthy, the same false 0 ms claim.

# Why
CloudWatch keeps "value 0" and "no datapoint" distinct; only counts have a true zero.
