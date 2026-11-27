---
title: LinkedIn job pages opened by /jobs/view/<id> hang on skeletons; use the search layout with currentJobId
category: toolchain
created: 2026-10-22
tags: [linkedin, jobs, browser, page-text, skeleton, webfetch, robots]
---

# Solution
Open `https://www.linkedin.com/jobs/search/?currentJobId=<id>` as the primary (only) route.
Treat `/jobs/view/<id>/` as known-bad, not a first try or fallback.

# Why
It stays on loading skeletons in automation, costing about 60 s per id for nothing.
