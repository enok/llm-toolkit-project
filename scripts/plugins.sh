#!/bin/sh
# Thin wrapper: all logic lives in plugins.py (cross-platform).
here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$here/plugins.py" "$@"
fi
exec python "$here/plugins.py" "$@"
