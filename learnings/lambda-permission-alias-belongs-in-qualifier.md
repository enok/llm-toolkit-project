---
title: "aws_lambda_permission: the alias goes in qualifier, never name:alias in function_name"
category: deployment
created: 2026-08-19
tags: [terraform, lambda, permission, alias, qualifier, api-gateway, perpetual-diff]
---

# Problem

Granting API Gateway invoke on a Lambda alias by setting
`function_name = "my-function:stage"` in `aws_lambda_permission`. The apply
succeeded and the integration worked, but every subsequent plan wanted to
replace the permission - a perpetual replacement that never converged to a
clean no-op plan.

# Failed Approaches

- Embedding the alias in the function name string (`name:alias`): accepted
  by the API, never matches what Terraform reads back, so the diff is
  eternal.
- Re-applying to "settle" the diff: the replacement recreates the same
  mismatch every time.

# Solution

```hcl
resource "aws_lambda_permission" "apigw" {
  function_name = var.lambda_function_name  # bare name only
  qualifier     = var.lambda_alias          # alias goes here
  ...
}
```

Bare name in `function_name`, alias in the dedicated `qualifier` argument.
Converges to a clean no-op plan immediately.

# Why

The provider normalizes `function_name` to the function ARN and sends the
alias as a separate API field. A `name:alias` string is resolved on write
but read back in normalized form, so state never equals config and
Terraform plans a replacement forever.
