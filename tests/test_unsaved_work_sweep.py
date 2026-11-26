from __future__ import annotations

import contextlib
import datetime as dt
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "unsaved_work_sweep.py"
SPEC = importlib.util.spec_from_file_location("unsaved_work_sweep", SCRIPT)
assert SPEC and SPEC.loader
sweep = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sweep
SPEC.loader.exec_module(sweep)

HAS_GIT = shutil.which("git") is not None
TODAY = dt.date(2026, 3, 1)

COLUMNS = ("#", "Wave", "Task", "Assets", "Vector DB used", "Complexity", "Model/Effort", "Status",
           "Evidence", "PR link(s)", "CI/CD run link(s)", "Tokens", "% Complete", "SLA", "Remaining SLA")


def ledger_section(name: str, date: str, remaining: int) -> str:
    footer = ["**Total (remaining/not completed)**", "", str(remaining)] + [""] * 12
    table = "\n".join("| " + " | ".join(c) + " |" for c in (COLUMNS, ("---",) * 15, footer))
    return f"## Session: {name} ({date} 09:00 UTC)\n\n{table}\n\n"


def run(cwd: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, check=True)
    return result.stdout


def init_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    run(path, "init", "-q", "-b", "main")
    run(path, "config", "user.email", "test@example.com")
    run(path, "config", "user.name", "Test")
    run(path, "config", "commit.gpgsign", "false")
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    run(path, "add", ".")
    run(path, "commit", "-q", "-m", "init")
    return path


