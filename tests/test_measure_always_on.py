from __future__ import annotations

import contextlib
import importlib.util
import io
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("measure_always_on", REPO_ROOT / "scripts" / "measure-always-on.py")
measure_always_on = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(measure_always_on)


def write(root: Path, relative: str, text: str) -> None:
    target = root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")


class MeasureAlwaysOnTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        write(self.root, "AGENTS.md", "a" * 100)
        write(self.root, "CLAUDE.md", "# t\n\n@AGENTS.md\n\nSee `@NOT-IMPORTED.md` and\n```\n@ALSO-NOT.md\n```\n")
        write(self.root, "NOT-IMPORTED.md", "x" * 1000)
        write(self.root, "ALSO-NOT.md", "x" * 1000)
        write(self.root, "rules/on.md", "---\ntrigger: always_on\n---\nbody\n")
        write(self.root, "rules/lazy.md", "---\ntrigger: model_decision\n---\nbody\n")
        write(self.root, "rules/README.md", "---\ntrigger: always_on\n---\nindex\n")
        write(self.root, ".cursor/rules/on.mdc", "---\nalwaysApply: true\n---\nr\n")
        write(self.root, ".cursor/rules/off.mdc", "---\nalwaysApply: false\n---\nr\n")
        write(self.root, ".cursor/rules/plain.md", "---\nalwaysApply: true\n---\nignored\n")
        write(self.root, "skills/demo/SKILL.md", "---\nname: demo\ndescription: >\n  first line\n  second\n---\n")
        write(self.root, "tool-subagents/agent.md", "---\nname: agent\ndescription: \"abc\"\n---\n")
        write(self.root, "tool-subagents/README.md", "---\ndescription: ignored\n---\n")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = measure_always_on.main(["--root", str(self.root), *args])
        return code, out.getvalue(), err.getvalue()

    def test_per_tool_bytes(self) -> None:
        result = measure_always_on.measure(self.root)
        tools = result["tools"]
        claude_bytes = (self.root / "CLAUDE.md").stat().st_size + 100
        self.assertEqual(tools["Claude Code"]["files"], ["CLAUDE.md", "AGENTS.md"])
        self.assertEqual(tools["Claude Code"]["bytes"], claude_bytes)
        self.assertEqual(tools["Codex"]["bytes"], 100)
        self.assertEqual(tools["Codex"]["truncated_bytes"], 0)
        on_rule = (self.root / "rules/on.md").stat().st_size
        self.assertEqual(result["always_on_rules"], {"count": 1, "bytes": on_rule})
        self.assertEqual(tools["Windsurf"]["bytes"], 100 + on_rule)
        self.assertEqual(tools["Cursor"]["files"], ["AGENTS.md", ".cursor/rules/on.mdc"])
        listings = tools["Claude Code"]["listings"]
        self.assertEqual(listings["skill_description_chars"], len("first line second"))
        self.assertEqual(listings["agent_description_chars"], 3)

    def test_codex_truncation_reported(self) -> None:
        write(self.root, "AGENTS.md", "a" * 33000)
        tools = measure_always_on.measure(self.root)["tools"]
        self.assertEqual(tools["Codex"]["bytes"], 32768)
        self.assertEqual(tools["Codex"]["truncated_bytes"], 33000 - 32768)

    def test_check_passes_within_limits(self) -> None:
        code, out, _ = self.run_main("--check")
        self.assertEqual(code, 0)
        self.assertIn("always-on size check passed", out)

    def test_check_fails_when_agents_md_too_large(self) -> None:
        write(self.root, "AGENTS.md", "a" * 24577)
        code, _, err = self.run_main("--check")
        self.assertEqual(code, 1)
        self.assertIn("AGENTS.md is 24,577 B", err)

    def test_agents_md_at_limit_passes(self) -> None:
        write(self.root, "AGENTS.md", "a" * 24576)
        self.assertEqual(self.run_main("--check")[0], 0)

    def test_rules_budget_only_checked_when_given(self) -> None:
        self.assertEqual(self.run_main("--check")[0], 0)
        code, _, err = self.run_main("--check", "--rules-budget", "1")
        self.assertEqual(code, 1)
        self.assertIn("always-on rules total", err)

    def test_without_check_always_exits_zero(self) -> None:
        write(self.root, "AGENTS.md", "a" * 40000)
        self.assertEqual(self.run_main()[0], 0)

    def test_repository_agents_md_within_budget(self) -> None:
        result = measure_always_on.measure(REPO_ROOT)
        self.assertLessEqual(result["agents_md_bytes"], measure_always_on.AGENTS_MAX_DEFAULT)
        self.assertIn("AGENTS.md", result["tools"]["Claude Code"]["files"])


if __name__ == "__main__":
    unittest.main()
