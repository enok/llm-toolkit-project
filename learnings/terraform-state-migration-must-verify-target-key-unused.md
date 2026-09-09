---
title: Before migrating Terraform state, verify the target bucket+key are unused
category: deployment
created: 2026-08-26
tags: [terraform, state, migration, s3, backend, collision, key-squatting]
---

# Problem

A proposed Terraform state migration would have written to an S3 key that
a separate restructuring root also intended to use. If executed, two
roots would write to the same state object, orphaning resources managed
by whichever root lost the race.

# Failed Approaches

- Assuming bucket namespacing is enough: state buckets can hold many
  roots' state files. The bucket name alone doesn't prevent key
  collisions.
- Trusting naming conventions: even if keys follow a pattern
  (`<app>/<service>.tfstate`), multiple roots can target the same pattern
  if they manage the same service.
- Checking only whether the key exists now: a key might not exist yet but
  be claimed in another root's pending migration or an unmerged branch.

# Solution

Before migrating state, check whether the target bucket+key are claimed:

```bash
# 1. Check if the key already exists in the backend
aws s3api head-object --bucket <bucket> --key <key> 2>&1

# 2. Grep all Terraform roots for the same bucket+key combination
rg "bucket.*=.*<bucket>" --type tf -A 5 | rg "key.*=.*<key>"

# 3. Check open PRs for the same backend configuration
gh pr list --json number,headRefName --jq '.[].number' |
  xargs -I {} gh pr view {} --json files \
    --jq '.files[].path' | xargs rg "key.*=.*<key>"

# 4. If any hits: import the existing state into your root, or change
#    your key to avoid the collision.
```

Document the collision (if any) in the migration runbook so others don't
repeat the same near-miss.

# Why

S3-backed state is a shared namespace; multiple roots can target the same
bucket+key. Terraform has no locking or conflict detection at the
key-selection level (only at the lock level during operations). If two
roots write to the same key, the last write wins and the first root's
resources become orphaned. Migrations are the riskiest time for
collisions because they bypass the normal resource-already-managed
checks.
