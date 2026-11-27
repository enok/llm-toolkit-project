---
title: First cloud deployment gotchas and planning the teardown of a demo
category: deployment
created: 2026-11-26
tags: [cloud-deploy, scale-to-zero, billing, permission-propagation, health-path, teardown, cost, demo]
---

# Problem
A first deployment of a demo service hit a series of avoidable surprises, and the demo was
left running after the work ended.

# Failed Approaches
- Treating PERMISSION_DENIED right after enabling an API as a real denial.
- Smoke-testing a reserved health path from outside.
- Assuming a scale-to-zero service sleeps while a browser tab keeps polling it.
- Estimating cost from one container when the instance bills the sum of all of them.
- Re-asking the user for the same sign-in or billing step.

# Solution
- A just-enabled API, or a freshly granted log-writer role, can answer PERMISSION_DENIED for
  seconds to minutes. Retry after about 45 seconds; the missing role can also hide the first
  run's step logs.
- A closed billing account blocks everything billable. Ask the owner and leave the billing tab
  open.
- The platform front end can answer reserved health paths (names ending in "z") with 404 from
  outside while in-instance probes pass. Smoke-test a normal path.
- A scale-to-zero service stays up while a tab polls it; poll only while the page is visible.
- Multi-container billing reserves the sum of containers' vCPU and memory. Compute the hourly
  cost first, keep max instances at 1 for a demo, and say "check the pricing page on the day".
- Parallel image builds sharing a cache collide.
- When a user-only step blocks (sign-in, billing), state it once and re-check state on resume;
  a repeated user instruction authorizes the actions the plan already lists.
- Plan teardown up front: delete the billed service, keep registry images and a one-command
  redeploy, confirm the old URL returns 404, and re-inspect live state after days of pause.
- See also `skills/terraform-change-safety/SKILL.md`.

# Why
Cloud control planes are eventually consistent and bill by reserved capacity, so propagation delay,
sidecar sums and idle polling explain most first-run surprises.
