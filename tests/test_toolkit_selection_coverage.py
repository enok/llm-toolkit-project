from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
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


@unittest.skipUnless(shutil.which("git") and shutil.which("bash"), "needs git and bash")
class FreshCloneSyncTest(unittest.TestCase):
    """The first sync in a fresh copy of the repository changes no tracked file."""

    def test_first_sync_leaves_tracked_files_unchanged(self) -> None:
        listed = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            stdout=subprocess.PIPE, check=True,
        ).stdout.decode("utf-8").split("\0")
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "toolkit"
            for rel in filter(None, listed):
                src = ROOT / rel
                if src.is_symlink() or not src.is_file():
                    continue
                dst = repo / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@example.invalid",
                       GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@example.invalid")
            for args in (["init", "-q"], ["add", "-A"], ["commit", "-q", "-m", "snapshot"]):
                subprocess.run(["git", "-c", "commit.gpgsign=false", "-C", str(repo), *args], check=True, env=env,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            result = subprocess.run(
                ["bash", str(repo / "scripts" / "sync-tool-configs.sh"), str(repo),
                 "--skip-agents-md", "--skip-github"],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env,
            )
            self.assertEqual(result.returncode, 0, result.stdout.decode("utf-8", "replace")[-2000:])
            status = subprocess.run(
                ["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=no"],
                stdout=subprocess.PIPE, check=True,
            ).stdout.decode("utf-8")
            self.assertEqual(status, "", "the first sync changed tracked files:\n" + status)


if __name__ == "__main__":
    unittest.main()
