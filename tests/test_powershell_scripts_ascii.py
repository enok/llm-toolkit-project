"""PowerShell sources must be ASCII-only or start with a UTF-8 BOM.

Windows PowerShell 5.1 reads a BOM-less file in the ANSI code page. The bytes of
an em dash, an en dash, a box-drawing line or an arrow then decode to a typographic
quote, which PowerShell accepts as a quote character, so a string literal ends
early and the script does not parse.
"""
from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = ("*.ps1", "*.psm1", "*.psd1")
BOM = b"\xef\xbb\xbf"


def tracked_powershell_files() -> list[Path]:
    try:
        out = subprocess.run(
            ["git", "ls-files", *PATTERNS], cwd=ROOT, capture_output=True, text=True, check=True
        ).stdout
        files = [ROOT / line for line in out.splitlines() if line]
        if files:
            return files
    except (OSError, subprocess.CalledProcessError):
        pass
    skip = {".git", "node_modules"}
    return [p for pat in PATTERNS for p in ROOT.rglob(pat) if not skip & set(p.parts)]


class PowerShellScriptsAsciiTest(unittest.TestCase):
    def test_non_ascii_powershell_files_carry_a_bom(self) -> None:
        offenders = []
        for path in tracked_powershell_files():
            data = path.read_bytes()
            if data.startswith(BOM):
                continue
            for number, line in enumerate(data.splitlines(), start=1):
                if any(byte > 127 for byte in line):
                    offenders.append(f"{path.relative_to(ROOT).as_posix()}:{number}")
                    break
        self.assertEqual([], offenders, "non-ASCII PowerShell source without a BOM")

    def test_some_powershell_files_are_checked(self) -> None:
        self.assertTrue(tracked_powershell_files())


if __name__ == "__main__":
    unittest.main()
