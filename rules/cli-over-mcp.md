---
trigger: always_on
description: Prefer capable authenticated CLIs for external systems while preserving explicit user-selected apps and MCP-only capabilities
---

# CLI over MCP

For an external system reachable through both a CLI and an MCP server, prefer a capable, authenticated CLI when it preserves the required semantics and evidence. Use the MCP surface when the user explicitly selects that app/tool, a provider-specific instruction requires it, the CLI is unavailable or lacks the operation, or the MCP integration provides a required capability the CLI cannot reproduce safely. More-specific repository or provider instructions take precedence over this general default.

## Rule

- Check CLI availability, authentication, and operation coverage before choosing the integration path.
- Do not override an explicit user request to use an installed app, connector, or MCP tool unless it cannot complete the operation safely; report the limitation instead.
- Prefer file-backed CLI or REST payloads for large writes so content is not embedded in generated command text.
- If a provider supports disabling individual integrations, disable or re-enable an MCP server only when the user or repository configuration authorizes that specific configuration change.
- Integration choice does not authorize an external read or write; apply the same operation-specific authorization gates whichever transport is selected.
- Record the concrete capability or safety reason whenever MCP is selected over an available CLI.

## Why

- CLI invocations can pass data disk-to-disk or via direct process I/O. In environments where large generated tool-call payloads have failed readback validation, a file-backed CLI or REST request reduces that transport risk; treat this as an environment-specific failure mode, not a universal MCP size limit.
- Redundant integrations increase routing ambiguity, but disabling user configuration is itself a state change and requires authority.

## How to apply

- Before choosing an integration for systems such as Confluence, Jira, GitHub, Slack, or AWS, check whether a CLI (`acli`, `gh`, `aws`, or a vendor CLI) covers the needed operation in this environment.
- When the CLI covers the operation, route large reads and writes through files where supported and verify the service readback. Put sensitive temporary payloads outside repositories with restrictive permissions, never persist credentials or tokens in them, redact diagnostics, and remove temporary payloads in a guaranteed cleanup path whether the operation succeeds, fails, or is interrupted. Retain only explicitly approved, non-sensitive diagnostics.
- Document the specific capability gap (with version checked and source doc referenced) whenever an MCP tool is used instead of the CLI, so the exception is traceable and not treated as a silent default.
