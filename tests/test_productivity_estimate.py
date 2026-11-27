from __future__ import annotations

import contextlib
import csv
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "productivity-impact-estimate" / "scripts" / "productivity_estimate.py"
SPEC = importlib.util.spec_from_file_location("productivity_estimate", SCRIPT)
assert SPEC and SPEC.loader
est = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = est
SPEC.loader.exec_module(est)


def run_main(*argv: str) -> tuple[int, str]:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        code = est.main(list(argv))
    return code, buf.getvalue()


class TotalsTests(unittest.TestCase):
    def test_default_manual_week_is_forty_hours(self) -> None:
        _, summary = est.build(est.load_rows(None))
        self.assertEqual(40.0, summary["manual_week_h"])
        self.assertEqual("ESTIMATE, not a measurement", summary["label"])

    def test_engineering_hours_exclude_meetings(self) -> None:
        _, summary = est.build(est.load_rows(None))
        self.assertEqual(30.0, summary["engineering_hours_per_week"])

    def test_conservative_never_exceeds_likely(self) -> None:
        _, summary = est.build(est.load_rows(None))
        saved = summary["saved_week_h"]
        self.assertLessEqual(saved["conservative"], saved["likely"])

    def test_team_rollups_for_one_five_ten(self) -> None:
        _, summary = est.build(est.load_rows(None))
        self.assertEqual(["1", "5", "10"], list(summary["team"]))
        one = summary["team"]["1"]["saved_week_h"]
        for n in (5, 10):
            got = summary["team"][str(n)]["saved_week_h"]
            self.assertAlmostEqual(one["conservative"] * n, got["conservative"], delta=0.06 * n)
            self.assertAlmostEqual(one["likely"] * n, got["likely"], delta=0.06 * n)
        self.assertEqual(summary["saved_year_h"], summary["team"]["1"]["saved_year_h"])


class RoundingTests(unittest.TestCase):
    def test_half_up_not_bankers(self) -> None:
        self.assertEqual(0.3, est.r(Decimal("0.25")))
        self.assertEqual(0.4, est.r(Decimal("0.35")))
        self.assertEqual(3.0, est.r(Decimal("2.5"), "1"))
        self.assertEqual(4.0, est.r(Decimal("3.5"), "1"))

    def test_single_row_arithmetic(self) -> None:
        rows = [dict(activity="Work", manual_h=10, conservative_pct=10, likely_pct=25, assets="")]
        table, summary = est.build(rows)
        self.assertEqual(1.0, table[0]["saved_h_conservative"])
        self.assertEqual(2.5, table[0]["saved_h_likely"])
        self.assertEqual(9.0, table[0]["toolkit_h_conservative"])
        self.assertEqual(7.5, table[0]["toolkit_h_likely"])
        self.assertEqual(10.0, summary["saved_week_pct_of_baseline"]["conservative"])


class CliTests(unittest.TestCase):
    def test_out_writes_csv_one_row_per_activity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "estimate.csv"
            code, text = run_main("--out", str(out))
            self.assertEqual(0, code)
            self.assertIn("ESTIMATE, not a measurement", text)
            with out.open(newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
        self.assertEqual(len(est.DEFAULT_ROWS), len(rows))
        self.assertEqual("manual_h", list(rows[0])[1])

    def test_json_flag_prints_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, text = run_main("--out", str(Path(tmp) / "e.csv"), "--json")
        self.assertEqual(0, code)
        self.assertEqual(40.0, json.loads(text)["manual_week_h"])

    def test_output_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.csv", Path(tmp) / "b.csv"
            _, ta = run_main("--out", str(a), "--json")
            _, tb = run_main("--out", str(b), "--json")
            self.assertEqual(ta, tb)
            self.assertEqual(a.read_bytes(), b.read_bytes())

    def test_rows_override_replaces_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            rows = Path(tmp) / "rows.json"
            rows.write_text(json.dumps([
                dict(activity="Coding", manual_h=20, conservative_pct=5, likely_pct=10),
                dict(activity="Meetings", manual_h=20, conservative_pct=0, likely_pct=0),
            ]), encoding="utf-8")
            code, text = run_main("--out", str(Path(tmp) / "e.csv"), "--rows", str(rows), "--json")
        summary = json.loads(text)
        self.assertEqual(0, code)
        self.assertEqual(40.0, summary["manual_week_h"])
        self.assertEqual(20.0, summary["engineering_hours_per_week"])
        self.assertEqual(2.0, summary["saved_week_h"]["likely"])

    def test_rows_validation_exits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps([dict(activity="x", manual_h=1)]), encoding="utf-8")
            with self.assertRaises(SystemExit):
                est.load_rows(str(bad))
            bad.write_text(json.dumps([dict(activity="x", manual_h=1, conservative_pct=30, likely_pct=10)]),
                           encoding="utf-8")
            with self.assertRaises(SystemExit):
                est.load_rows(str(bad))


if __name__ == "__main__":
    unittest.main()
