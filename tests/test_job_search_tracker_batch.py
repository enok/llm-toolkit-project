from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

try:
    import openpyxl
except ImportError:  # pragma: no cover
    openpyxl = None

SCRIPTS = Path(__file__).resolve().parents[1] / "skills" / "job-search-pipeline" / "scripts"
TRACKER_OPS = SCRIPTS / "tracker_ops.py"
BATCH = SCRIPTS / "tracker_batch.py"

LINK_A = "https://www.linkedin.com/jobs/view/111/"
LINK_B = "https://boards.example.com/jobs?gh_jid=222"
LINK_C = "https://www.linkedin.com/jobs/view/333/"
LINK_MISSING = "https://www.linkedin.com/jobs/view/999999/"


class BatchCase(unittest.TestCase):
    """Shared helpers: a temp dir, a CLI runner and readers for the ops/log files."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.tracker = str(self.dir / "tracker.xlsx")
        self.backups = str(self.dir / "backups")
        self.log = self.dir / "batch.log"
        self.ops_file = self.dir / "ops.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_cli(self, script: Path, *args: str, env: dict | None = None) -> subprocess.CompletedProcess:
        full_env = dict(os.environ, **(env or {}))
        return subprocess.run([sys.executable, str(script), *args], capture_output=True, encoding="utf-8",
                              errors="replace", env=full_env, stdin=subprocess.DEVNULL)

    def write_ops(self, ops, wrap: bool = False) -> None:
        self.ops_file.write_text(json.dumps({"ops": ops} if wrap else ops, ensure_ascii=False), encoding="utf-8")

    def batch(self, mtime, *extra: str, env: dict | None = None, tracker_ops: Path | None = None):
        args = ["--tracker", self.tracker, "--ops", str(self.ops_file), "--backup-dir", self.backups,
                "--log", str(self.log), "--expect-mtime", repr(float(mtime)), *extra]
        if tracker_ops is not None:
            args += ["--tracker-ops", str(tracker_ops)]
        proc = self.run_cli(BATCH, *args, env=env)
        summary = None
        if proc.stdout.strip():
            summary = json.loads(proc.stdout.strip().splitlines()[-1])
        return proc, summary

    def log_lines(self) -> list:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines() if line.strip()]

    def file_mtime(self) -> float:
        return os.stat(self.tracker).st_mtime


@unittest.skipIf(openpyxl is None, "openpyxl not installed")
class TrackerBatchTests(BatchCase):
    """tracker_batch.py against the real tracker_ops.py on a small temp tracker."""

    def setUp(self) -> None:
        super().setUp()
        self.assertEqual(self.run_cli(TRACKER_OPS, "init", "--tracker", self.tracker).returncode, 0)
        self.mtime = self.append_jobs([
            {"company": "Acme", "title": "Staff Engineer", "link": LINK_A, "fit": 80, "tier": "A"},
            {"company": "Globex", "title": "Senior Backend", "link": LINK_B, "fit": 70, "tier": "B"},
            {"company": "Initech", "title": "Platform Engineer", "link": LINK_C, "fit": 60, "tier": "B"},
        ])

    def append_jobs(self, jobs: list) -> float:
        path = self.dir / "jobs.json"
        path.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
        proc = self.run_cli(TRACKER_OPS, "append", "--tracker", self.tracker, "--jobs", str(path))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        return json.loads(proc.stdout)["mtime"]

    def rows(self, sheet: str, column: str) -> list:
        ws = openpyxl.load_workbook(self.tracker)[sheet]
        col = next(c.column for c in ws[1] if c.value == column)
        return [ws.cell(r, col).value for r in range(2, ws.max_row + 1) if ws.cell(r, col).value not in (None, "")]

    def test_batch_of_moves_and_a_set_succeeds_and_logs_every_op(self) -> None:
        self.write_ops([
            {"op": "move", "link": LINK_A, "to": "Applied", "date": "2026-01-05", "channel": "Email"},
            {"op": "move", "link": LINK_B, "to": "Applied", "date": "2026-01-06", "follow_up_days": 3},
            {"op": "set", "link": LINK_C, "column": "Decision notes", "value": "Check visa rules", "sheet": "For Approval"},
        ])
        proc, summary = self.batch(self.mtime)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((summary["ok"], summary["skipped"], summary["failed"]), (3, 0, None))
        self.assertEqual(summary["mtime"], self.file_mtime())
        lines = self.log_lines()
        self.assertEqual([x.get("ok") for x in lines], [True, True, True, None])
        self.assertEqual(lines[-1], {"done": True, "mtime": self.file_mtime()})
        self.assertEqual([(x["i"], x["op"], x["link"]) for x in lines[:3]],
                         [(0, "move", LINK_A), (1, "move", LINK_B), (2, "set", LINK_C)])
        mtimes = [x["mtime"] for x in lines[:3]]
        self.assertEqual(mtimes, sorted(mtimes))
        # the tracker reflects every change
        self.assertEqual(self.rows("Applied", "Company"), ["Acme", "Globex"])
        self.assertEqual(self.rows("Applied", "Channel"), ["Email"])
        self.assertEqual(self.rows("Applied", "Follow-up date"), ["2026-01-12", "2026-01-09"])
        self.assertEqual(self.rows("For Approval", "Company"), ["Initech"])
        self.assertEqual(self.rows("For Approval", "Decision notes"), ["Check visa rules"])
        # one pre-batch restore point plus tracker_ops' own backups
        names = sorted(p.name for p in Path(self.backups).iterdir())
        self.assertTrue(any(".pre-batch-" in n for n in names), names)
        self.assertEqual(summary["backup"], str(Path(self.backups) / next(n for n in names if ".pre-batch-" in n)))

    def test_ops_may_be_wrapped_in_an_object_and_saved_with_a_bom(self) -> None:
        self.ops_file.write_bytes(b"\xef\xbb\xbf" + json.dumps(
            {"ops": [{"op": "move", "link": LINK_A, "to": "Excluded", "detail": "Onsite only"}]}).encode("utf-8"))
        proc, summary = self.batch(self.mtime)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(summary["ok"], 1)
        self.assertEqual(self.rows("Excluded", "Company"), ["Acme"])

    def test_invalid_ops_exit_2_listing_every_problem_and_run_nothing(self) -> None:
        self.write_ops([
            {"op": "move", "link": LINK_A, "to": "Applied"},                      # valid, must NOT run
            {"op": "delete", "link": LINK_B},                                      # unknown op
            {"op": "move", "link": LINK_B, "to": "Hired"},                         # bad target
            {"op": "move", "link": LINK_B, "to": "Applied", "colour": "red"},      # unknown key
            {"op": "move", "link": LINK_B, "to": "Applied", "follow_up_days": "7", "date": "05/01/2026"},
            {"op": "set", "link": LINK_B, "column": "Notes"},                      # missing value
            "not an object",
        ])
        before = self.file_mtime()
        proc, summary = self.batch(self.mtime)
        self.assertEqual(proc.returncode, 2)
        for fragment in ("ops[1]: unknown op 'delete'", "ops[2]: 'to' must be one of", "ops[3]: unknown key 'colour'",
                         "ops[4]: 'follow_up_days' must be an integer", "ops[4]: 'date' must be YYYY-MM-DD",
                         "ops[5]: op 'set' needs 'value'", "ops[6]: must be an object"):
            self.assertIn(fragment, proc.stderr)
        self.assertEqual(len(summary["problems"]), 7)
        self.assertEqual((summary["ok"], summary["failed"]), (0, None))
        self.assertEqual(self.file_mtime(), before)
        self.assertEqual(self.rows("Applied", "Company"), [])
        self.assertFalse(self.log.exists())
        self.assertFalse(Path(self.backups).exists())

    def test_missing_ops_file_and_empty_list_exit_2(self) -> None:
        proc, _ = self.batch(self.mtime)  # ops.json was never written
        self.assertEqual(proc.returncode, 2)
        self.write_ops([])
        proc, _ = self.batch(self.mtime)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("non-empty list", proc.stderr)

    def test_failing_op_stops_the_batch_and_propagates_the_exit_code(self) -> None:
        self.write_ops([
            {"op": "move", "link": LINK_A, "to": "Applied"},
            {"op": "move", "link": LINK_MISSING, "to": "Applied"},
            {"op": "move", "link": LINK_B, "to": "Applied"},
        ])
        proc, summary = self.batch(self.mtime)
        self.assertEqual(proc.returncode, 2)  # tracker_ops: "job not found" is a usage error
        self.assertEqual((summary["ok"], summary["failed"]), (1, 1))
        self.assertEqual(summary["mtime"], self.file_mtime())
        lines = self.log_lines()
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0]["ok"])
        self.assertEqual((lines[1]["i"], lines[1]["ok"], lines[1]["exit"]), (1, False, 2))
        self.assertIn("job not found", lines[1]["error"])
        self.assertNotIn("done", json.dumps(lines))
        self.assertEqual(self.rows("Applied", "Company"), ["Acme"])
        self.assertEqual(self.rows("For Approval", "Company"), ["Globex", "Initech"])

    def test_stale_expect_mtime_propagates_exit_code_3_without_writing(self) -> None:
        self.write_ops([{"op": "move", "link": LINK_A, "to": "Applied"}])
        before = self.file_mtime()
        proc, summary = self.batch(1.0)
        self.assertEqual(proc.returncode, 3)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(self.log_lines()[0]["exit"], 3)
        self.assertEqual(self.file_mtime(), before)

    def test_resume_after_a_failure_skips_the_ops_that_already_succeeded(self) -> None:
        bad = [
            {"op": "move", "link": LINK_A, "to": "Applied"},
            {"op": "move", "link": LINK_MISSING, "to": "Applied"},
            {"op": "set", "link": LINK_C, "column": "Notes", "value": "Call on Monday"},
        ]
        self.write_ops(bad)
        proc, _ = self.batch(self.mtime)
        self.assertEqual(proc.returncode, 2)
        # a rerun without --resume must not append to a log that already has content
        proc, summary = self.batch(self.file_mtime())
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--resume", proc.stderr)
        self.assertEqual(len(self.log_lines()), 2)
        # fix the bad op and resume from the tracker's current mtime
        bad[1] = {"op": "move", "link": LINK_B, "to": "Applied"}
        self.write_ops(bad)
        proc, summary = self.batch(self.file_mtime(), "--resume")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((summary["ok"], summary["skipped"], summary["failed"]), (2, 1, None))
        lines = self.log_lines()
        self.assertEqual([(x.get("i"), x.get("ok")) for x in lines],
                         [(0, True), (1, False), (1, True), (2, True), (None, None)])
        self.assertTrue(lines[-1]["done"])
        self.assertEqual(self.rows("Applied", "Company"), ["Acme", "Globex"])  # Acme was not moved twice
        self.assertEqual(self.rows("For Approval", "Notes"), ["Call on Monday"])

    def test_resume_refuses_an_ops_file_that_disagrees_with_the_log(self) -> None:
        self.write_ops([{"op": "move", "link": LINK_A, "to": "Applied"}])
        self.assertEqual(self.batch(self.mtime)[0].returncode, 0)
        self.write_ops([{"op": "move", "link": LINK_B, "to": "Applied"}])
        before = self.file_mtime()
        proc, _ = self.batch(before, "--resume")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("the ops file changed", proc.stderr)
        self.assertEqual(self.file_mtime(), before)

    def test_resume_with_everything_done_runs_nothing(self) -> None:
        self.write_ops([{"op": "move", "link": LINK_A, "to": "Applied"}])
        self.assertEqual(self.batch(self.mtime)[0].returncode, 0)
        before = self.file_mtime()
        proc, summary = self.batch(before, "--resume")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((summary["ok"], summary["skipped"], summary["mtime"]), (0, 1, before))
        self.assertEqual(self.file_mtime(), before)

    def test_plan_prints_the_commands_and_runs_nothing(self) -> None:
        self.write_ops([
            {"op": "move", "link": LINK_A, "to": "Interviewing", "interview_stage": "Screening", "allow_backward": True},
            {"op": "set", "link": LINK_B, "column": "Notes", "value": "-starts with a dash"},
        ])
        before = self.file_mtime()
        proc, _ = self.batch(self.mtime, "--plan")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        plan = json.loads(proc.stdout)
        self.assertEqual((plan["ops"], plan["skipped"]), (2, 0))
        first, second = plan["plan"]
        self.assertIn("--allow-backward", first["argv"])
        self.assertIn("--interview-stage=Screening", first["argv"])
        self.assertIn(f"--expect-mtime={self.mtime!r}", first["argv"])
        self.assertIn("--expect-mtime=<mtime>", second["argv"])
        self.assertIn("--value=-starts with a dash", second["argv"])
        self.assertIn("tracker_ops.py", first["command"])
        self.assertEqual(self.file_mtime(), before)
        self.assertEqual(self.rows("Applied", "Company"), [])
        self.assertFalse(self.log.exists())
        self.assertFalse(Path(self.backups).exists())

    def test_plan_still_rejects_invalid_ops(self) -> None:
        self.write_ops([{"op": "move", "link": LINK_A}])
        proc, _ = self.batch(self.mtime, "--plan")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("needs 'to'", proc.stderr)

    def test_non_ascii_text_passes_through_even_when_the_parent_io_codec_is_ascii(self) -> None:
        title = "Senior Engineer \u2013 Platform"
        note = "Prefers \u201cremote\u201d \u2013 EU only"
        mtime = self.append_jobs([{"company": "Caf\u00e9 \u00dcber", "title": title,
                                   "link": "https://www.linkedin.com/jobs/view/444/"}])
        self.write_ops([
            {"op": "set", "link": "https://www.linkedin.com/jobs/view/444/", "column": "Decision notes", "value": note},
            {"op": "move", "link": "https://www.linkedin.com/jobs/view/444/", "to": "Applied",
             "detail": "applied via referral \u2013 Z\u00fcrich", "date": "2026-02-01"},
        ])
        # PYTHONIOENCODING=ascii in the parent would make an inherited child die on the en dash in its own output
        proc, summary = self.batch(mtime, env={"PYTHONIOENCODING": "ascii"})
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(summary["ok"], 2)
        self.assertEqual(self.rows("Applied", "Title"), [title])
        self.assertEqual(self.rows("Applied", "Company"), ["Caf\u00e9 \u00dcber"])
        self.assertIn("applied via referral \u2013 Z\u00fcrich", self.rows("Applied", "Stage history")[0])
        lines = self.log_lines()
        self.assertEqual([x["ok"] for x in lines[:2]], [True, True])
        self.assertTrue(self.log.read_bytes().isascii())  # the log is ASCII-only JSON, readable under any code page


class TrackerBatchStubTests(BatchCase):
    """tracker_batch.py against a stand-in tracker_ops (no openpyxl needed): chaining, env, child exit codes."""

    STUB = (
        "import json, os, sys\n"
        "rec = os.environ['STUB_RECORD']\n"
        "n = sum(1 for _ in open(rec, encoding='utf-8')) if os.path.exists(rec) else 0\n"
        "with open(rec, 'a', encoding='utf-8') as f:\n"
        "    f.write(json.dumps({'argv': sys.argv[1:], 'exe': sys.executable,\n"
        "                        'io': os.environ.get('PYTHONIOENCODING'), 'utf8': os.environ.get('PYTHONUTF8')}) + '\\n')\n"
        "mode = os.environ.get('STUB_MODE', 'ok')\n"
        "fail_at = int(os.environ.get('STUB_FAIL_AT', '-1'))\n"
        "if n == fail_at and mode == 'locked':\n"
        "    sys.stderr.write('tracker_ops: tracker is locked or read-only\\n'); sys.exit(4)\n"
        "if n == fail_at and mode == 'garbage':\n"
        "    print('not json at all'); sys.exit(0)\n"
        "if n == fail_at and mode == 'crash':\n"
        "    if os.name == 'nt':\n"
        "        sys.exit(3221225786)\n"
        "    import signal; os.kill(os.getpid(), signal.SIGKILL)\n"
        "print(json.dumps({'mtime': 1000.5 + n}, indent=1))\n"
    )

    def setUp(self) -> None:
        super().setUp()
        Path(self.tracker).write_bytes(b"placeholder")
        self.stub = self.dir / "stub_ops.py"
        self.stub.write_text(self.STUB, encoding="utf-8")
        self.record = self.dir / "record.jsonl"
        self.write_ops([
            {"op": "move", "link": LINK_A, "to": "Applied"},
            {"op": "set", "link": LINK_B, "column": "Notes", "value": 7},
            {"op": "move", "link": LINK_C, "to": "Closed", "outcome": "Rejected", "detail": "-no thanks"},
        ])

    def run_stub(self, mode: str = "ok", fail_at: int = -1, *extra: str):
        env = {"STUB_RECORD": str(self.record), "STUB_MODE": mode, "STUB_FAIL_AT": str(fail_at)}
        return self.batch(500.25, *extra, env=env, tracker_ops=self.stub)

    def calls(self) -> list:
        return [json.loads(x) for x in self.record.read_text(encoding="utf-8").splitlines()]

    def test_each_returned_mtime_feeds_the_next_expect_mtime(self) -> None:
        proc, summary = self.run_stub()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(summary, {"ok": 3, "skipped": 0, "failed": None, "mtime": 1002.5, "backup": summary["backup"]})
        calls = self.calls()
        self.assertEqual([next(a for a in c["argv"] if a.startswith("--expect-mtime=")) for c in calls],
                         ["--expect-mtime=500.25", "--expect-mtime=1000.5", "--expect-mtime=1001.5"])
        for c in calls:
            self.assertIn(f"--backup-dir={self.backups}", c["argv"])
            self.assertIn(f"--tracker={self.tracker}", c["argv"])
            self.assertEqual((c["exe"], c["io"], c["utf8"]), (sys.executable, "utf-8", "1"))
        self.assertEqual(calls[1]["argv"][0], "set")
        self.assertIn("--value=7", calls[1]["argv"])
        self.assertIn("--detail=-no thanks", calls[2]["argv"])
        self.assertEqual(self.log_lines()[-1], {"done": True, "mtime": 1002.5})

    def test_exit_code_4_locked_is_propagated(self) -> None:
        proc, summary = self.run_stub("locked", fail_at=1)
        self.assertEqual(proc.returncode, 4)
        self.assertEqual((summary["ok"], summary["failed"], summary["mtime"]), (1, 1, 1000.5))
        failure = self.log_lines()[1]
        self.assertEqual((failure["ok"], failure["exit"]), (False, 4))
        self.assertIn("locked", failure["error"])
        self.assertEqual(len(self.calls()), 2)  # the third op never ran

    def test_exit_zero_without_a_json_mtime_is_a_failure(self) -> None:
        proc, summary = self.run_stub("garbage", fail_at=0)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(summary["failed"], 0)
        self.assertIn("not json at all", self.log_lines()[0]["error"])

    def test_a_child_killed_by_a_signal_maps_to_exit_1(self) -> None:
        proc, summary = self.run_stub("crash", fail_at=0)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(self.log_lines()[0]["exit"], 1)

    def test_resume_continues_from_the_given_mtime_and_appends_to_the_log(self) -> None:
        proc, _ = self.run_stub("locked", fail_at=1)
        self.assertEqual(proc.returncode, 4)
        self.record.unlink()
        proc, summary = self.batch(2000.0, "--resume", env={"STUB_RECORD": str(self.record)}, tracker_ops=self.stub)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual((summary["ok"], summary["skipped"]), (2, 1))
        self.assertEqual([c["argv"][0] for c in self.calls()], ["set", "move"])
        self.assertIn("--expect-mtime=2000.0", self.calls()[0]["argv"])

    def test_missing_required_arguments_and_unknown_tracker_ops_exit_2(self) -> None:
        proc = self.run_cli(BATCH, "--tracker", self.tracker, "--ops", str(self.ops_file))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--expect-mtime", proc.stderr)
        proc, summary = self.batch(1.0, tracker_ops=self.dir / "nope.py")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("tracker_ops.py not found", proc.stderr)


if __name__ == "__main__":
    unittest.main()
