#!/usr/bin/env python3
"""Compatibility entrypoint for the SkillSpector skill scan.

`security-check-toolkit.sh` and `validate-specialist-agent.js` call this script
with `--changed` (new or modified skills only) or `--all` (every skill). Both
modes delegate to `scripts/validate-skills-with-skillspector.py`, which owns the
scanner invocation, the reviewed-findings allowlist, and severity thresholds.
"""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


def main() -> int:
    target = Path(__file__).resolve().with_name("validate-skills-with-skillspector.py")
    sys.argv = [str(target), *sys.argv[1:]]
    try:
        runpy.run_path(str(target), run_name="__main__")
    except SystemExit as exc:  # propagate the delegated exit code
        code = exc.code
        return int(code) if isinstance(code, int) else (0 if code is None else 1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
