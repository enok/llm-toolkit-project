---
title: Lambda console Triggers tab cannot represent alias-scoped API Gateway permissions
category: architecture
created: 2026-08-19
tags: [lambda, api-gateway, alias, console, triggers, permission, anti-pattern]
---

# Problem

An API Gateway REST API integrated with a Lambda **alias** (qualified invoke
permission on the alias) shows nothing on the Lambda console's function-level
Triggers tab, which reads only the unqualified function policy. Readers conclude
the trigger is missing and the integration is broken.

# Failed Approaches

- Adding an unqualified twin permission (same principal and source ARN, on the
  function itself, e.g. `AllowExecutionFromApiGatewayConsoleView`) purely for
  console visibility: the trigger row does appear, but the console cross-checks
  the statement against the API definition and the integration URI — which
  targets the alias — and permanently flags it: "API ... doesn't include a
  resource with path /<path> ... on the POST method". It looks broken forever
  and had to be reverted.

# Solution

Do not add a twin permission. Alias-scoped trigger visibility lives at
**Lambda console > Aliases > `<alias>` > Configuration > Permissions** —
document that location instead of the Triggers tab.

Verify the wiring functionally (test-invoke through the API) rather than by
reading the function-level Triggers tab. Note that SigV4 callers of an
`AWS_IAM`-authorized API additionally need an `execute-api:Invoke` identity
policy; a 403 there is caller-side, not integration-side.

# Why

The function-level Triggers tab is rendered from the unqualified function
resource policy and validated against the integration target. An alias-fronted
integration can never validate there: by design, the policy statement and the
integration URI reference different qualified ARNs.
