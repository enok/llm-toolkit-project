---
title: "\"No data\" and \"zero\" are different, and conflating them silently breaks monitoring"
category: monitoring
created: 2026-08-26
tags: [cloudwatch, metrics, zero, no-data, fill, treat-missing-data, alarms]
---

# Problem

Three instances of conflating "zero" with "no data" broke monitoring:
1. A `FILL(m,0)+TIME_SERIES(0)` hybrid adopted as a zero-line technique
   caused gaps instead of fixing them.
2. Failure-count alarms flipped from `notBreaching` to `missing`, driving
   INSUFFICIENT_DATA noise every idle period.
3. A "no messages published" alarm set to `missing` while watching `<= 0`,
   so it went INSUFFICIENT_DATA during outages.

# Failed Approaches

- Using `FILL(m,0)` plus `TIME_SERIES(0)`: the additive TIME_SERIES
  scaffold was meant to force a baseline but actually caused rendering
  gaps.
- Setting `treat_missing_data = missing` on sparse alarms to stop noise:
  this defeats N/N-consecutive evaluation (missing buckets are skipped, so
  one breaching datapoint pages immediately).
- Treating all metrics the same: applying zero-fill to latency metrics
  falsely asserts 0 ms and drags percentiles down.

# Solution

Distinguish between counts/rates (fill with zero) and latencies (leave
unfilled):

```hcl
# Count/rate metric - dashboard widget
metrics = [[{ "expression": "FILL(m1, 0)", "label": "Count (zero-filled)" }]]
# Count/rate alarm
treat_missing_data = "notBreaching"  # no data = no failures = good

# Latency metric - leave unfilled; a gap honestly means "no requests"
# Latency alarm
treat_missing_data = "breaching"  # no data during expected traffic = problem

# Event-driven "silence detection" alarm
comparison_operator = "LessThanOrEqualToThreshold"
threshold           = 0
treat_missing_data  = "breaching"  # missing data = breaching threshold
```

# Why

CloudWatch distinguishes between a datapoint with value 0 and no datapoint
at all. `FILL(m,0)` creates explicit zero datapoints for missing periods.
`treat_missing_data` controls alarm behavior when buckets are empty. Sparse
metrics emit no datapoints when idle; filling counts/rates shows
activity/silence truthfully, but filling latencies misrepresents idle as
"0 ms latency." Event-driven alarms must use `breaching` on missing data,
or they go INSUFFICIENT_DATA during the very outage they exist to catch.
