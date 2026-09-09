---
title: Terraform allowed_account_ids is a provider argument and invalid in backend blocks
category: deployment
created: 2026-08-26
tags: [terraform, backend, s3, provider, allowed-account-ids, init]
---

# Problem

A drafted Terraform backend migration included `allowed_account_ids`
inside the S3 backend block. `terraform init` failed with "Unsupported
argument: An argument named 'allowed_account_ids' is not expected here."

# Failed Approaches

- Assuming it's a backend safety feature: the backend block has no concept
  of account pinning; it only configures where state is stored.
- Copying from working examples: the working examples had
  `allowed_account_ids` in the provider block, not the backend block.

# Solution

Place `allowed_account_ids` in the provider configuration, not the backend:

```hcl
# CORRECT
terraform {
  backend "s3" {
    bucket  = "example-terraform-state-bucket"
    key     = "app/service.tfstate"
    region  = "us-west-2"
    encrypt = true
  }
}

provider "aws" {
  region              = "us-west-2"
  allowed_account_ids = ["123456789012"]
}

# INCORRECT - fails at init
terraform {
  backend "s3" {
    bucket              = "example-terraform-state-bucket"
    key                 = "app/service.tfstate"
    region              = "us-west-2"
    encrypt             = true
    allowed_account_ids = ["123456789012"]  # ERROR: not a backend argument
  }
}
```

# Why

The backend block configures the state storage backend; it accepts only
backend-specific arguments (bucket, key, region, encrypt, etc.).
`allowed_account_ids` is an AWS provider argument that pins which account
the provider is allowed to operate against. Placing it in the backend
block causes `terraform init` to fail before the provider is even
configured.
