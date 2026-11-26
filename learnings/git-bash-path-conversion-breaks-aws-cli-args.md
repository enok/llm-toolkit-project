---
title: Git Bash path conversion corrupts slash-prefixed AWS CLI arguments
category: environment
created: 2026-08-19
tags: [git-bash, msys, windows, aws-cli, log-group, path-conversion]
---

# Problem

On Windows Git Bash, `aws logs describe-metric-filters --log-group-name
/aws/lambda/<function>` failed with a validation error ("Member must satisfy
regular expression pattern") — the log group name arrived at the API mangled
into a Windows path (for example `C:/Program Files/Git/aws/lambda/...`).

# Failed Approaches

- Quoting the argument: MSYS path conversion happens regardless of quoting.
- Suspecting the log group did not exist: the resource was fine; only the
  argument was corrupted in transit.

# Solution

Disable MSYS path conversion for the command, or for the whole script:

```bash
MSYS_NO_PATHCONV=1 aws logs describe-metric-filters \
  --log-group-name "/aws/lambda/<function>"
```

`export MSYS_NO_PATHCONV=1` at the top of a session covers every subsequent
slash-prefixed argument (log groups, SSM parameter names, ARN-like paths;
`--query` is unaffected). An alternative is to prefix the value with a doubled
slash (`//aws/lambda/...`), but that leading slash leaks into the actual value
on some tools — the environment variable is the reliable form.

A script that sets `MSYS_NO_PATHCONV=1` can in turn break the stock cloud-CLI wrapper under
Git Bash, because the wrapper hands a POSIX path to the bundled Windows Python. Use a small shim
that calls the bundled Python with a Windows path instead of the wrapper.

# Why

MSYS2 (the layer under Git Bash) heuristically rewrites arguments that look like
absolute POSIX paths into Windows paths before the target program sees them.
Cloud resource names that begin with `/` — CloudWatch log groups, SSM parameters
— match that heuristic and are silently rewritten. `MSYS_NO_PATHCONV=1` turns
the rewriting off.
