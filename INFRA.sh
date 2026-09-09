#!/usr/bin/env bash
# Plan-first entry point for the complete toolkit CLI set on Linux, macOS, or
# Windows Git Bash. The default is a read-only plan; pass --apply only after
# reviewing the printed package plan.
#
# Usage: ./INFRA.sh [--apply] [--consumer <path>]
#   --apply             Actually install/link (default: dry-run plan only)
#   --consumer <path>   Also link a consumer repo to this toolkit after install
#
# This wraps scripts/bootstrap-dev.sh with a full-profile, all-agent plan.
# Windows (PowerShell): INFRA.ps1 - same behavior via scripts/bootstrap-dev.ps1.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLY=0
CONSUMER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --consumer) CONSUMER="${2:-}"; [[ -n "$CONSUMER" ]] || { echo "--consumer requires a path" >&2; exit 2; }; shift 2 ;;
    -h|--help) sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

BOOTSTRAP_ARGS=(--full --agent all)
if [[ "$APPLY" -eq 0 ]]; then
  BOOTSTRAP_ARGS+=(--dry-run)
fi
if [[ -n "$CONSUMER" ]]; then
  BOOTSTRAP_ARGS+=(--consumer "$CONSUMER")
fi

exec "$ROOT/scripts/bootstrap-dev.sh" "${BOOTSTRAP_ARGS[@]}"
