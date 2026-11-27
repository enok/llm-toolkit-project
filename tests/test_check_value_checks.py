"""Pins scripts/check_value_checks.py: the new-resource value-check ledger gate."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_value_checks.py"
HEADER = "resource,kind,date,model,winner,margin,with_passed,plain_passed,of,decision,evidence,note"


def row(resource: str, decision: str = "keep", note: str = "n", winner: str = "with") -> str:
    return f"{resource},rule,2026-11-26,opus,{winner},clear,7,5,7,{decision},audit,{note}"


def git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=repo, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )


def write(repo: Path, rel: str, text: str = "x\n") -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")


class Scenario:
    """Temp repo: base commit with a ledger, then a second commit adding files."""

    def __init__(self, added: List[str], ledger_lines: Optional[List[str]] = None,
                 header: str = HEADER) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "-q")
        write(self.repo, "docs/llm/value-checks.csv", "\n".join([header] + (ledger_lines or [])) + "\n")
        write(self.repo, "README.md")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "base")
        git(self.repo, "tag", "base")
        for rel in added:
            write(self.repo, rel)
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "--allow-empty", "-m", "add")

    def run(self, *extra: str, base: str = "base") -> Tuple[int, str, str]:
        p = subprocess.run(
            [sys.executable, str(SCRIPT), "--base", base, "--repo", str(self.repo), *extra],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=60,
        )
        return p.returncode, p.stdout, p.stderr

    def close(self) -> None:
        self.tmp.cleanup()


class ValueCheckTests(unittest.TestCase):
    def scenario(self, *a, **k) -> Scenario:
        s = Scenario(*a, **k)
        self.addCleanup(s.close)
        return s

    def js(self, s: Scenario) -> Tuple[int, Dict]:
        code, out, _ = s.run("--json")
        return code, json.loads(out)

    def test_no_new_resources_passes(self) -> None:
        code, data = self.js(self.scenario([]))
        self.assertEqual((code, data["checked"]), (0, 0))

    def test_new_skill_with_keep_row_passes(self) -> None:
        s = self.scenario(["skills/foo/SKILL.md"], [row("skills/foo")])
        code, data = self.js(s)
        self.assertEqual(code, 0)
        self.assertEqual((data["checked"], data["passed"], data["failed"]), (1, ["skills/foo"], []))

    def test_skill_row_with_skill_md_suffix_accepted(self) -> None:
        s = self.scenario(["skills/foo/SKILL.md"], [row("skills/foo/SKILL.md", "keep-slim")])
        self.assertEqual(self.js(s)[0], 0)

    def test_new_workflow_without_row_fails(self) -> None:
        s = self.scenario(["workflows/new-flow.md"], [row("rules/other.md")])
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertEqual(data["failed"][0]["resource"], "workflows/new-flow.md")
        self.assertIn("no row", data["failed"][0]["reason"])

    def test_remove_decision_fails(self) -> None:
        s = self.scenario(["rules/r.md"], [row("rules/r.md", "remove")])
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertIn("remove", data["failed"][0]["reason"])

    def test_on_demand_and_slim_fail(self) -> None:
        s = self.scenario(["tool-subagents/a.md", "rules/b.md"],
                          [row("tool-subagents/a.md", "on-demand"), row("rules/b.md", "slim")])
        code, data = self.js(s)
        self.assertEqual((code, len(data["failed"])), (1, 2))

    def test_on_demand_passes_only_when_the_file_loads_on_demand(self) -> None:
        s = self.scenario(["rules/b.md"], [row("rules/b.md", "on-demand")])
        write(s.repo, "rules/b.md", "---\ntrigger: model_decision\ndescription: Load when x\n---\n# B\n")
        self.assertEqual(self.js(s)[0], 0)
        write(s.repo, "rules/b.md", "---\ntrigger: always_on\n---\n# B\n")
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertIn("model_decision", data["failed"][0]["reason"])

    def test_exempt_without_note_fails(self) -> None:
        s = self.scenario(["rules/r.md"], [row("rules/r.md", "exempt", note="", winner="exempt")])
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertIn("empty note", data["failed"][0]["reason"])

    def test_exempt_with_note_passes(self) -> None:
        s = self.scenario(["rules/r.md"], [row("rules/r.md", "exempt", note="mandated", winner="exempt")])
        self.assertEqual(self.js(s)[0], 0)

    def test_unknown_decision_is_failure_and_ledger_error(self) -> None:
        s = self.scenario(["rules/r.md"], [row("rules/r.md", "maybe")])
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertEqual(len(data["failed"]), 1)
        self.assertEqual(len(data["ledger_errors"]), 1)

    def test_bad_winner_is_ledger_error(self) -> None:
        s = self.scenario([], [row("rules/r.md", winner="both")])
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertIn("winner", data["ledger_errors"][0])

    def test_duplicate_rows_are_ledger_error(self) -> None:
        s = self.scenario([], [row("rules/r.md"), row("rules/r.md")])
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertIn("duplicate", data["ledger_errors"][0])

    def test_bad_header_is_ledger_error(self) -> None:
        s = self.scenario(["rules/r.md"], [row("rules/r.md")], header="resource,kind,date")
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertIn("header", data["ledger_errors"][0])

    def test_ignored_paths_do_not_count(self) -> None:
        s = self.scenario([
            "learnings/some-lesson.md", "skills/foo/references/ref.md", "evals/case.md",
            "workflows/README.md", "tool-subagents/README.md", "rules/README.md",
            "rules/examples/ex.md", "rules/mirror.toml", "workflows/flow.toml",
            "scripts/tool.py", "skills/foo/other.md",
        ])
        code, data = self.js(s)
        self.assertEqual((code, data["checked"]), (0, 0))

    def test_modified_existing_file_not_counted(self) -> None:
        s = self.scenario([])
        write(s.repo, "rules/old.md")
        git(s.repo, "add", "-A")
        git(s.repo, "commit", "-q", "-m", "x")
        git(s.repo, "tag", "mid")
        write(s.repo, "rules/old.md", "changed\n")
        git(s.repo, "commit", "-q", "-am", "y")
        code, out, _ = s.run("--json", base="mid")
        self.assertEqual((code, json.loads(out)["checked"]), (0, 0))

    def test_bad_ref_exits_2(self) -> None:
        code, _, err = self.scenario([]).run(base="no-such-ref")
        self.assertEqual(code, 2)
        self.assertIn("git error", err)

    def test_not_a_repository_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            p = subprocess.run([sys.executable, str(SCRIPT), "--base", "x", "--repo", d],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            self.assertEqual(p.returncode, 2)

    def test_json_shape(self) -> None:
        s = self.scenario(["skills/a/SKILL.md", "workflows/w.md"], [row("skills/a")])
        code, data = self.js(s)
        self.assertEqual(code, 1)
        self.assertEqual(set(data), {"checked", "passed", "failed", "ledger_errors"})
        self.assertEqual(data["checked"], 2)
        self.assertEqual(data["passed"], ["skills/a"])
        self.assertEqual(set(data["failed"][0]), {"resource", "reason"})
        self.assertEqual(data["ledger_errors"], [])

    def test_human_report(self) -> None:
        s = self.scenario(["workflows/w.md"])
        code, out, _ = s.run()
        self.assertEqual(code, 1)
        self.assertIn("FAIL workflows/w.md", out)


if __name__ == "__main__":
    unittest.main()
