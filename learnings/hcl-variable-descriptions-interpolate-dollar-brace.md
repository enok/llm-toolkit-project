---
title: HCL variable descriptions interpolate ${...} — use angle-bracket placeholders
category: toolchain
created: 2026-08-19
tags: [terraform, hcl, variables, description, interpolation, template-syntax]
---

# Problem

Writing a naming convention literally in a variable description —
`description = "default composes ${org}-lambda-${environment}-${purpose}"` —
made Terraform treat `${org}` as template syntax. It either errors (no such
symbol in that scope) or interpolates something unintended, instead of showing
the placeholder text the description was meant to convey.

# Failed Approaches

- Assuming `description` is inert documentation text: it is an ordinary quoted
  HCL string expression, parsed like any other string in the file.

# Solution

Write placeholders in angle brackets inside descriptions and docs:

```hcl
variable "lambda_name" {
  type        = string
  description = "default composes <org>-lambda-<environment>-<purpose>"
}
```

Escaping as `$${org}` also works, but the angle-bracket convention reads more
cleanly and stays consistent across shared modules and their READMEs.

# Why

Every quoted string in HCL supports template interpolation; there is no "plain
text" string context. `${` always starts an expression unless it is escaped as
`$${`, so any documentation that quotes a naming template must avoid the
sequence entirely.
