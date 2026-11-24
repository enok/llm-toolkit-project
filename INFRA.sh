#!/usr/bin/env bash
# Plan-first entry point for the complete toolkit CLI set on Linux, macOS, or
# Windows Git Bash. The default is a read-only plan; pass --apply only after
# reviewing the printed package plan.
#
# Usage: ./INFRA.sh [--apply] [--consumer <path>] [--no-kb] [--kb-data-dir <path>]
#   --apply             Actually install/link (default: dry-run plan only)
#   --consumer <path>   Also link a consumer repo to this toolkit after install
#   --no-kb             Skip the knowledge-base step
#   --kb-data-dir <p>   Knowledge-base data folder
#
# This wraps scripts/bootstrap-dev.sh with a full-profile, all-agent plan.
# Windows (PowerShell): INFRA.ps1 - same behavior via scripts/bootstrap-dev.ps1.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APPLY=0
CONSUMER=""
NO_KB=0
KB_DATA_DIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --consumer) CONSUMER="${2:-}"; [[ -n "$CONSUMER" ]] || { echo "--consumer requires a path" >&2; exit 2; }; shift 2 ;;
    --no-kb) NO_KB=1; shift ;;
    --kb-data-dir) KB_DATA_DIR="${2:-}"; [[ -n "$KB_DATA_DIR" ]] || { echo "--kb-data-dir requires a path" >&2; exit 2; }; shift 2 ;;
    -h|--help) sed -n '2,12p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
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
if [[ "$NO_KB" -eq 1 ]]; then
  BOOTSTRAP_ARGS+=(--no-kb)
fi
if [[ -n "$KB_DATA_DIR" ]]; then
  BOOTSTRAP_ARGS+=(--kb-data-dir "$KB_DATA_DIR")
fi

exec "$ROOT/scripts/bootstrap-dev.sh" "${BOOTSTRAP_ARGS[@]}"
