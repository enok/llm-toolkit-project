from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "validate-specialist-agent.js"
HEADER = "resource,type,date,model,winner,margin,a,b,c,decision,source,note\n"


def ledger_row(path: str) -> str:
    return f"{path},workflow,2026-11-27,opus,plain,slight,8,8,8,remove,test,note\n"


def write(root: Path, relative: str, text: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")


@unittest.skipUnless(shutil.which("node"), "node is required to run the validator")
class CompanionLedgerTests(unittest.TestCase):
    """A missing evolution workflow passes only on an exact `remove` ledger row."""

    def run_validator(self, agent: str, ledger_paths: "list[str]") -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            shutil.copy(SCRIPT, root / "scripts" / SCRIPT.name)
            prompt = (f"---\nname: {agent}\nreadonly: true\n---\n\n## Related Specialists\n\n"
                      "Learning/token efficiency\n")
            write(root, f"tool-subagents/{agent}.md", prompt)
            write(root, f"tool-subagents/{agent}.toml", f'name = "{agent}"\n')
            write(root, "tool-subagents/README.md", f"`{agent}`\n")
            write(root, f"skills/{agent}/SKILL.md", f"---\nname: {agent}\n---\n")
            write(root, f"workflows/{agent}-validation.md", "validation\n")
            write(root, "workflows/README.md", f"{agent}-validation.md\n")
            for index in ("AGENTS.md", "README.md", "INTENTS.md"):
                write(root, index, f"**{agent}**\n")
            write(root, "docs/llm/value-checks.csv", HEADER + "".join(ledger_row(p) for p in ledger_paths))
            return subprocess.run(["node", str(root / "scripts" / SCRIPT.name), agent],
                                  cwd=root, capture_output=True, text=True, timeout=60)

    def test_exact_remove_row_passes(self) -> None:
        result = self.run_validator("demo-checker", ["workflows/demo-checker-evolution.md"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_no_row_fails(self) -> None:
        result = self.run_validator("demo-checker", [])
        self.assertEqual(result.returncode, 1)
        self.assertIn("evolution workflow missing for demo-checker", result.stderr)

    def test_row_for_a_different_path_fails(self) -> None:
        result = self.run_validator("demo-checker", ["workflows/demo-evolution.md"])
        self.assertEqual(result.returncode, 1)
        self.assertIn("evolution workflow missing for demo-checker", result.stderr)

    def test_listed_alias_passes(self) -> None:
        result = self.run_validator("java-change-validator", ["workflows/java-validator-evolution.md"])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
