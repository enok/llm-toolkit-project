from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ledger_merge_sections.py"
SPEC = importlib.util.spec_from_file_location("ledger_merge_sections", SCRIPT)
assert SPEC and SPEC.loader
merge = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = merge
SPEC.loader.exec_module(merge)

HEADER = "# Tasks Table\n\nLast updated: 2026-01-01 09:00 (shared note kept)\n\n"
STAMP = "2026-02-03 10:15"


def section(name: str, body: str) -> str:
    return f"## Session: {name}\n\n{body}\n\n"


class MergeSectionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def put(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def run_main(self, *args: str):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = merge.main(["--root", str(self.root), "--stamp", STAMP, *args])
        return code, out.getvalue(), err.getvalue()

    def test_other_sessions_are_preserved_byte_for_byte(self) -> None:
        other_a = section("alpha", "alpha notes")
        other_b = section("beta", "beta notes")
        self.put("TASKS_TABLE.md", HEADER + other_a + "---\n\n" + section("mine", "old text") + "---\n\n" + other_b)
        part = self.put("part.md", section("mine", "new text"))
        code, out, err = self.run_main("--merge", f"TASKS_TABLE.md={part}")
        self.assertEqual(code, 0, err)
        text = (self.root / "TASKS_TABLE.md").read_text(encoding="utf-8")
        self.assertIn(other_a, text)
        self.assertIn(other_b, text)
        self.assertIn("new text", text)
        self.assertNotIn("old text", text)
        self.assertEqual(text.count("## Session:"), 3)
        self.assertEqual(text.count("---\n"), 2)  # separators survive the replacement
        self.assertIn("3 -> 3", out)

    def test_missing_section_is_appended_with_separator(self) -> None:
        self.put("TASKS_TABLE.md", HEADER + section("alpha", "alpha notes"))
        part = self.put("part.md", section("fresh", "fresh notes"))
        code, out, _ = self.run_main("--merge", f"TASKS_TABLE.md={part}")
        self.assertEqual(code, 0)
        text = (self.root / "TASKS_TABLE.md").read_text(encoding="utf-8")
        self.assertTrue(text.index("## Session: alpha") < text.index("---") < text.index("## Session: fresh"))
        self.assertIn("1 -> 2", out)

    def test_header_with_any_prefix_matches_exactly(self) -> None:
        self.put("TASKS_TABLE.md", HEADER + section("Cowork / run-1", "one") + section("Cowork / run-10", "ten"))
        part = self.put("part.md", section("Cowork / run-1", "uno"))
        self.assertEqual(self.run_main("--merge", f"TASKS_TABLE.md={part}")[0], 0)
        text = (self.root / "TASKS_TABLE.md").read_text(encoding="utf-8")
        self.assertIn("uno", text)
        self.assertIn("ten", text)  # run-10 is not matched by run-1
        self.assertEqual(text.count("## Session:"), 2)

    def test_only_the_timestamp_of_last_updated_is_refreshed(self) -> None:
        self.put("TASKS_TABLE.md", HEADER + section("mine", "x"))
        part = self.put("part.md", section("mine", "y"))
        self.assertEqual(self.run_main("--merge", f"TASKS_TABLE.md={part}")[0], 0)
        first_lines = (self.root / "TASKS_TABLE.md").read_text(encoding="utf-8").splitlines()[:3]
        self.assertEqual(first_lines, ["# Tasks Table", "", f"Last updated: {STAMP} (shared note kept)"])

    def test_stamp_only_refresh_when_section_text_is_unchanged(self) -> None:
        original = HEADER + section("mine", "same") + "---\n\n" + section("other", "o")
        self.put("TASKS_TABLE.md", original)
        part = self.put("part.md", section("mine", "same"))
        self.assertEqual(self.run_main("--merge", f"TASKS_TABLE.md={part}")[0], 0)
        expected = original.replace("2026-01-01 09:00", STAMP)
        self.assertEqual((self.root / "TASKS_TABLE.md").read_text(encoding="utf-8"), expected)

    def test_count_assertion_fails_when_sections_would_drop(self) -> None:
        ledger = HEADER + section("alpha", "a") + section("beta", "b")
        # A part whose text swallows the next header (a nested header inside one code-free body) cannot drop sections
        # through the normal path, so exercise the guard directly.
        original = merge.merge_text
        try:
            merge.merge_text = lambda l, p, s: (HEADER, 2, 0)
            self.put("TASKS_TABLE.md", ledger)
            part = self.put("part.md", section("alpha", "a2"))
            code, _, err = self.run_main("--merge", f"TASKS_TABLE.md={part}")
        finally:
            merge.merge_text = original
        self.assertEqual(code, 1)
        self.assertIn("section count dropped", err)
        self.assertEqual((self.root / "TASKS_TABLE.md").read_text(encoding="utf-8"), ledger)

    def test_all_or_nothing_across_targets(self) -> None:
        tasks = HEADER + section("mine", "old")
        self.put("TASKS_TABLE.md", tasks)
        good = self.put("good.md", section("mine", "new"))
        bad = self.put("bad.md", "no session header here\n")
        self.put("CONTEXT_STATE.md", HEADER + section("mine", "ctx"))
        code, _, err = self.run_main("--merge", f"TASKS_TABLE.md={good}", "--merge", f"CONTEXT_STATE.md={bad}")
        self.assertEqual(code, 2)
        self.assertIn("no '## Session: ' section", err)
        self.assertEqual((self.root / "TASKS_TABLE.md").read_text(encoding="utf-8"), tasks)

    def test_multiple_sections_in_one_part_file(self) -> None:
        self.put("CONTEXT_STATE.md", HEADER + section("a", "old a"))
        part = self.put("part.md", section("a", "new a") + section("b", "new b"))
        self.assertEqual(self.run_main("--merge", f"CONTEXT_STATE.md={part}")[0], 0)
        text = (self.root / "CONTEXT_STATE.md").read_text(encoding="utf-8")
        self.assertEqual(text.count("## Session:"), 2)
        self.assertIn("new a", text)
        self.assertIn("new b", text)

    def test_crlf_ledger_keeps_crlf(self) -> None:
        ledger = (HEADER + section("mine", "x")).replace("\n", "\r\n")
        self.put("TASKS_TABLE.md", ledger)
        part = self.put("part.md", section("mine", "y"))
        self.assertEqual(self.run_main("--merge", f"TASKS_TABLE.md={part}")[0], 0)
        raw = (self.root / "TASKS_TABLE.md").read_bytes()
        self.assertNotIn(b"\n", raw.replace(b"\r\n", b""))

    def test_bad_stamp_and_missing_args_exit_2(self) -> None:
        self.put("TASKS_TABLE.md", HEADER + section("mine", "x"))
        part = self.put("part.md", section("mine", "y"))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(merge.main(["--root", str(self.root), "--stamp", "yesterday", "--merge", f"TASKS_TABLE.md={part}"]), 2)
            self.assertEqual(merge.main(["--root", str(self.root), "--stamp", STAMP]), 2)
            self.assertEqual(merge.main(["--root", str(self.root), "--stamp", STAMP, "--merge", "TASKS_TABLE.md"]), 2)

    def test_cli_runs_from_another_working_directory(self) -> None:
        self.put("TASKS_TABLE.md", HEADER + section("mine", "x"))
        part = self.put("part.md", section("mine", "y"))
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), "--stamp", STAMP, "--merge", f"TASKS_TABLE.md={part}"],
            cwd=elsewhere, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
