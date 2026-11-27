#!/bin/sh
# Thin wrapper: all logic lives in kb.py (cross-platform).
here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$here/kb.py" "$@"
fi
exec python "$here/kb.py" "$@"