@unittest.skipUnless(HAS_GIT, "git is required")
class SweepTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        # A bare "remote" so main has an upstream and a clean repo has no findings.
        self.remote = self.base / "remote.git"
        run(self.base, "init", "-q", "--bare", "-b", "main", str(self.remote))
        self.repo = init_repo(self.base / "repo")
        run(self.repo, "remote", "add", "origin", str(self.remote))
        run(self.repo, "push", "-q", "-u", "origin", "main")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def sweep(self, *extra_roots: Path, stale_days: int = 7, output_dirs=()):
        return sweep.run_sweep([self.repo, *extra_roots], list(output_dirs), stale_days, today=TODAY)

    def kinds(self, report) -> list[str]:
        return sorted(item["kind"] for item in report["findings"])

    def test_clean_repo_has_no_findings(self) -> None:
        report = self.sweep()
        self.assertEqual(report["findings"], [])
        self.assertEqual(report["errors"], [])
        self.assertEqual(report["total"], 0)

    def test_dirty_tracked_file_is_reported(self) -> None:
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        report = self.sweep()
        self.assertEqual(self.kinds(report), ["dirty-worktree"])
        self.assertIn("README.md", report["findings"][0]["files"][0])

    def test_untracked_asset_under_watched_dir_is_reported_others_are_not(self) -> None:
        (self.repo / "learnings").mkdir()
        (self.repo / "learnings" / "new-lesson.md").write_text("x\n", encoding="utf-8")
        (self.repo / "notes.txt").write_text("scratch\n", encoding="utf-8")
        report = self.sweep()
        self.assertEqual(self.kinds(report), ["untracked-asset"])
        self.assertEqual(report["findings"][0]["detail"], "learnings/new-lesson.md")

    def test_ignored_untracked_asset_is_not_reported(self) -> None:
        (self.repo / ".gitignore").write_text("skills/tmp/\n", encoding="utf-8")
        run(self.repo, "add", ".gitignore")
        run(self.repo, "commit", "-q", "-m", "ignore")
        run(self.repo, "push", "-q")
        (self.repo / "skills" / "tmp").mkdir(parents=True)
        (self.repo / "skills" / "tmp" / "x.md").write_text("x\n", encoding="utf-8")
        self.assertEqual(self.sweep()["findings"], [])

    def test_branch_without_remote_is_reported_with_commit_count(self) -> None:
        run(self.repo, "checkout", "-q", "-b", "feature/local-only")
        (self.repo / "a.txt").write_text("a\n", encoding="utf-8")
        run(self.repo, "add", ".")
        run(self.repo, "commit", "-q", "-m", "a")
        run(self.repo, "checkout", "-q", "main")
        report = self.sweep()
        self.assertEqual(self.kinds(report), ["branch-no-remote"])
        self.assertEqual(report["findings"][0]["where"], "feature/local-only")
        self.assertEqual(report["findings"][0]["commits"], 1)

    def test_branch_pushed_without_upstream_config_is_not_reported(self) -> None:
        run(self.repo, "branch", "same-name")
        run(self.repo, "push", "-q", "origin", "same-name")
        self.assertEqual(self.sweep()["findings"], [])

    def test_unpushed_commit_on_tracked_branch_is_reported(self) -> None:
        (self.repo / "b.txt").write_text("b\n", encoding="utf-8")
        run(self.repo, "add", ".")
        run(self.repo, "commit", "-q", "-m", "b")
        report = self.sweep()
        self.assertEqual(self.kinds(report), ["branch-unpushed"])
        self.assertEqual(report["findings"][0]["ahead"], 1)

    def test_upstream_gone_is_reported(self) -> None:
        run(self.repo, "checkout", "-q", "-b", "topic")
        run(self.repo, "push", "-q", "-u", "origin", "topic")
        run(self.repo, "checkout", "-q", "main")
        run(self.remote, "branch", "-q", "-D", "topic")
        run(self.repo, "fetch", "-q", "--prune")
        self.assertEqual(self.kinds(self.sweep()), ["branch-upstream-gone"])

    def test_stash_is_reported(self) -> None:
        (self.repo / "README.md").write_text("stash me\n", encoding="utf-8")
        run(self.repo, "stash", "push", "-q", "-m", "wip")
        report = self.sweep()
        self.assertEqual(self.kinds(report), ["stash"])
        self.assertIn("wip", report["findings"][0]["detail"])

    def test_linked_worktree_is_found_from_main_checkout_and_deduplicated(self) -> None:
        wt = self.base / "wt"
        run(self.repo, "worktree", "add", "-q", "-b", "wt-branch", str(wt))
        run(self.repo, "push", "-q", "-u", "origin", "wt-branch")
        (wt / "README.md").write_text("dirty in worktree\n", encoding="utf-8")
        report = self.sweep(wt)  # worktree passed again as a root: still one finding
        dirty = [f for f in report["findings"] if f["kind"] == "dirty-worktree"]
        self.assertEqual(len(dirty), 1)
        self.assertEqual(Path(dirty[0]["where"]).resolve(), wt.resolve())

    def test_detached_head_with_unreferenced_commit_is_reported(self) -> None:
        run(self.repo, "checkout", "-q", "--detach")
        (self.repo / "d.txt").write_text("d\n", encoding="utf-8")
        run(self.repo, "add", ".")
        run(self.repo, "commit", "-q", "-m", "d")
        self.assertIn("detached-head", self.kinds(self.sweep()))

    def test_open_stale_ledger_section_is_reported_fresh_and_done_are_not(self) -> None:
        text = (
            "# Tasks Table\n\n"
            + ledger_section("old-open", "2026-01-01", 3)
            + ledger_section("fresh-open", "2026-02-27", 2)
            + ledger_section("old-done", "2026-01-01", 0)
        )
        (self.repo / "TASKS_TABLE.md").write_text(text, encoding="utf-8")
        run(self.repo, "add", ".")
        run(self.repo, "commit", "-q", "-m", "ledger")
        run(self.repo, "push", "-q")
        report = self.sweep(stale_days=7)
        self.assertEqual(self.kinds(report), ["ledger-open-section"])
        self.assertIn("old-open", report["findings"][0]["where"])
        self.assertEqual(report["findings"][0]["age_days"], 59)
        # A zero threshold makes the fresh section visible too.
        self.assertEqual(len(self.sweep(stale_days=0)["findings"]), 2)

    def test_ledger_section_without_date_counts_as_unknown_age(self) -> None:
        section = ledger_section("undated", "2026-01-01", 1).replace(" (2026-01-01 09:00 UTC)", "")
        (self.repo / "TASKS_TABLE.md").write_text("# Tasks\n\n" + section, encoding="utf-8")
        run(self.repo, "add", ".")
        run(self.repo, "commit", "-q", "-m", "ledger")
        run(self.repo, "push", "-q")
        report = self.sweep()
        self.assertEqual(self.kinds(report), ["ledger-open-section"])
        self.assertIsNone(report["findings"][0]["age_days"])

    def test_output_dir_artifacts_are_reported(self) -> None:
        out = self.base / "outputs"
        out.mkdir()
        (out / "work.bundle").write_bytes(b"x")
        (out / "fix.patch").write_text("p\n", encoding="utf-8")
        (out / "notes.md").write_text("n\n", encoding="utf-8")
        report = self.sweep(output_dirs=[out])
        self.assertEqual(self.kinds(report), ["loose-artifact", "loose-artifact"])

    def test_non_git_root_is_an_error_not_a_crash(self) -> None:
        plain = self.base / "plain"
        plain.mkdir()
        report = sweep.run_sweep([plain], [], 7, today=TODAY)
        self.assertEqual(report["findings"], [])
        self.assertEqual(len(report["errors"]), 1)

    def test_sweep_never_mutates_the_repository(self) -> None:
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        (self.repo / "rules").mkdir()
        (self.repo / "rules" / "r.md").write_text("r\n", encoding="utf-8")
        before = run(self.repo, "status", "--porcelain=v2", "--untracked-files=all")
        refs = run(self.repo, "for-each-ref")
        self.sweep()
        self.assertEqual(run(self.repo, "status", "--porcelain=v2", "--untracked-files=all"), before)
        self.assertEqual(run(self.repo, "for-each-ref"), refs)

    # -- CLI -------------------------------------------------------------
    def cli(self, *args: str):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = sweep.main(["--root", str(self.repo), *args])
        return code, out.getvalue()

    def test_exit_zero_with_findings_by_default_and_json_output(self) -> None:
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        code, text = self.cli("--json")
        self.assertEqual(code, 0)
        data = json.loads(text)
        self.assertEqual(data["counts"], {"dirty-worktree": 1})
        self.assertEqual(data["total"], 1)

    def test_fail_on_findings_exits_one_only_with_findings(self) -> None:
        self.assertEqual(self.cli("--fail-on-findings")[0], 0)
        (self.repo / "README.md").write_text("changed\n", encoding="utf-8")
        code, text = self.cli("--fail-on-findings")
        self.assertEqual(code, 1)
        self.assertIn("[dirty-worktree] 1", text)

    def test_human_output_for_clean_repo_says_nothing_found(self) -> None:
        code, text = self.cli()
        self.assertEqual(code, 0)
        self.assertIn("Nothing found", text)

    def test_negative_stale_days_is_a_usage_error(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as raised:
            sweep.parse_args(["--stale-days", "-1"])
        self.assertEqual(raised.exception.code, 2)

    def test_script_runs_from_another_directory(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--root", str(self.repo), "--json"],
            cwd=self.base, text=True, capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["total"], 0)


if __name__ == "__main__":
    unittest.main()
