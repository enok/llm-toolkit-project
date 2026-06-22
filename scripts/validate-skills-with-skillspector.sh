#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if command -v python >/dev/null 2>&1; then
  exec python scripts/validate-skills-with-skillspector.py "$@"
fi

if command -v python3 >/dev/null 2>&1; then
  exec python3 scripts/validate-skills-with-skillspector.py "$@"
fi

echo "FAIL: python is required to run SkillSpector validation." >&2
exit 127
