---
title: A Terraform root that plans to create resources another root owns is targeted-apply-only
category: deployment
created: 2026-08-26
tags: [terraform, targeted-apply, resource-ownership, plan, root, warning]
---

# Problem

A legacy Terraform root's untargeted plan showed "10 resources to add"
for production resources that a restructure root should own. An
untargeted apply would have tried to create duplicate resources (likely
failing with AlreadyExists errors or silently adopting them), creating a
split-brain ownership situation.

# Failed Approaches

- Trusting "0 to destroy" in the plan: the absence of destroys doesn't
  prove the creates are safe. Resources can be imported or managed by
  another root.
- Assuming Terraform will error on conflict: some AWS resources are
  upserts (alarms, dashboards); others allow duplicate creation (log
  groups with different names).
- Planning to "fix it later": once resources are in state, removing them
  requires careful coordination between both roots.

# Solution

Identify roots with conflicting ownership before they diverge:

```bash
# 1. Generate plan detail for both roots
cd legacy-root && terraform plan -out=legacy.plan && terraform show -json legacy.plan > legacy.json
cd ../restructure-root && terraform plan -out=restructure.plan && terraform show -json restructure.plan > restructure.json

# 2. Extract resource addresses from each plan
jq -r '.planned_values.root_module.resources[].address' legacy.json > legacy-resources.txt
jq -r '.planned_values.root_module.resources[].address' restructure.json > restructure-resources.txt

# 3. Find overlaps
comm -12 <(sort legacy-resources.txt) <(sort restructure-resources.txt)

# 4. Document the decision: if the legacy root is being retired, mark it
#    targeted-apply-only and add a README warning; if the restructure
#    root will take over, import resources there and remove them from
#    legacy state.
```

Add a written warning to the targeted-apply-only root's README naming the
safe `-target` addresses and stating that any plan showing new resources
to add belongs to the other root, not this one.

# Why

Terraform roots are independent; one root's plan doesn't see another root's
state. When ownership is split or transitioning, a plan can look valid
(creates, no destroys) while actually conflicting with another root's
resources. Marking a root as targeted-apply-only prevents accidental full
applies during the transition period. The warning must be written and
committed; relying on institutional memory guarantees eventual mistakes.
