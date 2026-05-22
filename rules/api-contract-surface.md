---
trigger: always_on
description: Contract changes must identify downstream consumers, gateways, and generated artifacts
---

# API contract surface

When an API or public contract changes:

1. Identify the source-of-truth contract file or schema.
2. Call out whether the change is additive, behavioral, or breaking.
3. List downstream repos, generated clients, gateways, and docs that must stay in sync.
4. Do not treat a contract edit as complete until downstream impact is acknowledged or explicitly deferred with a tracked follow-up.
