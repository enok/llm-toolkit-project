---
title: Terraform fails AWS SSO token refresh while the AWS CLI works
category: toolchain
created: 2026-08-19
tags: [terraform, aws-sso, credentials, s3-backend, export-credentials, InvalidGrantException]
---

# Problem

`aws sts get-caller-identity` succeeded, but `terraform plan` against an
S3 backend failed with "No valid credential sources found ... unable to
refresh SSO token ... InvalidGrantException", even though the backend
pinned no profile and both used the same default credential chain.

# Failed Approaches

- Assuming the backend pinned a different (expired) profile - it declared
  none; both paths used the default chain.
- Re-running the same command hoping the CLI's earlier success had
  refreshed the shared SSO cache - the Go SDK inside Terraform still
  failed the CreateToken refresh the CLI handles fine.
- Considering `aws sso login` - interactive/browser-bound, unusable from
  an unattended agent session.

# Solution

Export the CLI's working session credentials into environment variables
and run Terraform in that environment:

```bash
eval "$(aws configure export-credentials --format env)"
terraform plan ...
```

Env vars (`AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`/`AWS_SESSION_TOKEN`)
take precedence in both the provider and the S3 backend. Since shell state
does not persist across agent tool calls, put the `eval` and the
terraform command in the same shell invocation. The same fix applies to
boto3 scripts.

# Why

The AWS CLI and the AWS SDK for Go (used by Terraform) implement SSO
token refresh differently; certain cached-session states are refreshable
by the CLI but rejected by the SDK (`InvalidGrantException`).
`export-credentials` sidesteps refresh entirely by handing over the
already-valid session keys.
