from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ORCHESTRATOR = "tool-subagents/agent-orchestrator.md"
SKIP = shutil.ignore_patterns(".git", "node_modules", "__pycache__", ".tmp-lane")


@unittest.skipUnless(shutil.which("node"), "node is required to run the validator")
class AllEnforcesOrchestratorFlagsTests(unittest.TestCase):
    """`--all` (npm run validate, CI) runs the same orchestrator flag gate as a single-agent run."""

    def run_all(self, edit) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            shutil.copytree(REPO_ROOT, root, ignore=SKIP)
            target = root / ORCHESTRATOR
            target.write_text(edit(target.read_text(encoding="utf-8")), encoding="utf-8")
            env = dict(os.environ, SKIP_SECURITY_CHECK_TOOLKIT="1")
            return subprocess.run(["node", str(root / "scripts" / "validate-specialist-agent.js"), "--all"],
                                  cwd=root, capture_output=True, text=True, timeout=300, env=env)

    def test_correct_flags_pass(self) -> None:
        result = self.run_all(lambda text: text)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_readonly_true_fails(self) -> None:
        result = self.run_all(lambda text: re.sub(r"(?m)^readonly:.*$", "readonly: true", text, count=1))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("should declare readonly: false", result.stderr)

    def test_missing_external_side_effects_fails(self) -> None:
        result = self.run_all(lambda text: re.sub(r"(?m)^external_side_effects:.*\n", "", text, count=1))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("should declare external_side_effects: true", result.stderr)


if __name__ == "__main__":
    unittest.main()
