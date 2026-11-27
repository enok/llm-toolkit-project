#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Pick the first python that actually runs. Skip the Windows Store stub under
# WindowsApps: it is found on PATH but does not run scripts.
find_python_cmd() {
  local candidate found
  for candidate in python3 python python.exe py; do
    found="$(command -v "$candidate" 2>/dev/null || true)"
    [ -n "$found" ] || continue
    case "$found" in
      */WindowsApps/*|*\\WindowsApps\\*) continue ;;
    esac
    if [ "$candidate" = "py" ]; then
      if py -3 -c 'import sys' >/dev/null 2>&1; then
        printf '%s\n' "py -3"
        return 0
      fi
    elif "$candidate" -c 'import sys' >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

if python_cmd_text="$(find_python_cmd)"; then
  read -r -a python_cmd <<< "$python_cmd_text"
  exec "${python_cmd[@]}" scripts/validate-skills-with-skillspector.py "$@"
fi

echo "FAIL: python is required to run SkillSpector validation." >&2
exit 127
