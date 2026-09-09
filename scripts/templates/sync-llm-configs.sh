#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SYNC_ARGS=()
for arg in "$@"; do
  case "$arg" in
    --force) SYNC_ARGS+=("--force") ;;
    --skip-cursor-rules) SYNC_ARGS+=("--skip-cursor-rules") ;;
    *) echo "Usage: $0 [--force] [--skip-cursor-rules]" >&2; exit 2 ;;
  esac
done

PYTHON_BIN=""
if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "Error: Python is required to resolve the toolkit root from shared toolkit links." >&2
  exit 1
fi

TOOLKIT_ROOT="$("$PYTHON_BIN" - "$REPO_ROOT" <<'PY'
from pathlib import Path
import sys

repo = Path(sys.argv[1])

def valid(root: Path) -> bool:
    return (root / "scripts" / "sync-tool-configs.sh").exists()

def emit(root: Path) -> None:
    root = root.resolve()
    if valid(root):
        print(root)
        raise SystemExit(0)

agents = repo / ".agents"
if agents.exists():
    resolved_agents = agents.resolve()
    emit(resolved_agents.parent)

for skills_root in (
    repo / ".agents" / "skills",
    repo / ".agent" / "skills",
    repo / ".claude" / "skills",
    repo / ".codex" / "skills",
    repo / ".cursor" / "skills",
    repo / ".gemini" / "skills",
    repo / ".opencode" / "skills",
    repo / ".windsurf" / "skills",
):
    if skills_root.exists():
        resolved_skills = skills_root.resolve()
        emit(resolved_skills.parent)
        for child in sorted(skills_root.iterdir()):
            if child.exists():
                resolved_child = child.resolve()
                emit(resolved_child.parent.parent)

raise SystemExit(
    "Could not resolve toolkit root from linked shared skill paths. "
    "Re-run toolkit setup or ensure-symlinks first."
)
PY
)"

exec bash "$TOOLKIT_ROOT/scripts/sync-tool-configs.sh" "$REPO_ROOT" "${SYNC_ARGS[@]}"
