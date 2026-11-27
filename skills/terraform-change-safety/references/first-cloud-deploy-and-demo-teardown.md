# First Cloud Deploy and Demo Teardown

Cloud control planes are eventually consistent and bill by reserved capacity, so propagation delay, sidecar sums and idle polling explain most first-run surprises.

## First-deploy gotchas

- A just-enabled API, or a freshly granted log-writer role, can answer `PERMISSION_DENIED` for seconds to minutes. Do not treat it as a real denial: retry after about 45 seconds. The missing role can also hide the first run's step logs.
- A closed billing account blocks everything billable. Ask the owner and leave the billing tab open.
- The platform front end can answer reserved health paths (names ending in "z") with 404 from outside while in-instance probes pass. Do not smoke-test a reserved health path from outside; smoke-test a normal path.
- A scale-to-zero service stays up while a browser tab keeps polling it. Poll only while the page is visible.
- Multi-container billing reserves the sum of all containers' vCPU and memory, so do not estimate cost from one container. Compute the hourly cost first, keep max instances at 1 for a demo, and say "check the pricing page on the day".
- Parallel image builds sharing a cache collide.
- When a user-only step blocks (sign-in, billing), state it once and re-check state on resume; do not re-ask for the same step. A repeated user instruction authorizes the actions the plan already lists.

## Teardown plan (before the first apply)

- Delete the billed service; keep registry images and a one-command redeploy.
- Confirm the old URL returns 404.
- Re-inspect live state after days of pause, and verify nothing billable remains.
