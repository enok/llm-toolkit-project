#!/usr/bin/env bash
# Create an isolated environment for scripts/convert_to_markdown.py and install the pinned
# libraries from requirements.txt. Works in bash on Linux, macOS and Git Bash on Windows.
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
venv="${DOCS_VENV:-.venv-docs}"

python_bin="$(command -v python3 || command -v python || true)"
[[ -n "$python_bin" ]] || { echo "python3 not found" >&2; exit 1; }
"$python_bin" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' \
  || { echo "Python 3.11 or newer is required (pinned Pillow 13.0.0); found $("$python_bin" -V 2>&1)" >&2; exit 1; }

[[ -d "$venv" ]] || "$python_bin" -m venv "$venv"
if [[ -x "$venv/bin/python" ]]; then
  venv_python="$venv/bin/python"          # Linux, macOS
else
  venv_python="$venv/Scripts/python.exe"  # Windows (Git Bash)
fi

"$venv_python" -m pip install --require-virtualenv -r "$here/requirements.txt"

echo "Done. Run: $venv_python $here/convert_to_markdown.py <file> [out.md]"
