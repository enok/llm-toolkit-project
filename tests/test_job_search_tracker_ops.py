from __future__ import annotations

import datetime as dt
import importlib.util
import io
import json
import os
import re
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

try:
    import openpyxl  # noqa: F401
except ImportError:  # pragma: no cover
    openpyxl = None

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "job-search-pipeline" / "scripts" / "tracker_ops.py"


def load():
    spec = importlib.util.spec_from_file_location("tracker_ops", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


@unittest.skipIf(openpyxl is None, "openpyxl not installed")
class TrackerOpsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ops = load()
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.tracker = str(self.dir / "tracker.xlsx")
        self.assertEqual(self.run_ops("init", "--tracker", self.tracker)[0], 0)
        jobs = [
            {"company": "Acme", "title": "Staff Engineer", "link": "https://www.linkedin.com/jobs/view/111/",
             "fit": 80, "tier": "A", "required": ["Java", "Kafka", "GraphQL"], "nice": ["Rust"]},
            {"company": "Globex", "title": "Senior Backend", "link": "https://boards.example.com/jobs?gh_jid=222",
             "fit": 70, "tier": "B", "required": ["Java", "GraphQL"], "red_flags": ["pay not stated"]},
        ]
        self.jobs = self.dir / "jobs.json"
        self.jobs.write_text(json.dumps({"jobs": jobs}), encoding="utf-8")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_ops(self, *args):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = self.ops.main(list(args))
        return code, (json.loads(buf.getvalue()) if buf.getvalue().strip() else None)

    def test_append_dedups_and_lists_known(self) -> None:
        code, out = self.run_ops("append", "--tracker", self.tracker, "--jobs", str(self.jobs), "--cv-skill", "^java$")
        self.assertEqual(code, 0)
        self.assertEqual(len(out["added"]), 2)
        code, out = self.run_ops("append", "--tracker", self.tracker, "--jobs", str(self.jobs))
        self.assertEqual(out["added"], [])
        self.assertEqual(len(out["skipped_duplicates"]), 2)
        _, known = self.run_ops("known", "--tracker", self.tracker)
        self.assertIn("111", known["ids"])
        self.assertIn("222", known["ids"])

    def test_known_lists_rejected_companies_from_closed_rows(self) -> None:
        _, empty = self.run_ops("known", "--tracker", self.tracker)
        self.assertEqual(empty["rejected_companies"], [])
        wb = openpyxl.load_workbook(self.tracker)
        ws = wb["Closed"]
        h = {c.value: c.column for c in ws[1]}
        rows = [
            ("ExampleCorp", "Rejected"),
            ("examplecorp", "Rejected"),       # same company, other case: listed once
            ("Zeta Labs", " REJECTED "),       # outcome match ignores case and padding
            ("alpha Works", "rejected"),
            ("OfferCo", "Offer"),
            ("NoReplyCo", "No response"),
            ("BlankOutcomeCo", None),
            (None, "Rejected"),                # blank company is skipped
            ("  ", "Rejected"),
        ]
        for i, (company, outcome) in enumerate(rows, start=2):
            ws.cell(i, h["Company"]).value = company
            ws.cell(i, h["Title"]).value = f"Role {i}"
            ws.cell(i, h["Outcome"]).value = outcome
        wb.save(self.tracker)
        code, known = self.run_ops("known", "--tracker", self.tracker)
        self.assertEqual(code, 0)
        self.assertEqual(known["rejected_companies"], ["alpha Works", "ExampleCorp", "Zeta Labs"])
        for key in ("mtime", "ids", "company_title"):  # existing keys stay
            self.assertIn(key, known)
        self.assertIn("examplecorp | role 2", known["company_title"])
        out = str(self.dir / "known.json")
        code, summary = self.run_ops("known", "--tracker", self.tracker, "--out", out)
        self.assertEqual((code, summary["rejected_companies"]), (0, 3))
        self.assertEqual(json.loads(Path(out).read_text(encoding="utf-8"))["rejected_companies"], known["rejected_companies"])

    def test_expect_mtime_mismatch_aborts_without_writing(self) -> None:
        code, _ = self.run_ops("append", "--tracker", self.tracker, "--jobs", str(self.jobs), "--expect-mtime", "1")
        self.assertEqual(code, 3)
        _, known = self.run_ops("known", "--tracker", self.tracker)
        self.assertEqual(known["ids"], [])

    def test_approvals_and_moves(self) -> None:
        self.run_ops("append", "--tracker", self.tracker, "--jobs", str(self.jobs))
        wb = openpyxl.load_workbook(self.tracker)
        wb["For Approval"]["B2"] = "☑ Approve"
        wb["For Approval"]["B3"] = "✖ Reject"
        wb.save(self.tracker)
        _, appr = self.run_ops("approvals", "--tracker", self.tracker)
        self.assertEqual([x["company"] for x in appr["approve"]], ["Acme"])
        self.assertEqual([x["company"] for x in appr["reject"]], ["Globex"])
        link = "https://www.linkedin.com/jobs/view/111/"
        self.assertEqual(self.run_ops("move", "--tracker", self.tracker, "--link", link, "--to", "Applied",
                                      "--date", "2026-01-05")[0], 0)
        self.assertEqual(self.run_ops("move", "--tracker", self.tracker, "--link", link, "--to", "Closed",
                                      "--date", "2026-01-20", "--outcome", "Rejected", "--detail", "not moving forward")[0], 0)
        self.assertEqual(self.run_ops("move", "--tracker", self.tracker, "--link",
                                      "https://boards.example.com/jobs?gh_jid=222", "--to", "Excluded")[0], 0)
        wb = openpyxl.load_workbook(self.tracker)
        closed = [c.value for c in wb["Closed"][2]]
        self.assertIn("Rejected", closed)
        self.assertIn("2026-01-05 Applied; 2026-01-20 Closed (not moving forward)", closed)
        self.assertEqual(wb["Excluded"]["A2"].value, "Globex")
        self.assertIsNone(wb["For Approval"]["F2"].value)

    def test_write_returns_mtime_for_chained_writes_and_refuses_backward_moves(self) -> None:
        _, out = self.run_ops("append", "--tracker", self.tracker, "--jobs", str(self.jobs))
        link = "https://www.linkedin.com/jobs/view/111/"
        code, out = self.run_ops("move", "--tracker", self.tracker, "--link", link, "--to", "Interviewing",
                                 "--expect-mtime", str(out["mtime"]), "--interview-stage", "Screening")
        self.assertEqual(code, 0)
        code, _ = self.run_ops("move", "--tracker", self.tracker, "--link", link, "--to", "Applied",
                               "--expect-mtime", str(out["mtime"]))
        self.assertEqual(code, 2)
        excluded = self.dir / "excluded.json"
        excluded.write_text(json.dumps([{"company": "Initech", "title": "Dev", "link": "https://x.example/j/9",
                                         "reason": "On-site only", "typo_key": 1}]), encoding="utf-8")
        code, out = self.run_ops("exclude", "--tracker", self.tracker, "--jobs", str(excluded),
                                 "--expect-mtime", str(out["mtime"]))
        self.assertEqual((code, out["excluded"]), (0, ["https://x.example/j/9"]))

    def test_sidegig_upserts_by_platform(self) -> None:
        data = self.dir / "gigs.json"
        data.write_text(json.dumps([{"platform": "ExampleGigs", "status": "Invited", "next_action": "Take test"}]),
                        encoding="utf-8")
        _, out = self.run_ops("sidegig", "--tracker", self.tracker, "--data", str(data))
        self.assertEqual(out["added"], ["ExampleGigs"])
        data.write_text(json.dumps([{"platform": "examplegigs", "status": "Active"}]), encoding="utf-8")
        _, out = self.run_ops("sidegig", "--tracker", self.tracker, "--data", str(data))
        self.assertEqual(out["updated"], ["examplegigs"])
        wb = openpyxl.load_workbook(self.tracker)
        self.assertEqual(wb["Side Gigs"]["D2"].value, "Active")
        self.assertIsNone(wb["Side Gigs"]["B3"].value)

    def test_gaps_flags_repeated_gap_and_keeps_owner_status(self) -> None:
        self.run_ops("append", "--tracker", self.tracker, "--jobs", str(self.jobs))
        rules = self.dir / "rules.json"
        rules.write_text(json.dumps({"cv_skills": ["^java$"], "rules": [{"match": "kafka", "ref": "P-1", "week": "W2"}]}),
                         encoding="utf-8")
        wb = openpyxl.load_workbook(self.tracker)
        wb["Skill Map"]["F5"] = "Owner note"  # Rust row: owner-set status must survive
        wb.save(self.tracker)
        code, out = self.run_ops("gaps", "--tracker", self.tracker, "--rules", str(rules))
        self.assertEqual(code, 0)
        self.assertEqual(out["repeated_gaps"], [{"skill": "GraphQL", "jobs": 2}])
        wb = openpyxl.load_workbook(self.tracker)
        self.assertEqual(wb["Skill Map"]["F5"].value, "Owner note")
        fa = wb["For Approval"]
        hdr = [c.value for c in fa[1]]
        self.assertEqual(fa.cell(2, hdr.index("Readiness %") + 1).value, 0.38)
        self.assertTrue(str(fa.cell(2, hdr.index("Next study action") + 1).value).startswith("Close GAP: GraphQL"))


    # --- optional ATS columns, shortlist, expire -------------------------------------------------------------

    OPTIONAL = ["ATS match %", "Missing keywords", "Apply kit"]

    def write_jobs(self, name, jobs) -> str:
        path = self.dir / name
        path.write_text(json.dumps({"jobs": jobs}), encoding="utf-8")
        return str(path)

    def job(self, n, **kw) -> dict:
        base = {"company": f"Co{n}", "title": f"Role {n}", "link": f"https://jobs.example/view/{n}",
                "required": [f"Skill{n}"]}
        base.update(kw)
        return base

    def header(self, sheet="For Approval") -> list:
        wb = openpyxl.load_workbook(self.tracker)
        return [c.value for c in wb[sheet][1] if c.value not in (None, "")]

    def rows_by_company(self, sheet="For Approval") -> dict:
        wb = openpyxl.load_workbook(self.tracker)
        ws = wb[sheet]
        hdr = [c.value for c in ws[1]]
        ci = hdr.index("Company")
        return {row[ci].value: {hdr[i]: c.value for i, c in enumerate(row)}
                for row in ws.iter_rows(min_row=2) if row[ci].value}

    def edit(self, fn) -> None:
        """Owner-style edit of the workbook: fn(workbook, header_index_by_name)."""
        wb = openpyxl.load_workbook(self.tracker)
        ws = wb["For Approval"]
        fn(wb, {c.value: c.column for c in ws[1] if c.value})
        wb.save(self.tracker)

    def mark(self, marks: dict) -> None:
        def go(wb, col):
            ws = wb["For Approval"]
            for r in range(2, ws.max_row + 1):
                if ws.cell(r, col["Company"]).value in marks:
                    ws.cell(r, col["Approve ☐"]).value = marks[ws.cell(r, col["Company"]).value]
        self.edit(go)

    def file_state(self):
        p = Path(self.tracker)
        return p.stat().st_mtime, p.read_bytes()

    def test_append_adds_optional_columns_at_end_and_writes_values(self) -> None:
        before = self.header()
        self.edit(lambda wb, col: setattr(wb["For Approval"].auto_filter, "ref", "A1:AD1"))
        jobs = self.write_jobs("kit.json", [
            self.job(1, ats_match=87, missing_keywords=["Kafka", " Spring ", ""], apply_kit="kits/co1"),
            self.job(2, missing_keywords="GraphQL; Rust"),
        ])
        code, out = self.run_ops("append", "--tracker", self.tracker, "--jobs", jobs)
        self.assertEqual(code, 0)
        self.assertEqual(out["columns_added"], self.OPTIONAL)
        self.assertNotIn("ats_match", out["ignored_keys"])
        self.assertNotIn("missing_keywords", out["ignored_keys"])
        self.assertNotIn("apply_kit", out["ignored_keys"])
        self.assertEqual(self.header(), before + self.OPTIONAL)  # existing order untouched, new ones last
        rows = self.rows_by_company()
        self.assertEqual(rows["Co1"]["ATS match %"], 87)
        self.assertIsInstance(rows["Co1"]["ATS match %"], int)
        self.assertEqual(rows["Co1"]["Missing keywords"], "Kafka; Spring")
        self.assertEqual(rows["Co1"]["Apply kit"], "kits/co1")
        self.assertEqual(rows["Co1"]["Approve ☐"], "☐")
        self.assertIsNone(rows["Co2"]["ATS match %"])
        self.assertEqual(rows["Co2"]["Missing keywords"], "GraphQL; Rust")
        self.assertIsNone(rows["Co2"]["Apply kit"])
        wb = openpyxl.load_workbook(self.tracker)
        self.assertEqual(wb["For Approval"].auto_filter.ref, "A1:AG1")
        # second append reuses the columns instead of adding duplicates
        more = self.write_jobs("kit2.json", [self.job(3, ats_match="64", apply_kit="kits/co3")])
        code, out = self.run_ops("append", "--tracker", self.tracker, "--jobs", more)
        self.assertEqual((code, out["columns_added"]), (0, []))
        self.assertEqual(self.header(), before + self.OPTIONAL)
        self.assertEqual(self.rows_by_company()["Co3"]["ATS match %"], 64)

    def test_append_without_optional_keys_keeps_header_and_dry_run_adds_nothing(self) -> None:
        before = self.header()
        code, out = self.run_ops("append", "--tracker", self.tracker, "--jobs", str(self.jobs))
        self.assertEqual((code, out["columns_added"]), (0, []))
        self.assertEqual(self.header(), before)
        mtime, data = self.file_state()
        jobs = self.write_jobs("dry.json", [self.job(9, ats_match=50)])
        code, out = self.run_ops("append", "--tracker", self.tracker, "--jobs", jobs, "--dry-run")
        self.assertEqual((code, out["columns_added"], out["dry_run"]), (0, self.OPTIONAL, True))
        self.assertEqual(self.file_state(), (mtime, data))

    def test_append_rejects_bad_ats_match_without_writing(self) -> None:
        mtime, data = self.file_state()
        for bad in (101, -1, 87.5, "high", True):
            jobs = self.write_jobs("bad.json", [self.job(1), self.job(2, ats_match=bad)])
            with redirect_stderr(io.StringIO()):
                code, _ = self.run_ops("append", "--tracker", self.tracker, "--jobs", jobs)
            self.assertEqual(code, 2, bad)
        self.assertEqual(self.file_state(), (mtime, data))

    def test_shortlist_orders_unmarked_rows_and_excludes_marked(self) -> None:
        jobs = [
            self.job(1, tier="A", fit=80, ats_match=70, posted="2026-10-01", apply_method="External"),
            self.job(2, tier="B", fit=95, ats_match=99, posted="2026-10-06"),   # B ranks after every A
            self.job(3, tier="A", fit=60, ats_match=90, posted="2026-10-01"),   # A, best ATS
            self.job(4, tier="A", fit=70, ats_match=90, posted="2026-10-01"),   # same ATS, better fit
            self.job(5, tier="A", fit=70, ats_match=90, posted="2026-10-05"),   # same fit, newer
            self.job(6, tier="C", fit=99),
            self.job(7, tier="A", fit=99, ats_match=99, posted="2026-10-06"),   # approved -> excluded
            self.job(8, tier="A", fit=99, ats_match=99),                        # rejected -> excluded
            self.job(9, tier="A", fit=99, ats_match=99),                        # later -> excluded
            self.job(10, tier="A", fit=99, ats_match=99),                       # unrecognised mark -> excluded
            self.job(11, tier="A", fit=50, ats_match=70, posted="2026-10-03"),  # ties row 1's ATS, lower fit
            self.job(12, fit=99, ats_match=99),                                 # no tier -> last
            self.job(13, tier="A", fit=80, posted="2026-10-06"),                # A without ATS after A with ATS
            self.job(14, tier="B", fit=10, ats_match=20),                       # FALSE counts as unmarked
        ]
        self.run_ops("append", "--tracker", self.tracker, "--jobs", self.write_jobs("sl.json", jobs))
        self.mark({"Co7": "☑ Approve", "Co8": "✖ Reject", "Co9": "⏸ Later", "Co10": "yes", "Co14": False})
        mtime, data = self.file_state()
        code, out = self.run_ops("shortlist", "--tracker", self.tracker, "--size", "20")
        self.assertEqual(code, 0)
        self.assertEqual([x["company"] for x in out],
                         ["Co5", "Co4", "Co3", "Co1", "Co11", "Co13", "Co2", "Co14", "Co6", "Co12"])
        self.assertEqual(self.file_state(), (mtime, data))  # read-only
        first = out[0]
        self.assertEqual((first["tier"], first["fit"], first["ats_match"], first["posted"]), ("A", 70, 90, "2026-10-05"))
        self.assertEqual(set(first), {"row", "num", "company", "title", "link", "tier", "fit", "ats_match", "posted",
                                      "apply_method"})
        self.assertEqual(out[3]["apply_method"], "External")
        _, top = self.run_ops("shortlist", "--tracker", self.tracker, "--size", "3")
        self.assertEqual([x["company"] for x in top], ["Co5", "Co4", "Co3"])
        with redirect_stderr(io.StringIO()):
            self.assertEqual(self.run_ops("shortlist", "--tracker", self.tracker, "--size", "0")[0], 2)

    def test_shortlist_on_tracker_without_optional_columns(self) -> None:
        jobs = [self.job(1, tier="B", fit=90, posted="2026-10-06"), self.job(2, tier="A", fit=50, posted="2026-10-01"),
                self.job(3, tier="A", fit=50, posted="2026-10-04")]
        self.run_ops("append", "--tracker", self.tracker, "--jobs", self.write_jobs("legacy.json", jobs))
        self.assertNotIn("ATS match %", self.header())
        _, out = self.run_ops("shortlist", "--tracker", self.tracker, "--size", "5")
        self.assertEqual([x["company"] for x in out], ["Co3", "Co2", "Co1"])
        self.assertEqual([x["ats_match"] for x in out], [None, None, None])

    def posted_fixture(self) -> None:
        """Rows for expire, reference date 2026-10-07 and --days 14 (rows older than 2026-09-23 expire)."""
        jobs = [
            self.job(1, fit=70, pay="USD 5000", posted="2026-09-01"),           # 36 days -> expires
            self.job(2, posted="2026-09-23"),                                   # exactly 14 days -> kept
            self.job(3, posted="2026-09-22"),                                   # 15 days -> expires
            self.job(4, posted="2026-10-05"),                                   # fresh
            self.job(5, posted="2026-08-01"),                                   # old but approved
            self.job(6, posted="2026-08-02"),                                   # old but rejected
            self.job(7, posted="2026-08-03"),                                   # old but parked
            self.job(8),                                                        # no Posted date
            self.job(9, posted="3 days ago"),                                   # unreadable date
            self.job(10, posted="2026-08-04"),                                  # old, spreadsheet date cell
            self.job(11, posted="2026-08-05"),                                  # old, unrecognised owner mark
            self.job(12, posted="2026-10-30"),                                  # future date -> kept
        ]
        self.run_ops("append", "--tracker", self.tracker, "--jobs", self.write_jobs("exp.json", jobs),
                     "--note", "scan note")
        self.mark({"Co5": "☑ Approve", "Co6": "✖ Reject", "Co7": "⏸ Later", "Co11": "applied by hand"})

        def set_date(wb, col):
            ws = wb["For Approval"]
            for r in range(2, ws.max_row + 1):
                if ws.cell(r, col["Company"]).value == "Co10":
                    ws.cell(r, col["Posted"]).value = dt.datetime(2026, 8, 4, 9, 30)
        self.edit(set_date)

    def test_expire_dry_run_writes_nothing_then_real_run_moves_only_unmarked_stale_rows(self) -> None:
        self.posted_fixture()
        mtime, data = self.file_state()
        args = ("expire", "--tracker", self.tracker, "--days", "14", "--today", "2026-10-07")
        code, out = self.run_ops(*args, "--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(out["dry_run"])
        self.assertEqual([x["company"] for x in out["expired"]], ["Co1", "Co3", "Co10"])
        self.assertEqual([x["age_days"] for x in out["expired"]], [36, 15, 64])
        self.assertEqual(out["reason"], "Expired unreviewed (14 days)")
        self.assertEqual(out["kept_marked"], 4)
        self.assertEqual([x["company"] for x in out["skipped_undated"]], ["Co8", "Co9"])
        self.assertEqual(self.file_state(), (mtime, data))  # dry run: no write, mtime unchanged
        self.assertEqual(out["mtime"], mtime)

        backups = self.dir / "bak"
        code, out = self.run_ops(*args, "--expect-mtime", str(out["mtime"]), "--backup-dir", str(backups))
        self.assertEqual(code, 0)
        self.assertFalse(out["dry_run"])
        self.assertEqual(out["count"], 3)
        self.assertEqual(out["mtime"], Path(self.tracker).stat().st_mtime)
        self.assertEqual(len(list(backups.glob("tracker.bak-*.xlsx"))), 1)
        fa = self.rows_by_company()
        self.assertEqual(sorted(fa), ["Co11", "Co12", "Co2", "Co4", "Co5", "Co6", "Co7", "Co8", "Co9"])
        self.assertEqual(fa["Co5"]["Approve ☐"], "☑ Approve")  # marked rows untouched
        self.assertEqual(fa["Co6"]["Approve ☐"], "✖ Reject")
        self.assertEqual(fa["Co7"]["Approve ☐"], "⏸ Later")
        self.assertEqual(fa["Co11"]["Approve ☐"], "applied by hand")
        ex = self.rows_by_company("Excluded")
        self.assertEqual(sorted(ex), ["Co1", "Co10", "Co3"])
        self.assertEqual(ex["Co1"]["Reason"], "Expired unreviewed (14 days)")
        self.assertEqual((ex["Co1"]["Title"], ex["Co1"]["Job link"], ex["Co1"]["Fit"], ex["Co1"]["Pay"]),
                         ("Role 1", "https://jobs.example/view/1", 70, "USD 5000"))
        sm = self.rows_by_company("Skill Map")
        self.assertEqual(sm["Co1"]["Bucket"], "Excluded")
        self.assertEqual(sm["Co5"]["Bucket"], "For Approval")
        # moved rows are now known to dedup, and a run with nothing left to expire does not rewrite the file
        _, known = self.run_ops("known", "--tracker", self.tracker)
        self.assertIn("https://jobs.example/view/1", known["ids"])
        mtime2, data2 = self.file_state()
        code, out = self.run_ops(*args)
        self.assertEqual((code, out["count"], out["expired"]), (0, 0, []))
        self.assertEqual(self.file_state(), (mtime2, data2))

    def test_expire_expect_mtime_mismatch_aborts_and_locked_file_exits_4(self) -> None:
        self.posted_fixture()
        mtime, data = self.file_state()
        args = ("expire", "--tracker", self.tracker, "--days", "14", "--today", "2026-10-07")
        with redirect_stderr(io.StringIO()):
            code, _ = self.run_ops(*args, "--expect-mtime", "1")
            self.assertEqual(code, 3)
            code, _ = self.run_ops(*args, "--dry-run", "--expect-mtime", "1")  # the guard applies to dry runs too
            self.assertEqual(code, 3)
            self.assertEqual(self.file_state(), (mtime, data))
            with mock.patch.object(self.ops.os, "replace", side_effect=PermissionError("locked")):
                code, _ = self.run_ops(*args, "--expect-mtime", str(mtime))
            self.assertEqual(code, 4)
            self.assertEqual(self.file_state(), (mtime, data))
            self.assertEqual(list(self.dir.glob("*.tmp-tracker-ops")), [])
            for bad in (["--days", "-1"], ["--today", "07/10/2026"]):
                code, _ = self.run_ops("expire", "--tracker", self.tracker, "--days", "14", *bad)
                self.assertEqual(code, 2)

    def test_parse_posted_formats(self) -> None:
        pp = self.ops.parse_posted
        d = dt.date(2026, 9, 25)
        for ok in ("2026-09-25", "2026-09-25T10:15:00Z", "2026/09/25", "2026-9-25", "25/09/2026", "09/25/2026",
                   "Sep 25, 2026", "25 September 2026", dt.date(2026, 9, 25), dt.datetime(2026, 9, 25, 8, 0)):
            self.assertEqual(pp(ok), d, ok)
        for unknown in (None, "", "3 days ago", "05/09/2026", "2026-13-45", "yesterday"):
            self.assertIsNone(pp(unknown), unknown)

    # --- set ---------------------------------------------------------------------------------------------------

    LINK1, LINK2 = "https://jobs.example/view/1", "https://jobs.example/view/2"

    def set_args(self, link, column, value, *extra) -> tuple:
        return ("set", "--tracker", self.tracker, "--link", link, "--column", column, "--value", value, *extra)

    def run_refused(self, *args):
        """Run a write that must fail: returns (exit code, stderr) after checking the file was not touched."""
        before = self.file_state()
        err = io.StringIO()
        with redirect_stderr(err):
            code, out = self.run_ops(*args)
        self.assertIsNone(out)
        self.assertEqual(self.file_state(), before)
        self.assertEqual(list(self.dir.glob("*.tmp-tracker-ops")), [])
        return code, err.getvalue()

    def seed_two_rows(self) -> None:
        jobs = [self.job(1, tier="A", fit=80, apply_method="External"), self.job(2, tier="B", fit=70)]
        path = self.write_jobs("two.json", jobs)
        self.assertEqual(self.run_ops("append", "--tracker", self.tracker, "--jobs", path)[0], 0)

    def test_set_apply_kit_on_existing_for_approval_row_adds_the_column(self) -> None:
        self.seed_two_rows()
        self.mark({"Co1": "☑ Approve"})
        before = self.header()
        self.assertNotIn("Apply kit", before)
        mtime, _ = self.file_state()
        backups = self.dir / "bak"
        code, out = self.run_ops(*self.set_args(self.LINK1, "Apply kit", "  kits/2026-10-07-co1  "),
                                 "--expect-mtime", str(mtime), "--backup-dir", str(backups))
        self.assertEqual(code, 0)
        self.assertEqual((out["sheet"], out["row"], out["column"], out["value"], out["previous"], out["column_added"],
                          out["dry_run"]), ("For Approval", 2, "Apply kit", "kits/2026-10-07-co1", None, True, False))
        self.assertEqual(out["mtime"], Path(self.tracker).stat().st_mtime)
        self.assertEqual(len(list(backups.glob("tracker.bak-*.xlsx"))), 1)
        self.assertEqual(self.header(), before + ["Apply kit"])  # added last, nothing reordered
        rows = self.rows_by_company()
        self.assertEqual(rows["Co1"]["Apply kit"], "kits/2026-10-07-co1")
        self.assertIsNone(rows["Co2"]["Apply kit"])
        self.assertEqual((rows["Co1"]["Approve ☐"], rows["Co1"]["Fit score"], rows["Co2"]["Approve ☐"]),
                         ("☑ Approve", 80, "☐"))  # the owner's mark and every other cell are untouched
        # the returned mtime chains into the next write; the column is reused, a link variant still finds the row
        code, out = self.run_ops(*self.set_args(self.LINK1 + "/?utm=x", "Apply kit", "kits/co1-v2"),
                                 "--expect-mtime", str(out["mtime"]))
        self.assertEqual((code, out["previous"], out["column_added"]), (0, "kits/2026-10-07-co1", False))
        self.assertEqual(self.header(), before + ["Apply kit"])
        self.assertEqual(self.rows_by_company()["Co1"]["Apply kit"], "kits/co1-v2")

    def test_set_allowed_columns_validation_and_text_values(self) -> None:
        self.seed_two_rows()
        code, out = self.run_ops(*self.set_args(self.LINK2, "ats match %", "87%"))
        self.assertEqual((code, out["column"], out["value"]), (0, "ATS match %", 87))
        self.assertIsInstance(self.rows_by_company()["Co2"]["ATS match %"], int)
        for column, value in (("Missing keywords", "Kafka; Spring"), ("Decision notes", "call recruiter first"),
                              ("Next action", "send kit"), ("Notes", "=HYPERLINK(\"http://x.example\",\"x\")")):
            code, out = self.run_ops(*self.set_args(self.LINK2, column, value))
            self.assertEqual((code, out["column"]), (0, column))
        row = self.rows_by_company()["Co2"]
        self.assertEqual((row["Missing keywords"], row["Decision notes"], row["Next action"]),
                         ("Kafka; Spring", "call recruiter first", "send kit"))
        self.assertEqual(row["Notes"], "=HYPERLINK(\"http://x.example\",\"x\")")  # text, never a live formula
        ws = openpyxl.load_workbook(self.tracker)["For Approval"]
        notes = next(c for c in ws[1] if c.value == "Notes")
        self.assertEqual(ws.cell(3, notes.column).data_type, "s")
        for bad in ("101", "-1", "87.5", "high", "", "   "):
            code, err = self.run_refused(*self.set_args(self.LINK2, "ATS match %", bad))
            self.assertEqual(code, 2, bad)
        code, err = self.run_refused(*self.set_args(self.LINK2, "Apply kit", " "))
        self.assertEqual((code, "empty" in err), (2, True))

    def test_set_refuses_approval_key_and_other_columns_and_leaves_file_unchanged(self) -> None:
        self.seed_two_rows()
        for column in ("Approve ☐", "Approve", "approve?", "Approved", "#", "Job link", "job  link", "Company", "Title"):
            code, err = self.run_refused(*self.set_args(self.LINK1, column, "x"))
            self.assertEqual(code, 2, column)
            self.assertIn("will not write", err, column)
        for column in ("Tier", "Fit score", "Posted", "Nope"):  # not on the allow-list
            code, err = self.run_refused(*self.set_args(self.LINK1, column, "x"))
            self.assertEqual(code, 2, column)
            self.assertIn("cannot be set", err, column)
        self.assertEqual(self.rows_by_company()["Co1"]["Approve ☐"], "☐")

    def test_set_link_not_found_or_empty_exits_2(self) -> None:
        self.seed_two_rows()
        code, err = self.run_refused(*self.set_args("https://jobs.example/view/999", "Apply kit", "kits/x"))
        self.assertEqual((code, "not found" in err), (2, True))
        code, err = self.run_refused(*self.set_args(self.LINK1, "Apply kit", "kits/x", "--sheet", "Applied"))
        self.assertEqual((code, "not found in sheet Applied" in err), (2, True))  # the row lives in For Approval
        self.assertEqual(self.run_refused(*self.set_args("  ", "Apply kit", "kits/x"))[0], 2)
        self.assertEqual(self.run_refused(*self.set_args(self.LINK1, "Apply kit", "kits/x", "--sheet", "Summary"))[0], 2)
        self.assertEqual(self.run_refused(*self.set_args(self.LINK1, "Apply kit", "kits/x", "--sheet", "Nope"))[0], 2)
        missing = str(self.dir / "missing.xlsx")
        with redirect_stderr(io.StringIO()):
            code, _ = self.run_ops("set", "--tracker", missing, "--link", self.LINK1, "--column", "Notes", "--value", "x")
        self.assertEqual(code, 2)

    def test_set_expect_mtime_mismatch_and_locked_file(self) -> None:
        self.seed_two_rows()
        mtime, data = self.file_state()
        args = self.set_args(self.LINK1, "Apply kit", "kits/co1")
        self.assertEqual(self.run_refused(*args, "--expect-mtime", "1")[0], 3)
        self.assertEqual(self.run_refused(*args, "--dry-run", "--expect-mtime", "1")[0], 3)  # the guard covers dry runs
        self.assertEqual(self.run_refused(*args, "--expect-mtime", str(mtime + 5))[0], 3)
        with mock.patch.object(self.ops.os, "replace", side_effect=PermissionError("locked")):
            self.assertEqual(self.run_refused(*args, "--expect-mtime", str(mtime))[0], 4)
        self.assertNotIn("Apply kit", self.header())
        # a file edited by the owner between the load and the write is caught by the re-check before the replace
        real_load = self.ops.openpyxl.load_workbook

        def load_then_owner_saves(*a, **kw):
            wb = real_load(*a, **kw)
            os.utime(self.tracker, (mtime + 60, mtime + 60))
            return wb
        with mock.patch.object(self.ops.openpyxl, "load_workbook", side_effect=load_then_owner_saves), \
                redirect_stderr(io.StringIO()):
            code, _ = self.run_ops(*args, "--expect-mtime", str(mtime))
        self.assertEqual(code, 3)
        self.assertEqual(self.file_state()[1], data)
        self.assertEqual(list(self.dir.glob("*.tmp-tracker-ops")), [])

    def test_set_link_in_two_tabs_needs_sheet(self) -> None:
        self.seed_two_rows()

        def add_applied_copy(wb, col):
            wb["Applied"].append([1, "Co1", "Role 1", self.LINK1 + "/"])  # same job, different spelling of the link
        self.edit(add_applied_copy)
        applied_header = self.header("Applied")
        code, err = self.run_refused(*self.set_args(self.LINK1, "Next action", "ping recruiter"))
        self.assertEqual(code, 2)
        self.assertIn("ambiguous", err)
        self.assertIn("For Approval row 2", err)
        self.assertIn("Applied row 2", err)
        self.assertIn("--sheet", err)
        code, out = self.run_ops(*self.set_args(self.LINK1, "Next action", "ping recruiter", "--sheet", "Applied"))
        self.assertEqual((code, out["sheet"], out["row"], out["column_added"]), (0, "Applied", 2, False))
        self.assertEqual(self.rows_by_company("Applied")["Co1"]["Next action"], "ping recruiter")
        code, out = self.run_ops(*self.set_args(self.LINK1, "Apply kit", "kits/co1", "--sheet", "For Approval"))
        self.assertEqual((code, out["sheet"], out["column_added"]), (0, "For Approval", True))
        self.assertEqual(self.header("Applied"), applied_header)  # the other tab did not gain a column
        # a link that appears in one tab only is found without --sheet, and its tab gains the missing column
        code, out = self.run_ops(*self.set_args(self.LINK2, "Notes", "second row"))
        self.assertEqual((code, out["sheet"], out["column_added"]), (0, "For Approval", True))
        # a duplicate inside the chosen tab is ambiguous too
        self.edit(lambda wb, col: wb["For Approval"].append(
            [9, "☐", None, None, None, "Co1 again", "Role 1", self.LINK1]))
        code, err = self.run_refused(*self.set_args(self.LINK1, "Apply kit", "kits/other", "--sheet", "For Approval"))
        self.assertEqual((code, "remove the duplicate row first" in err), (2, True))

    def test_set_dry_run_reports_without_writing(self) -> None:
        self.seed_two_rows()
        mtime, data = self.file_state()
        code, out = self.run_ops(*self.set_args(self.LINK1, "Apply kit", "kits/co1"), "--dry-run")
        self.assertEqual((code, out["dry_run"], out["column_added"], out["row"]), (0, True, True, 2))
        self.assertEqual(self.file_state(), (mtime, data))
        self.assertEqual(out["mtime"], mtime)

    def test_help_lists_new_commands(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            self.ops.main(["--help"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn("shortlist", buf.getvalue())
        self.assertIn("expire", buf.getvalue())
        self.assertRegex(buf.getvalue(), r"(?m)^\s+set\s+set one cell")
        buf = io.StringIO()
        with redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
            self.ops.main(["set", "--help"])
        self.assertEqual(cm.exception.code, 0)
        for flag in ("--tracker", "--link", "--column", "--value", "--sheet", "--expect-mtime", "--backup-dir"):
            self.assertIn(flag, buf.getvalue())

    # --- hyperlinks survive row deletes; repair removes orphan rows --------------------------------------------

    def written_link_refs(self, sheet="For Approval") -> list:
        """Hyperlink refs exactly as they sit in the saved sheet XML (a reload would already hide stale ones)."""
        idx = openpyxl.load_workbook(self.tracker).sheetnames.index(sheet) + 1
        with zipfile.ZipFile(self.tracker) as z:
            xml = z.read(f"xl/worksheets/sheet{idx}.xml").decode("utf-8")
        return sorted(re.findall(r"<hyperlink\b[^>]*?\bref=\"([A-Z]+\d+)\"", xml))

    def orphan_rows(self, sheet) -> list:
        ws = openpyxl.load_workbook(self.tracker)[sheet]
        h = {c.value: c.column for c in ws[1] if c.value}
        return [r for r in range(2, ws.max_row + 1)
                if ws.cell(r, h["Company"]).value in (None, "") and ws.cell(r, h["Title"]).value in (None, "")
                and any(c.value not in (None, "") for c in ws[r])]

    def link_fixture(self, count=8) -> list:
        """Append Co1..Co<count> to For Approval and give every Job link cell a hyperlink to its own value."""
        links = [f"https://jobs.example/view/{n}" for n in range(1, count + 1)]
        jobs = [self.job(n) for n in range(1, count + 1)]
        self.assertEqual(self.run_ops("append", "--tracker", self.tracker, "--jobs",
                                      self.write_jobs("links.json", jobs))[0], 0)

        def link_up(wb, col):
            ws = wb["For Approval"]
            for r in range(2, ws.max_row + 1):
                cell = ws.cell(r, col["Job link"])
                if cell.value:
                    cell.hyperlink = cell.value
        self.edit(link_up)
        return links

    def assert_links_belong_to_rows(self, sheet, expected_companies) -> None:
        wb = openpyxl.load_workbook(self.tracker)
        ws = wb[sheet]
        h = {c.value: c.column for c in ws[1] if c.value}
        rows = [r for r in range(2, ws.max_row + 1) if ws.cell(r, h["Company"]).value not in (None, "")]
        self.assertEqual([ws.cell(r, h["Company"]).value for r in rows], expected_companies)
        self.assertEqual(rows, list(range(2, 2 + len(rows))))  # dense, no gaps
        self.assertEqual(self.orphan_rows(sheet), [])
        col = openpyxl.utils.get_column_letter(h["Job link"])
        for r in rows:
            cell = ws.cell(r, h["Job link"])
            if sheet == "For Approval":
                self.assertIsNotNone(cell.hyperlink, f"{sheet} row {r} lost its link")
            if cell.hyperlink is not None:
                self.assertEqual(cell.hyperlink.target, cell.value, f"{sheet} row {r} carries another row's link")
                self.assertEqual(cell.hyperlink.ref, cell.coordinate)
        if sheet == "For Approval":
            self.assertEqual(self.written_link_refs(sheet), sorted(f"{col}{r}" for r in rows))
        # nothing at all below the last real row except the formatting-only rows openpyxl keeps
        for r in range(rows[-1] + 1 if rows else 2, ws.max_row + 1):
            self.assertTrue(all(c.value in (None, "") for c in ws[r]), f"{sheet} row {r} holds stray values")

    def test_move_to_excluded_keeps_hyperlinks_on_their_own_rows(self) -> None:
        links = self.link_fixture(8)
        self.assertEqual(self.written_link_refs(), [f"H{r}" for r in range(2, 10)])
        _, state = self.run_ops("known", "--tracker", self.tracker)
        mtime = state["mtime"]
        moved = [4, 8, 1, 5, 2]  # middle, last data row, first data row, middle, first again
        for n in moved:
            code, out = self.run_ops("move", "--tracker", self.tracker, "--link", links[n - 1], "--to", "Excluded",
                                     "--detail", f"reason {n}", "--expect-mtime", str(mtime),
                                     "--backup-dir", str(self.dir / "bak"))
            self.assertEqual(code, 0)
            mtime = out["mtime"]
            self.assert_links_belong_to_rows(
                "For Approval", [f"Co{k}" for k in range(1, 9) if k not in moved[: moved.index(n) + 1]])
        self.assert_links_belong_to_rows("For Approval", ["Co3", "Co6", "Co7"])
        ex = self.rows_by_company("Excluded")
        self.assertEqual(sorted(ex), sorted(f"Co{n}" for n in moved))
        for n in moved:
            self.assertEqual(ex[f"Co{n}"]["Job link"], links[n - 1])
            self.assertTrue(ex[f"Co{n}"]["Reason"].startswith(f"reason {n}"), ex[f"Co{n}"]["Reason"])
        self.assert_links_belong_to_rows("Excluded", [f"Co{n}" for n in moved])

    def test_expire_keeps_hyperlinks_on_their_own_rows(self) -> None:
        stale = {1: "2026-09-01", 3: "2026-09-02", 6: "2026-09-03"}
        links = self.link_fixture(6)
        self.edit(lambda wb, col: [
            setattr(wb["For Approval"].cell(r, col["Posted"]), "value", stale.get(r - 1, "2026-10-06"))
            for r in range(2, 8)])
        code, out = self.run_ops("expire", "--tracker", self.tracker, "--days", "14", "--today", "2026-10-07")
        self.assertEqual((code, out["count"]), (0, 3))
        self.assert_links_belong_to_rows("For Approval", ["Co2", "Co4", "Co5"])
        ex = self.rows_by_company("Excluded")
        self.assertEqual({k: v["Job link"] for k, v in ex.items()}, {f"Co{n}": links[n - 1] for n in stale})

    def test_save_reanchors_hyperlinks_in_every_sheet_after_delete_rows(self) -> None:
        """The fix lives in Tracker.save(), so any code path that deletes rows benefits, in any worksheet."""
        self.link_fixture(5)

        def link_gigs(wb, col):
            ws = wb["Side Gigs"]
            for i in range(1, 5):
                ws.cell(1 + i, 2).value = f"Platform{i}"
                ws.cell(1 + i, 3).hyperlink = f"https://gigs.example/p{i}"
        self.edit(link_gigs)
        t = self.ops.Tracker(self.tracker)
        t.wb["For Approval"].delete_rows(2, 1)
        t.wb["For Approval"].delete_rows(5, 1)
        t.wb["Side Gigs"].delete_rows(3, 2)
        stale = [c.hyperlink.ref for c in t.wb["Side Gigs"]["C"] if c.hyperlink]
        self.assertNotEqual(stale, [f"C{r}" for r in range(2, 2 + len(stale))])  # the bug openpyxl leaves behind
        t.save()
        self.assertEqual(self.written_link_refs("Side Gigs"), ["C2", "C3"])
        self.assertEqual(self.written_link_refs("For Approval"), ["H2", "H3", "H4"])
        wb = openpyxl.load_workbook(self.tracker)
        gigs = [(wb["Side Gigs"].cell(r, 3).value, wb["Side Gigs"].cell(r, 3).hyperlink.target) for r in range(2, 4)]
        self.assertEqual(gigs, [("https://gigs.example/p1",) * 2, ("https://gigs.example/p4",) * 2])
        self.assertIsNone(wb["Side Gigs"].cell(4, 3).value)
        self.assert_links_belong_to_rows("For Approval", ["Co2", "Co3", "Co4"])

    ORPHAN_ROWS = {"For Approval": [9, 10, 12], "Applied": [3], "Excluded": [4]}
    NO_LINKS_FIXED = {"For Approval": [], "Applied": [], "Interviewing": [], "Closed": [], "Excluded": []}

    def orphan_fixture(self) -> None:
        """Pipeline tabs polluted the way the old hyperlink bug left them, plus rows that must never be removed."""
        self.link_fixture(6)

        def pollute(wb, col):
            fa, ap, ex = wb["For Approval"], wb["Applied"], wb["Excluded"]
            junk = "https://jobs.example/view/6"
            for r in (9, 10):                      # link-only rows with a hyperlink, as in the corrupted tracker
                fa.cell(r, col["Job link"]).hyperlink = junk
            fa.cell(12, col["Decision notes"]).value = "stray note"   # orphan after a blank row
            fa.cell(13, col["Company"]).value = "OnlyCompany"         # keep: has a Company
            fa.cell(14, col["Title"]).value = "Only title"            # keep: has a Title
            ha = {c.value: c.column for c in ap[1] if c.value}
            for r, (co, ti) in {2: ("AppCo", "Dev"), 4: ("AppCo2", "Dev2")}.items():
                ap.cell(r, ha["Company"]).value, ap.cell(r, ha["Title"]).value = co, ti
                ap.cell(r, ha["Job link"]).hyperlink = f"https://jobs.example/applied/{r}"
            ap.cell(3, ha["Job link"]).hyperlink = "https://jobs.example/applied/2"
            hx = {c.value: c.column for c in ex[1] if c.value}
            for r in (2, 3, 5):
                ex.cell(r, hx["Company"]).value, ex.cell(r, hx["Title"]).value = f"Ex{r}", f"ExRole{r}"
                ex.cell(r, hx["Job link"]).hyperlink = f"https://jobs.example/excluded/{r}"
            ex.cell(4, hx["Reason"]).value = "orphan reason"
            sm = wb["Skill Map"]
            sm.cell(2, 4).value = "SkillWithoutJob"                    # not a pipeline tab: never repaired
        self.edit(pollute)

    def test_repair_dry_run_reports_orphans_and_writes_nothing(self) -> None:
        self.orphan_fixture()
        before = self.file_state()
        code, out = self.run_ops("repair", "--tracker", self.tracker, "--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(out["dry_run"])
        self.assertEqual({k: v for k, v in out.items() if k not in ("dry_run", "mtime", "links_fixed")},
                         {"For Approval": [9, 10, 12], "Applied": [3], "Interviewing": [], "Closed": [],
                          "Excluded": [4]})
        self.assertEqual(out["links_fixed"], self.NO_LINKS_FIXED)
        self.assertEqual(out["mtime"], before[0])
        self.assertEqual(self.file_state(), before)

    def test_repair_removes_only_orphan_rows_and_keeps_links_anchored(self) -> None:
        self.orphan_fixture()
        self.assertEqual(self.orphan_rows("For Approval"), [9, 10, 12])
        mtime = self.file_state()[0]
        bak = self.dir / "bak"
        code, out = self.run_ops("repair", "--tracker", self.tracker, "--expect-mtime", str(mtime),
                                 "--backup-dir", str(bak))
        self.assertEqual(code, 0)
        self.assertFalse(out["dry_run"])
        self.assertEqual({k: v for k, v in out.items() if k not in ("dry_run", "mtime", "links_fixed")}, {
            "For Approval": self.ORPHAN_ROWS["For Approval"], "Applied": [3], "Interviewing": [], "Closed": [],
            "Excluded": [4]})
        self.assertEqual(out["links_fixed"], self.NO_LINKS_FIXED)  # orphans are deleted, not "fixed"
        self.assertEqual(out["mtime"], Path(self.tracker).stat().st_mtime)
        self.assertEqual(len(list(bak.glob("tracker.bak-*.xlsx"))), 1)
        for sheet in ("For Approval", "Applied", "Interviewing", "Closed", "Excluded"):
            self.assertEqual(self.orphan_rows(sheet), [], sheet)
        wb = openpyxl.load_workbook(self.tracker)
        fa = wb["For Approval"]
        hf = {c.value: c.column for c in fa[1] if c.value}
        # real rows, the Company-only row and the Title-only row are all still there, in order
        self.assertEqual([(fa.cell(r, hf["Company"]).value, fa.cell(r, hf["Title"]).value) for r in range(2, 12)],
                         [(f"Co{n}", f"Role {n}") for n in range(1, 7)] + [(None, None)] * 2 +  # blank rows stay
                         [("OnlyCompany", None), (None, "Only title")])
        for r in range(2, 8):
            self.assertEqual(fa.cell(r, hf["Job link"]).hyperlink.target, f"https://jobs.example/view/{r - 1}")
        self.assertEqual(self.written_link_refs(), [f"H{r}" for r in range(2, 8)])
        self.assertEqual(self.written_link_refs("Applied"), ["D2", "D3"])
        self.assertEqual(self.written_link_refs("Excluded"), ["C2", "C3", "C4"])
        ap, ex = wb["Applied"], wb["Excluded"]
        self.assertEqual([(ap.cell(r, 2).value, ap.cell(r, 4).hyperlink.target) for r in (2, 3)],
                         [("AppCo", "https://jobs.example/applied/2"), ("AppCo2", "https://jobs.example/applied/4")])
        self.assertEqual([(ex.cell(r, 1).value, ex.cell(r, 3).hyperlink.target) for r in (2, 3, 4)],
                         [(f"Ex{n}", f"https://jobs.example/excluded/{n}") for n in (2, 3, 5)])
        self.assertEqual(wb["Skill Map"].cell(2, 4).value, "SkillWithoutJob")
        # a second run finds nothing and does not rewrite the file
        state = self.file_state()
        code, again = self.run_ops("repair", "--tracker", self.tracker)
        self.assertEqual(code, 0)
        self.assertEqual([v for k, v in again.items() if k not in ("dry_run", "mtime", "links_fixed")], [[]] * 5)
        self.assertEqual(again["links_fixed"], self.NO_LINKS_FIXED)
        self.assertEqual(self.file_state(), state)

    def mismatch_fixture(self) -> None:
        """Job link hyperlinks that point at another job, next to ones that must stay as they are."""
        self.link_fixture(4)

        def skew(wb, col):
            fa, ap, ex = wb["For Approval"], wb["Applied"], wb["Excluded"]
            fa.cell(3, col["Job link"]).hyperlink = "https://jobs.example/view/OTHER"   # Co2: points elsewhere
            fa.cell(5, col["Job link"]).hyperlink = "https://jobs.example/view/OTHER"   # Co4: points elsewhere
            ha = {c.value: c.column for c in ap[1] if c.value}
            for r, (value, target) in enumerate([
                    ("https://jobs.example/applied/1", "https://jobs.example/applied/1"),      # matches: untouched
                    ("https://jobs.example/applied/2", "https://jobs.example/applied/9"),      # mismatch: fixed
                    ("see the mail thread", "https://jobs.example/applied/3")], start=2):      # not a URL: untouched
                ap.cell(r, ha["Company"]).value, ap.cell(r, ha["Title"]).value = f"App{r}", f"Dev{r}"
                ap.cell(r, ha["Job link"]).hyperlink = target
                ap.cell(r, ha["Job link"]).value = value
            ap.cell(2, ha["Mail link"]).hyperlink = "https://mail.example/a"            # other column: untouched
            ap.cell(2, ha["Mail link"]).value = "https://mail.example/different"
            hx = {c.value: c.column for c in ex[1] if c.value}
            ex.cell(2, hx["Company"]).value, ex.cell(2, hx["Title"]).value = "Ex2", "ExRole2"
            ex.cell(2, hx["Job link"]).hyperlink = "https://jobs.example/excluded/2"
            ex.cell(2, hx["Job link"]).value = "  HTTPS://jobs.example/excluded/2-fixed "   # padded, case-insensitive http
            gigs = wb["Side Gigs"]
            gigs.cell(2, 3).hyperlink = "https://gigs.example/a"                         # not a pipeline tab
            gigs.cell(2, 3).value = "https://gigs.example/b"
        self.edit(skew)

    def link_targets(self, sheet, column) -> dict:
        ws = openpyxl.load_workbook(self.tracker)[sheet]
        col = {c.value: c.column for c in ws[1] if c.value}[column]
        return {c.coordinate: (c.value, c.hyperlink.target if c.hyperlink else None)
                for c in ws[openpyxl.utils.get_column_letter(col)][1:] if c.value or c.hyperlink}

    def test_repair_dry_run_reports_mismatched_job_links_and_writes_nothing(self) -> None:
        self.mismatch_fixture()
        before = self.file_state()
        code, out = self.run_ops("repair", "--tracker", self.tracker, "--dry-run")
        self.assertEqual(code, 0)
        self.assertTrue(out["dry_run"])
        self.assertEqual(out["links_fixed"], {"For Approval": ["H3", "H5"], "Applied": ["D3"], "Interviewing": [],
                                              "Closed": [], "Excluded": ["C2"]})
        self.assertEqual({k: v for k, v in out.items() if k not in ("dry_run", "mtime", "links_fixed")},
                         {"For Approval": [], "Applied": [], "Interviewing": [], "Closed": [], "Excluded": []})
        self.assertEqual(self.file_state(), before)

    def test_repair_fixes_mismatched_job_link_targets_and_leaves_the_rest(self) -> None:
        self.mismatch_fixture()
        mtime = self.file_state()[0]
        code, out = self.run_ops("repair", "--tracker", self.tracker, "--expect-mtime", str(mtime),
                                 "--backup-dir", str(self.dir / "bak"))
        self.assertEqual(code, 0)
        self.assertFalse(out["dry_run"])
        self.assertEqual(out["links_fixed"], {"For Approval": ["H3", "H5"], "Applied": ["D3"], "Interviewing": [],
                                              "Closed": [], "Excluded": ["C2"]})
        self.assertEqual(out["mtime"], Path(self.tracker).stat().st_mtime)
        self.assertEqual(len(list((self.dir / "bak").glob("tracker.bak-*.xlsx"))), 1)
        fa = self.link_targets("For Approval", "Job link")
        self.assertEqual(fa, {f"H{r}": (f"https://jobs.example/view/{r - 1}",) * 2 for r in range(2, 6)})
        self.assertEqual(self.link_targets("Applied", "Job link"), {
            "D2": ("https://jobs.example/applied/1",) * 2,                        # matching link untouched
            "D3": ("https://jobs.example/applied/2",) * 2,                        # target reset to the text
            "D4": ("see the mail thread", "https://jobs.example/applied/3")})     # not a URL: kept
        # padded value: the target becomes the trimmed text, the cell text itself is not rewritten
        self.assertEqual(self.link_targets("Excluded", "Job link"),
                         {"C2": ("  HTTPS://jobs.example/excluded/2-fixed ", "HTTPS://jobs.example/excluded/2-fixed")})
        self.assertEqual(self.link_targets("Applied", "Mail link"),
                         {"W2": ("https://mail.example/different", "https://mail.example/a")})
        self.assertEqual(self.link_targets("Side Gigs", "Link"),
                         {"C2": ("https://gigs.example/b", "https://gigs.example/a")})
        self.assertEqual(self.written_link_refs("For Approval"), [f"H{r}" for r in range(2, 6)])
        # nothing left to fix: the second run reports nothing and leaves the file alone
        state = self.file_state()
        code, again = self.run_ops("repair", "--tracker", self.tracker)
        self.assertEqual((code, again["links_fixed"]), (0, {**self.NO_LINKS_FIXED}))
        self.assertEqual(self.file_state(), state)

    def test_repair_leaves_a_tracker_with_matching_links_alone(self) -> None:
        self.link_fixture(4)
        state = self.file_state()
        code, out = self.run_ops("repair", "--tracker", self.tracker)
        self.assertEqual((code, out["links_fixed"]), (0, self.NO_LINKS_FIXED))
        self.assertEqual(self.file_state(), state)

    def test_repair_fixes_links_and_removes_orphans_in_one_run(self) -> None:
        self.orphan_fixture()
        self.edit(lambda wb, col: setattr(wb["For Approval"].cell(3, col["Job link"]), "hyperlink",
                                          "https://jobs.example/view/OTHER"))
        code, out = self.run_ops("repair", "--tracker", self.tracker)
        self.assertEqual(code, 0)
        self.assertEqual(out["For Approval"], [9, 10, 12])
        self.assertEqual(out["links_fixed"]["For Approval"], ["H3"])  # orphan rows 9-10 are not reported as fixes
        self.assertEqual(self.orphan_rows("For Approval"), [])
        fa = self.link_targets("For Approval", "Job link")
        self.assertEqual(fa, {f"H{r}": (f"https://jobs.example/view/{r - 1}",) * 2 for r in range(2, 8)})
        self.assertEqual(self.written_link_refs(), sorted(fa))

    def test_mismatched_links_ignores_empty_values_and_internal_links(self) -> None:
        self.link_fixture(3)
        t = self.ops.Tracker(self.tracker)
        ws = t.wb["For Approval"]
        ws["H2"].value = None                     # empty value with a link: orphan removal covers it, not this
        ws["H3"].hyperlink = self.ops.openpyxl.worksheet.hyperlink.Hyperlink(ref="H3", location="Sheet2!A1")
        ws["H4"].value = "https://jobs.example/view/other"
        self.assertEqual([(c.coordinate, url) for c, url in self.ops.mismatched_links(ws)],
                         [("H4", "https://jobs.example/view/other")])
        self.assertEqual(self.ops.mismatched_links(ws, skip_rows={4}), [])

    def test_repair_guards_expect_mtime_and_is_listed_in_help(self) -> None:
        self.orphan_fixture()
        before = self.file_state()
        with redirect_stderr(io.StringIO()):
            code, _ = self.run_ops("repair", "--tracker", self.tracker, "--expect-mtime", "1")
        self.assertEqual(code, 3)
        self.assertEqual(self.file_state(), before)
        buf = io.StringIO()
        with redirect_stdout(buf), self.assertRaises(SystemExit):
            self.ops.main(["repair", "--help"])
        for flag in ("--tracker", "--dry-run", "--expect-mtime", "--backup-dir"):
            self.assertIn(flag, buf.getvalue())
        buf = io.StringIO()
        with redirect_stdout(buf), self.assertRaises(SystemExit):
            self.ops.main(["--help"])
        self.assertRegex(buf.getvalue(), r"(?m)^\s+repair\s+delete orphan rows")


if __name__ == "__main__":
    unittest.main()
