from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ledger_compact.py"
SPEC = importlib.util.spec_from_file_location("ledger_compact", SCRIPT)
assert SPEC and SPEC.loader
ledger = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ledger
SPEC.loader.exec_module(ledger)

TASKS_HEADER = "# Tasks Table\n\nLast updated: 2026-01-01\n\n"
CONTEXT_HEADER = "# Context State\n\nShared notes for all sessions.\n\n"


COLUMNS = (
    "#", "Wave", "Task", "Assets", "Vector DB used", "Complexity", "Model/Effort", "Status",
    "Evidence", "PR link(s)", "CI/CD run link(s)", "Tokens", "% Complete", "SLA", "Remaining SLA",
)


def tasks_section(name: str, remaining: int, heading_suffix: str = "") -> str:
    """A session section in the current 15-column format with its three footer rows."""
    status = "completed" if remaining == 0 else "running"
    row = ["1", "W0", "first step", "none (inline)", "no", "light", "Claude Haiku 5.5 / low", status,
           "first-pass", "-", "-", "1.0K", "100" if remaining == 0 else "40", "00:05", "00:00" if remaining == 0 else "00:03"]
    footer_all = ["**Total (all tasks)**", "", "1"] + [""] * 12
    footer_rem = ["**Total (remaining/not completed)**", "", str(remaining)] + [""] * 12
    footer_crit = ["**Remaining SLA to complete all tasks (critical path)**", "", "1"] + [""] * 12
    rows = [COLUMNS, ["---"] * 15, row, footer_all, footer_rem, footer_crit]
    table = "\n".join("| " + " | ".join(cells) + " |" for cells in rows)
    return f"## Session: {name}{heading_suffix}\n\nRequested by: a user\n\n{table}\n\n"


def short_tasks_section(name: str, remaining: int) -> str:
    """The older short footer form: the count sits right after the label."""
    return (
        f"## Session: {name}\n\n"
        "| # | Task | Status |\n|---|------|--------|\n"
        "| 1 | first step | done |\n"
        f"| Total (remaining/not completed) | {remaining} |\n\n"
    )


def context_section(name: str) -> str:
    return f"## Session: {name}\n\n- decision recorded for {name}\n\n"


def snapshot(root: Path) -> dict[str, bytes]:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


class LedgerCompactTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "ledger"
        self.root.mkdir()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    # -- helpers ---------------------------------------------------------
    def write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8", newline="")
        return path

    def read(self, *parts: str) -> str:
        return self.root.joinpath(*parts).read_text(encoding="utf-8")

    def run_cli(self, *args: str, root: Path | None = None):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = ledger.main(["--root", str(root or self.root), *args])
        text = out.getvalue()
        return code, (json.loads(text) if text.strip() else None), err.getvalue()

    def sessions(self, report, key: str, file: str) -> list[str]:
        return [item["session"] for item in report[key] if item["file"] == file]

    def default_ledgers(self) -> None:
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("alpha-done", 0) + tasks_section("beta-open", 2) + tasks_section("gamma-done", 0))
        self.write("CONTEXT_STATE.md", CONTEXT_HEADER + context_section("alpha-done") + context_section("beta-open") + context_section("gamma-done"))

    # -- selection rules -------------------------------------------------
    def test_archives_sections_with_zero_remaining_and_keeps_header(self) -> None:
        self.default_ledgers()
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(self.sessions(report, "archived", "TASKS_TABLE.md"), ["alpha-done", "gamma-done"])
        self.assertEqual(self.sessions(report, "kept", "TASKS_TABLE.md"), ["beta-open"])
        self.assertEqual(self.read("TASKS_TABLE.md"), TASKS_HEADER + tasks_section("beta-open", 2))
        archive = self.read("ledger-archive", "TASKS_TABLE.archive-2026-02-03.md")
        self.assertIn(tasks_section("alpha-done", 0), archive)
        self.assertIn(tasks_section("gamma-done", 0), archive)
        self.assertNotIn("beta-open", archive)
        self.assertLess(report["bytes_after"]["TASKS_TABLE.md"], report["bytes_before"]["TASKS_TABLE.md"])

    def test_header_wording_is_ignored_only_remaining_count_counts(self) -> None:
        text = (
            TASKS_HEADER
            + tasks_section("late-open", 3, " (all waves complete)")
            + tasks_section("quiet-done", 0, " (work in progress)")
        )
        self.write("TASKS_TABLE.md", text)
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(self.sessions(report, "archived", "TASKS_TABLE.md"), ["quiet-done"])
        self.assertEqual(self.sessions(report, "kept", "TASKS_TABLE.md"), ["late-open"])
        self.assertIn("all waves complete", self.read("TASKS_TABLE.md"))
        self.assertNotIn("late-open", self.read("ledger-archive", "TASKS_TABLE.archive-2026-02-03.md"))

    def test_short_footer_form_is_still_understood(self) -> None:
        self.write("TASKS_TABLE.md", TASKS_HEADER + short_tasks_section("old-done", 0) + short_tasks_section("old-open", 4))
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(self.sessions(report, "archived", "TASKS_TABLE.md"), ["old-done"])
        self.assertEqual(self.sessions(report, "kept", "TASKS_TABLE.md"), ["old-open"])

    def test_remaining_count_is_read_from_task_column_not_other_footers(self) -> None:
        # "Total (all tasks)" is 1 and the critical-path row is non-zero text; only the remaining row decides.
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("done-one", 0))
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(self.sessions(report, "archived", "TASKS_TABLE.md"), ["done-one"])

    def test_footer_inside_code_fence_is_ignored(self) -> None:
        fenced = "## Session: fenced\n\n```\n| **Total (remaining/not completed)** |  | 0 |\n```\n\n"
        self.write("TASKS_TABLE.md", TASKS_HEADER + fenced)
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(report["archived"], [])
        self.assertEqual(report["kept"][0]["reason"], "no-total-row")

    def test_non_numeric_remaining_cell_keeps_section(self) -> None:
        text = tasks_section("odd", 0).replace("|  | 0 |", "|  | 0 pending review |")
        self.write("TASKS_TABLE.md", TASKS_HEADER + text)
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(report["archived"], [])

    def test_session_without_total_row_is_kept(self) -> None:
        self.write("TASKS_TABLE.md", TASKS_HEADER + "## Session: notes-only\n\nno table here\n\n")
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(report["archived"], [])
        self.assertEqual(report["kept"][0]["reason"], "no-total-row")

    def test_keep_protects_zero_remaining_section(self) -> None:
        self.default_ledgers()
        code, report, _ = self.run_cli("--keep", "alpha-done", "--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(self.sessions(report, "archived", "TASKS_TABLE.md"), ["gamma-done"])
        self.assertEqual(self.sessions(report, "kept", "TASKS_TABLE.md"), ["alpha-done", "beta-open"])
        self.assertIn("## Session: alpha-done", self.read("TASKS_TABLE.md"))
        # CONTEXT_STATE follows the protected session too.
        self.assertIn("## Session: alpha-done", self.read("CONTEXT_STATE.md"))
        self.assertNotIn("alpha-done", self.read("ledger-archive", "CONTEXT_STATE.archive-2026-02-03.md"))

    def test_context_state_sections_follow_archived_sessions(self) -> None:
        self.default_ledgers()
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(self.sessions(report, "archived", "CONTEXT_STATE.md"), ["alpha-done", "gamma-done"])
        self.assertEqual(self.read("CONTEXT_STATE.md"), CONTEXT_HEADER + context_section("beta-open"))
        archive = self.read("ledger-archive", "CONTEXT_STATE.archive-2026-02-03.md")
        self.assertIn(context_section("alpha-done"), archive)
        self.assertIn(context_section("gamma-done"), archive)

    def test_cowork_prefixed_heading_name_is_parsed(self) -> None:
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("Cowork / sample-session", 0))
        self.write("CONTEXT_STATE.md", CONTEXT_HEADER + "## Session: Cowork / sample-session\n\nnotes\n\n")
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(self.sessions(report, "archived", "CONTEXT_STATE.md"), ["sample-session"])

    def test_missing_context_state_is_fine(self) -> None:
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("alpha-done", 0) + tasks_section("beta-open", 1))
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(list(report["bytes_before"]), ["TASKS_TABLE.md"])
        self.assertFalse((self.root / "ledger-archive" / "CONTEXT_STATE.archive-2026-02-03.md").exists())

    def test_missing_tasks_table_exits_2(self) -> None:
        self.write("CONTEXT_STATE.md", CONTEXT_HEADER + context_section("alpha-done"))
        before = snapshot(self.root)
        code, report, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIsNone(report)
        self.assertIn("TASKS_TABLE.md not found", err)
        self.assertEqual(snapshot(self.root), before)

    def test_crlf_ledgers_round_trip_untouched_sections(self) -> None:
        kept = tasks_section("beta-open", 2).replace("\n", "\r\n")
        header = TASKS_HEADER.replace("\n", "\r\n")
        self.write("TASKS_TABLE.md", header + tasks_section("alpha-done", 0).replace("\n", "\r\n") + kept)
        code, _, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual((self.root / "TASKS_TABLE.md").read_bytes(), (header + kept).encode("utf-8"))

    # -- write behaviour -------------------------------------------------
    def test_dry_run_writes_nothing(self) -> None:
        self.default_ledgers()
        (self.root / ".git").mkdir()
        before = snapshot(self.root)
        code, report, _ = self.run_cli("--dry-run", "--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertTrue(report["dry_run"])
        self.assertEqual(self.sessions(report, "archived", "TASKS_TABLE.md"), ["alpha-done", "gamma-done"])
        self.assertLess(report["bytes_after"]["TASKS_TABLE.md"], report["bytes_before"]["TASKS_TABLE.md"])
        self.assertEqual(report["exclude"], "would-add")
        self.assertEqual(snapshot(self.root), before)
        self.assertFalse((self.root / "ledger-archive").exists())
        self.assertFalse((self.root / ".git" / "info").exists())

    def test_second_run_is_idempotent(self) -> None:
        self.default_ledgers()
        self.assertEqual(self.run_cli("--date", "2026-02-03")[0], 0)
        after_first = snapshot(self.root)
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(report["archived"], [])
        self.assertEqual(report["bytes_before"], report["bytes_after"])
        self.assertEqual(snapshot(self.root), after_first)

    def test_archive_file_is_appended_not_overwritten(self) -> None:
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("alpha-done", 0) + tasks_section("beta-open", 1))
        self.assertEqual(self.run_cli("--date", "2026-02-03")[0], 0)
        archive_path = self.root / "ledger-archive" / "TASKS_TABLE.archive-2026-02-03.md"
        first = archive_path.read_text(encoding="utf-8")
        self.assertEqual(first.count("# Archived 2026-02-03 from TASKS_TABLE.md"), 1)

        self.write("TASKS_TABLE.md", self.read("TASKS_TABLE.md") + tasks_section("delta-done", 0))
        self.assertEqual(self.run_cli("--date", "2026-02-03")[0], 0)
        second = archive_path.read_text(encoding="utf-8")
        self.assertTrue(second.startswith(first))
        self.assertIn("## Session: delta-done", second)
        self.assertEqual(second.count("# Archived 2026-02-03 from TASKS_TABLE.md"), 2)
        self.assertEqual(second.count("## Session: alpha-done"), 1)

    def test_append_adds_newline_when_archive_lacks_one(self) -> None:
        archive_dir = self.root / "ledger-archive"
        archive_dir.mkdir()
        (archive_dir / "TASKS_TABLE.archive-2026-02-03.md").write_text("previous text without newline", encoding="utf-8", newline="")
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("alpha-done", 0))
        self.assertEqual(self.run_cli("--date", "2026-02-03")[0], 0)
        archive = self.read("ledger-archive", "TASKS_TABLE.archive-2026-02-03.md")
        self.assertTrue(archive.startswith("previous text without newline\n# Archived 2026-02-03"))

    # -- git exclude -----------------------------------------------------
    def test_exclude_line_added_once(self) -> None:
        (self.root / ".git" / "info").mkdir(parents=True)
        exclude = self.root / ".git" / "info" / "exclude"
        exclude.write_text("# local excludes\n*.scratch", encoding="utf-8", newline="")  # no trailing newline
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("alpha-done", 0) + tasks_section("beta-open", 1))
        code, report, _ = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertEqual(report["exclude"], "added")
        self.write("TASKS_TABLE.md", self.read("TASKS_TABLE.md") + tasks_section("delta-done", 0))
        code, report, _ = self.run_cli("--date", "2026-02-04")
        self.assertEqual(code, 0)
        self.assertEqual(report["exclude"], "present")
        lines = exclude.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines.count("ledger-archive/"), 1)
        self.assertEqual(lines[:2], ["# local excludes", "*.scratch"])

    def test_exclude_created_when_info_dir_missing(self) -> None:
        (self.root / ".git").mkdir()
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("alpha-done", 0))
        self.assertEqual(self.run_cli("--date", "2026-02-03")[0], 0)
        self.assertEqual(self.read(".git", "info", "exclude"), "ledger-archive/\n")

    def test_worktree_git_file_resolves_common_dir(self) -> None:
        main_git = Path(self.tmp.name) / "main" / ".git"
        gitdir = main_git / "worktrees" / "wt"
        gitdir.mkdir(parents=True)
        (gitdir / "commondir").write_text("../..\n", encoding="utf-8")
        worktree = Path(self.tmp.name) / "wt"
        worktree.mkdir()
        (worktree / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
        (worktree / "TASKS_TABLE.md").write_text(TASKS_HEADER + tasks_section("alpha-done", 0), encoding="utf-8", newline="")
        code, report, err = self.run_cli("--date", "2026-02-03", root=worktree)
        self.assertEqual(code, 0, err)
        self.assertEqual(report["exclude"], "added")
        self.assertEqual((main_git / "info" / "exclude").read_text(encoding="utf-8"), "ledger-archive/\n")

    def test_unresolvable_git_file_warns_and_still_archives(self) -> None:
        (self.root / ".git").write_text("gitdir: ../does-not-exist/.git/worktrees/x\n", encoding="utf-8")
        self.write("TASKS_TABLE.md", TASKS_HEADER + tasks_section("alpha-done", 0) + tasks_section("beta-open", 1))
        code, report, err = self.run_cli("--date", "2026-02-03")
        self.assertEqual(code, 0)
        self.assertTrue(report["exclude"].startswith("skipped:"))
        self.assertIn("warning", err)
        self.assertTrue((self.root / "ledger-archive" / "TASKS_TABLE.archive-2026-02-03.md").is_file())

    # -- CLI -------------------------------------------------------------
    def test_invalid_date_is_rejected(self) -> None:
        self.default_ledgers()
        before = snapshot(self.root)
        err = io.StringIO()
        with redirect_stderr(err), self.assertRaises(SystemExit) as raised:
            ledger.main(["--root", str(self.root), "--date", "03/02/2026"])
        self.assertEqual(raised.exception.code, 2)
        self.assertIn("YYYY-MM-DD", err.getvalue())
        self.assertEqual(snapshot(self.root), before)

    def test_cli_runs_from_another_working_directory(self) -> None:
        self.default_ledgers()
        elsewhere = Path(self.tmp.name) / "elsewhere"
        elsewhere.mkdir()
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.root), "--keep", "gamma-done", "--date", "2026-02-03"],
            cwd=elsewhere, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(self.sessions(report, "archived", "TASKS_TABLE.md"), ["alpha-done"])
        self.assertFalse(report["dry_run"])


if __name__ == "__main__":
    unittest.main()
