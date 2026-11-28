from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT / "docs" / "llm" / "toolkit-selection.txt"
BEGIN = "# BEGIN TOOLKIT SELECTION FILTERS"
END = "# END TOOLKIT SELECTION FILTERS"


def listed_paths() -> set[str]:
    paths = set()
    for line in SELECTION.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith(("rules/", "workflows/")):
            paths.add(line)
    return paths


def selection_block(name: str) -> str:
    text = (ROOT / name).read_text(encoding="utf-8")
    match = re.search(re.escape(BEGIN) + r".*?" + re.escape(END), text, re.S)
    assert match, f"{name} has no selection block"
    return match.group(0)


class ToolkitSelectionCoverageTest(unittest.TestCase):
    def test_every_rule_and_workflow_is_listed(self) -> None:
        listed = listed_paths()
        existing = {
            f"{d}/{p.name}"
            for d in ("rules", "workflows")
            for p in (ROOT / d).glob("*.md")
            if p.name != "README.md"
        }
        self.assertEqual(sorted(existing - listed), [])

    def test_every_listed_path_exists(self) -> None:
        missing = [p for p in sorted(listed_paths()) if not (ROOT / p).is_file()]
        self.assertEqual(missing, [])

    def test_committed_ignore_blocks_are_consistent(self) -> None:
        cursorignore = selection_block(".cursorignore")
        indexing = selection_block(".cursorindexingignore")
        self.assertEqual(cursorignore, indexing)
        self.assertNotIn(".cursor/workflows/", cursorignore)


if __name__ == "__main__":
    unittest.main()
