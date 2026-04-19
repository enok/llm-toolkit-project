#!/usr/bin/env bash
# Consumer-local wrapper: refresh shared tool surfaces and local exports.
# Run from the consumer repo root: ./scripts/sync-llm-configs.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONSUMER="$(cd "$SCRIPT_DIR/.." && pwd)"

# Find the toolkit by resolving the .agents symlink
TOOLKIT=""
if [[ -L "$CONSUMER/.agents" ]]; then
    TOOLKIT="$(cd "$CONSUMER/.agents" && pwd -P)"
    TOOLKIT="$(dirname "$TOOLKIT")"
fi

if [[ -z "$TOOLKIT" || ! -f "$TOOLKIT/scripts/sync-tool-configs.sh" ]]; then
    echo "Error: Could not locate toolkit sync-tool-configs.sh. Ensure .agents/ is symlinked to the toolkit." >&2
    exit 1
fi

# Delegate to toolkit sync script
exec bash "$TOOLKIT/scripts/sync-tool-configs.sh" "$CONSUMER" "$@"
