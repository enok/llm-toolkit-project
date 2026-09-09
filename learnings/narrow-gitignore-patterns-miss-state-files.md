---
title: Narrow gitignore patterns miss real Terraform state files
category: security
created: 2026-08-26
tags: [gitignore, terraform, state, secrets, aws-account, patterns]
---

# Problem

`.gitignore` patterns `**/terraform.tfstate` and `**/terraform.tfstate.backup`
did not match `backup_version.tfstate` or `last_valid_version.tfstate`,
leaving roughly 1 MB of state carrying an AWS account ID and resource ARNs
fully stageable. These were state-recovery snapshots created during an
incident.

# Failed Approaches

- Assuming the standard pattern is enough: the canonical state file names
  are covered, but recovery/backup workflows create different names.
- Relying on `git status` to show stageable secrets: by the time secrets
  show in `git status`, they're one `git add` away from history. Prevention
  beats detection.
- Trusting that recovery files are temporary: these files may be the only
  local copies of critical state; deleting them is unsafe until the remote
  backend's versions are verified.

# Solution

Use broader patterns that match all state file variants:

```gitignore
# Terraform state files (broad patterns)
*.tfstate
*.tfstate.*

# Explicit backup patterns (defense in depth)
**/terraform.tfstate.backup
**/backup_*.tfstate
**/last_valid_*.tfstate
**/.terraform/
```

Audit existing untracked state files before deleting anything:

```bash
git ls-files --others --exclude-standard | grep -E '\.tfstate'
aws s3api list-object-versions --bucket <bucket> --prefix <key>
```

Add a pre-commit hook that blocks any staged path matching `\.tfstate`.

# Why

Terraform state files take many names: the canonical `terraform.tfstate`
and `terraform.tfstate.backup`, but also `terraform.tfstate.d/`, backup
snapshots (`backup_*.tfstate`), and recovery files (`last_valid_*.tfstate`).
Narrow patterns give false security; secrets slip through under unexpected
names. The wildcard `*.tfstate*` catches all variants. "Never commit" does
not mean "safe to delete" - recovery files may be the only local copies;
verify remote versions first.
