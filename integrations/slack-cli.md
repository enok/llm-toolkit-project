# Slack CLI

Install the official [Slack CLI](https://github.com/slackapi/slack-cli) from a pinned release
asset, not the pipe-to-shell installer.

## Secure installation

- Pin an exact release tag; never `latest` (it changes under you and cannot be re-verified).
- Verify the published SHA-256 before extracting.
- Refuse to overwrite an existing `slack` executable: stop and ask the user (it may be another
  tool or a version they rely on).

```bash
{ command -v slack || [ -e "$HOME/.local/bin/slack" ]; } && { echo "slack already installed; not overwriting"; exit 1; }
SLACK_CLI_VERSION="<pinned-version>"; SLACK_CLI_SHA256="<published-digest>"
ASSET="slack_cli_${SLACK_CLI_VERSION}_linux_64-bit.tar.gz"
curl -fsSL --proto '=https' -o "$ASSET" "https://downloads.slack-edge.com/slack-cli/${ASSET}"
echo "${SLACK_CLI_SHA256}  ${ASSET}" | sha256sum --check --status || exit 1
mkdir -p "$HOME/.local/opt/slack-cli" && tar -xzf "$ASSET" -C "$HOME/.local/opt/slack-cli"
```

Never automate `slack login` or pass tokens on the command line.
