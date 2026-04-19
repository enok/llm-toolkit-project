#!/usr/bin/env bash
# Ensure symlinks to toolkit are correct (repair if needed).
# Usage: ./scripts/ensure-symlinks.sh [consumer-path] [--force] [--pull]
#
# Options:
#   --force  Replace blocking paths (wrong symlinks or copied folders)
#   --pull   Run git pull in toolkit before checking

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOLKIT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
FORCE=""
PULL=""

source "$SCRIPT_DIR/lib.sh"

POSITIONAL=()
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --pull) PULL=1 ;;
    *) POSITIONAL+=("$arg") ;;
  esac
done

CONSUMER="${POSITIONAL[0]:-.}"
CONSUMER="$(resolve_absolute_path "$CONSUMER")"

# Optional: pull latest toolkit first
if [[ -n "$PULL" && -d "$TOOLKIT_ROOT/.git" ]]; then
  echo "Pulling latest toolkit changes..."
  (cd "$TOOLKIT_ROOT" && git pull) || echo "Warning: git pull failed, continuing..."
fi

echo "Ensuring symlinks for: $CONSUMER"
echo "Toolkit root: $TOOLKIT_ROOT"
echo ""

# Ensure toolkit layouts first
ensure_toolkit_windsurf_layout "$TOOLKIT_ROOT" "$FORCE" || exit 1
ensure_toolkit_setup_layout "$TOOLKIT_ROOT" "$FORCE" || exit 1

# Define links to verify/create
declare -a LINKS=(
  ".agents:$TOOLKIT_ROOT/.agents"
  ".windsurf:$TOOLKIT_ROOT/.windsurf"
  ".setup:$TOOLKIT_ROOT/.setup"
)

[[ -d "$TOOLKIT_ROOT/.cursor" ]] && LINKS+=(".cursor:$TOOLKIT_ROOT/.cursor")
[[ -d "$TOOLKIT_ROOT/.claude" ]] && LINKS+=(".claude:$TOOLKIT_ROOT/.claude")
[[ -d "$TOOLKIT_ROOT/.codex" ]] && LINKS+=(".codex:$TOOLKIT_ROOT/.codex")

ERRORS=0
for entry in "${LINKS[@]}"; do
  IFS=':' read -r link_name target <<< "$entry"
  link_path="$CONSUMER/$link_name"

  if [[ ! -e "$target" ]]; then
    echo "Skipping $link_name: target not found ($target)"
    continue
  fi

  if ensure_dir_link "$link_path" "$target" "$FORCE"; then
    echo "  OK: $link_name"
  else
    echo "  FAIL: $link_name"
    ((ERRORS++)) || true
  fi
done

echo ""
if [[ $ERRORS -eq 0 ]]; then
  echo "Done. All symlinks are correct."
else
  echo "Warning: $ERRORS symlink(s) could not be verified/created."
  echo "Run with --force to replace blocking paths."
  exit 1
fi
