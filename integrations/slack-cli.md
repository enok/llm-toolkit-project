# Slack CLI

Use the official [Slack CLI](https://github.com/slackapi/slack-cli) to create,
develop, validate, and deploy Slack applications from an LLM-assisted terminal.
The upstream project is maintained by Slack and licensed under Apache-2.0.

The Slack CLI is not a general replacement for the Slack Web API or connector
tools. Installing it does not authorize an LLM to post messages, and this
toolkit never automates `slack login`, reads Slack credential files, or accepts
tokens on the command line.

## Secure installation

Official documentation shows a pipe-to-shell installer. Do not use that path
from an agent session: it executes remotely mutable content before local
review. Install from a pinned release asset with a verified digest instead.

1. Choose an exact release tag (do not track `latest`) and record it.
2. Take the SHA-256 digest published by the project for that platform's asset.
3. Download the asset, verify size and digest **before** extracting, and refuse
   to overwrite an existing `slack` executable.

```bash
SLACK_CLI_VERSION="<pinned-version>"
SLACK_CLI_SHA256="<published-digest>"
ASSET="slack_cli_${SLACK_CLI_VERSION}_linux_64-bit.tar.gz"

curl -fsSL --proto '=https' --tlsv1.2 \
  -o "$ASSET" \
  "https://downloads.slack-edge.com/slack-cli/${ASSET}"

echo "${SLACK_CLI_SHA256}  ${ASSET}" | sha256sum --check --status \
  || { echo "digest mismatch — do not extract"; exit 1; }

tar -xzf "$ASSET" -C "$HOME/.local/opt/"   # target must not already hold a slack binary
```

```powershell
$version = '<pinned-version>'
$sha256  = '<published-digest>'
$asset   = "slack_cli_${version}_windows_64-bit.zip"

Invoke-WebRequest -Uri "https://downloads.slack-edge.com/slack-cli/$asset" -OutFile $asset
if ((Get-FileHash $asset -Algorithm SHA256).Hash -ne $sha256) {
  throw 'digest mismatch — do not extract'
}
Expand-Archive -Path $asset -DestinationPath "$env:LOCALAPPDATA\Programs\slack-cli"
```

Supported targets are Linux x86-64/ARM64, macOS x86-64/ARM64, and Windows
x86-64. Accept release-asset redirects only to the project's own release host,
validate the archive's exact published size and digest before extraction,
publish the binary without overwriting a raced destination, and reject archive
path traversal.

Verify the result before use:

```bash
slack version
```

## Authentication

After installation, authenticate interactively when required:

```text
slack login
```

Do not place Slack tokens in repository files, task prompts, command arguments,
or generated toolchain manifests. External Slack writes still require this
toolkit's authorization and human-facing approval gates — see
`rules/external-write-authorization.md` and
`rules/human-comment-reply-gate.md`.

## New LLM client bootstrap

`INFRA.sh` and `INFRA.ps1` at the repository root combine the full
developer-tool profile, the supported LLM agent CLIs, and optional consumer
linking. Both entrypoints are plan-only by default and require an explicit
`--apply` or `-Apply` before installing anything. Add the pinned Slack CLI step
to that bootstrap only when Slack app development is actually in scope for the
machine.
