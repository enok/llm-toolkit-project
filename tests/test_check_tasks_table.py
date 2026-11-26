from __future__ import annotations

import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_tasks_table.py"
VALID_FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tasks_table_valid.md"
SPEC = importlib.util.spec_from_file_location("check_tasks_table", SCRIPT)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = checker
SPEC.loader.exec_module(checker)

COLUMNS = list(checker.COLUMNS)
MANIFEST_FIELDS = {
    "Route": "`INTENTS` row \"build\" → `example-skill`",
    "Rules in force": "`example-rule`",
    "Agents": "`example-agent` (reviewer lane), root",
    "Helpers": "`scripts/example_check.py`",
}


def manifest(omit=(), extra=""):
    parts = [f"{key}: {value}" for key, value in MANIFEST_FIELDS.items() if key not in omit]
    return "Requested by: tester · " + " · ".join(parts) + extra


MANIFEST = manifest()


def table_row(cells):
    return "| " + " | ".join(cells) + " |"


def row(num, wave, status, tokens, sla, remaining, assets="skill:example-skill · script:scripts/example_check.py"):
    return table_row([
        str(num), wave, f"Task {num}", assets, "standard: sonnet / medium", status,
        "first-pass; notes/out.md", "—", "—", tokens, "0", sla, remaining,
    ])


def footer(
    count=4, tokens="~34.5K", sla="00:40", open_count=2, remaining="00:12",
    path="3 → 4", path_sla="00:12",
):
    def line(label, third, tok="", sla_cell="", rem=""):
        return table_row([label, "", str(third), "", "", "", "", "", "", tok, "", sla_cell, rem])

    return [
        line("Total (all tasks)", count, tokens, sla),
        line("Total (remaining/not completed)", open_count, rem=remaining),
        line("Remaining SLA to complete all tasks (critical path)", path, rem=path_sla),
    ]


def default_rows():
    return [
        row(1, "W0", "completed", "10.0K", "00:05", "00:00"),
        row(2, "W1", "completed", "20.5K", "00:20", "00:00"),
        row(3, "W2", "running (dispatched 20:06)", "~4.0K", "00:10", "00:07"),
        row(4, "W3", "pending", "—", "00:05", "00:05"),
    ]


def ledger(rows=None, footers=None, header=None, manifest=MANIFEST, name="Session A"):
    rows = default_rows() if rows is None else rows
    footers = footer() if footers is None else footers
    header = COLUMNS if header is None else header
    lines = [f"## Session: {name} (2026-10-27) — generic ledger", manifest, ""]
    lines.append(table_row(header))
    lines.append(table_row(["---"] * len(header)))
    lines.extend(rows)
    lines.extend(footers)
    return "\n".join(lines) + "\n"


LEGACY = (
    "## Session: Old\n\n"
    "| # | Task | Model/Effort | Status | Evidence |\n"
    "| --- | --- | --- | --- | --- |\n"
    "| 1 | Do the thing | light | completed | notes |\n"
)


class CheckTasksTableTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_check(self, text, *args, name="TASKS_TABLE.md"):
        path = self.dir / name
        path.write_text(text, encoding="utf-8", newline="\n")
        return self.run_path(path, *args)

    def run_path(self, path, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = checker.main([str(path), *args])
        return code, buf.getvalue()

    def assert_fails(self, text, *needles, args=()):
        code, out = self.run_check(text, *args)
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL", out)
        for needle in needles:
            self.assertIn(needle, out)
        return out

    # -- passing inputs

    def test_valid_table_passes(self) -> None:
        code, out = self.run_check(ledger())
        self.assertEqual(code, 0, out)
        self.assertIn("checked 1 section(s): 0 fail, 0 warn", out)

    def test_real_world_sample_passes(self) -> None:
        code, out = self.run_path(VALID_FIXTURE)
        self.assertEqual(code, 0, out)
        self.assertIn("0 fail", out)

    def test_crlf_and_bold_footer_labels_pass(self) -> None:
        footers = [line.replace("| Total (all tasks) |", "| **Total (all tasks)** |") for line in footer()]
        path = self.dir / "crlf.md"
        path.write_bytes(ledger(footers=footers).replace("\n", "\r\n").encode("utf-8"))
        code, out = self.run_path(path)
        self.assertEqual(code, 0, out)

    def test_all_numeric_tokens_sum_within_tolerance(self) -> None:
        rows = [
            row(1, "W0", "completed", "10.0K", "00:05", "00:00"),
            row(2, "W1", "failed", "1.5M", "00:20", "00:00"),
        ]
        footers = footer(count=2, tokens="1510.0K", sla="00:25", open_count=1, remaining="00:00", path="2", path_sla="00:00")
        code, out = self.run_check(ledger(rows=rows, footers=footers))
        self.assertEqual(code, 0, out)

    def test_partial_column_total_is_still_checked(self) -> None:
        # a dash row contributes 0, so a wrong total fails even though the column is partial
        out = self.assert_fails(ledger(footers=footer(tokens="99.0K")), "Total (all tasks) Tokens", "34.5K")
        self.assertIn("must carry a leading ~", out)  # unmarked total although a summand is a ~ estimate
        self.assert_fails(ledger(footers=footer(tokens="—")), "but the rows sum to 34.5K")

    def test_est_rows_are_not_summed_and_total_is_exact(self) -> None:
        rows = default_rows()
        rows[3] = row(4, "W3", "pending", "est. 2-4K", "00:05", "00:05")
        code, out = self.run_check(ledger(rows=rows, footers=footer(tokens="~34.5K")))
        self.assertEqual(code, 0, out)  # the planned band is not summed
        self.assert_fails(ledger(rows=rows, footers=footer(tokens="~36.0K")), "!= sum of rows 34.5K")
        self.assert_fails(ledger(rows=rows, footers=footer(tokens="~999.9K")), "!= sum of rows 34.5K")
        self.assert_fails(ledger(rows=rows, footers=footer(tokens="~30.0K")), "!= sum of rows 34.5K")
        self.assert_fails(ledger(rows=rows, footers=footer(tokens="34.5K")), "must carry a leading ~")

    def test_tilde_total_without_estimated_summand_fails(self) -> None:
        rows = default_rows()
        rows[2] = row(3, "W2", "running (dispatched 20:06)", "4.0K", "00:10", "00:07")
        self.assert_fails(ledger(rows=rows, footers=footer(tokens="~34.5K")), "no summed row is a ~ estimate")
        code, out = self.run_check(ledger(rows=rows, footers=footer(tokens="34.5K")))
        self.assertEqual(code, 0, out)

    def test_band_total_with_no_spend_fails(self) -> None:
        rows = [row(n, "W0", "pending", "est. 2-4K", "00:05", "00:05") for n in range(1, 3)]
        footers = footer(count=2, tokens="est. 999K", sla="00:10", open_count=2, remaining="00:10", path="1", path_sla="00:05")
        self.assert_fails(ledger(rows=rows, footers=footers), "is a band")
        code, out = self.run_check(ledger(rows=rows, footers=footer(count=2, tokens="—", sla="00:10", open_count=2, remaining="00:10", path="1", path_sla="00:05")))
        self.assertEqual(code, 0, out)

    def test_plan_before_dispatch_with_no_spend_passes(self) -> None:
        rows = [row(n, "W0" if n < 3 else "W1", "pending", "—", "00:05", "00:05") for n in range(1, 5)]
        footers = footer(count=4, tokens="—", sla="00:20", open_count=4, remaining="00:20", path="1 → 3", path_sla="00:10")
        code, out = self.run_check(ledger(rows=rows, footers=footers))
        self.assertEqual(code, 0, out)

    def test_backtick_wrapped_footer_labels_pass(self) -> None:
        def wrap(line, wrapper):
            head, rest = line[2:].split(" |", 1)
            return "| " + wrapper(head) + " |" + rest

        for wrapper in (lambda s: f"`{s}`", lambda s: f"**`{s}`**"):
            with self.subTest(wrapper=wrapper("x")):
                footers = [wrap(line, wrapper) for line in footer()]
                code, out = self.run_check(ledger(footers=footers))
                self.assertEqual(code, 0, out)
        wrong = [wrap(line, lambda s: f"`{s}`") for line in footer(count=9)]
        self.assert_fails(ledger(footers=wrong), "count 9 != 4 task rows")

    # -- schema failures

    def test_missing_column_fails(self) -> None:
        header = [c for c in COLUMNS if c != "Assets"]
        self.assert_fails(ledger(header=header), "header columns", "missing Assets")

    def test_misordered_columns_fail(self) -> None:
        header = list(COLUMNS)
        header[3], header[4] = header[4], header[3]
        self.assert_fails(ledger(header=header), "out of order")

    def test_row_with_missing_cell_fails(self) -> None:
        rows = default_rows()
        rows[1] = table_row(rows[1].strip("| ").split(" | ")[:-1])
        self.assert_fails(ledger(rows=rows), "row 2: has 12 cells, expected 13")

    def test_bad_wave_empty_assets_and_status_fail(self) -> None:
        rows = default_rows()
        rows[0] = row(1, "Wave0", "completed", "10.0K", "00:05", "00:00")
        rows[1] = row(2, "W1", "completed", "20.5K", "00:20", "00:00", assets="—")
        rows[3] = row(4, "W3", "almost done", "—", "00:05", "00:05")
        out = self.assert_fails(ledger(rows=rows), "row 1: Wave", "row 2: Assets", "row 4: Status")
        self.assertIn("checked 1 section(s): 3 fail", out)

    def test_status_with_trailing_detail_is_accepted(self) -> None:
        rows = default_rows()
        rows[3] = row(4, "W3", "blocked (waiting on a human decision)", "—", "00:05", "00:05")
        code, out = self.run_check(ledger(rows=rows))
        self.assertEqual(code, 0, out)

    def test_invalid_tokens_format_fails(self) -> None:
        for tokens in ("10 tokens", "10.25K", "10.K", "1k", "~~5K", "est."):
            with self.subTest(tokens=tokens):
                rows = default_rows()
                rows[0] = row(1, "W0", "completed", tokens, "00:05", "00:00")
                self.assert_fails(ledger(rows=rows), "row 1: Tokens")
        self.assert_fails(ledger(footers=footer(tokens="~34.50K")), "Total (all tasks) Tokens")

    def test_integer_and_one_decimal_tokens_pass(self) -> None:
        rows = default_rows()
        rows[0] = row(1, "W0", "completed", "10K", "00:05", "00:00")
        code, out = self.run_check(ledger(rows=rows))
        self.assertEqual(code, 0, out)

    def test_manifest_missing_fails(self) -> None:
        self.assert_fails(ledger(manifest="Requested by: tester"), "'Route'", "'Rules in force'", "'Agents'", "'Helpers'")

    def test_each_manifest_field_is_required(self) -> None:
        for field in MANIFEST_FIELDS:
            with self.subTest(field=field):
                self.assert_fails(ledger(manifest=manifest(omit=(field,))), f"does not mention '{field}'")

    def test_asset_missing_from_manifest_fails(self) -> None:
        rows = default_rows()
        rows[0] = row(1, "W0", "completed", "10.0K", "00:05", "00:00", assets="skill:example-skill · workflow:unlisted-flow")
        self.assert_fails(ledger(rows=rows), "row 1: Assets item 'workflow:unlisted-flow' is not mentioned in the manifest")

    def test_asset_names_match_the_manifest_loosely(self) -> None:
        text = manifest(extra=" · Docs: `workflow-doc.md`")
        accepted = [
            "skill:example-skill", "rule:example-rule.md", "script:other/dir/example_check.py",
            "script:scripts\\example_check.py", "script:example_check", "wf:workflow-doc",
            "workflow:workflow-doc.md", "agent:example-agent", "INTENTS", "INTENTS.md · skill:example-skill",
            "none (inline)",
        ]
        rejected = [
            "skill:example", "script:scripts/other_tool.py", "agent:example-agentx", "rule:rule-example",
            "skill:example-skill · agent:ghost",
        ]
        for assets in accepted:
            with self.subTest(accepted=assets):
                rows = default_rows()
                rows[0] = row(1, "W0", "completed", "10.0K", "00:05", "00:00", assets=assets)
                code, out = self.run_check(ledger(rows=rows, manifest=text))
                self.assertEqual(code, 0, out)
        for assets in rejected:
            with self.subTest(rejected=assets):
                rows = default_rows()
                rows[0] = row(1, "W0", "completed", "10.0K", "00:05", "00:00", assets=assets)
                self.assert_fails(ledger(rows=rows, manifest=text), "row 1: Assets item")

    # -- footer failures

    def test_missing_footer_row_fails(self) -> None:
        self.assert_fails(ledger(footers=footer()[:2]), "missing footer row", "critical path")

    def test_footer_rows_out_of_order_fail(self) -> None:
        a, b, c = footer()
        self.assert_fails(ledger(footers=[b, a, c]), "out of order")

    def test_wrong_task_count_fails(self) -> None:
        self.assert_fails(ledger(footers=footer(count=5)), "count 5 != 4 task rows")

    def test_wrong_token_sum_fails(self) -> None:
        self.assert_fails(ledger(footers=footer(tokens="~40.0K")), "Total (all tasks) Tokens", "34.5K")

    def test_wrong_token_sum_fails_when_every_row_is_numeric(self) -> None:
        rows = [
            row(1, "W0", "completed", "10.0K", "00:05", "00:00"),
            row(2, "W1", "completed", "20.0K", "00:20", "00:00"),
        ]
        footers = footer(count=2, tokens="31.0K", sla="00:25", open_count=0, remaining="00:00", path="—", path_sla="00:00")
        self.assert_fails(ledger(rows=rows, footers=footers), "!= sum of rows 30.0K")

    def test_wrong_total_sla_fails(self) -> None:
        self.assert_fails(ledger(footers=footer(sla="00:35")), "sum of baselines 00:40")

    def test_wrong_remaining_count_fails(self) -> None:
        self.assert_fails(ledger(footers=footer(open_count=3)), "count 3 != 2 non-completed rows")

    def test_wrong_remaining_sla_sum_fails(self) -> None:
        self.assert_fails(ledger(footers=footer(remaining="00:20")), "sum of row Remaining SLA 00:12")

    def test_critical_path_longer_than_remaining_sum_fails(self) -> None:
        self.assert_fails(ledger(footers=footer(path_sla="00:13")), "exceeds the remaining sum 00:12")

    # -- row rules

    def test_terminal_row_without_actual_tokens_fails(self) -> None:
        for status in ("completed", "failed", "escalated"):
            for tokens in ("—", "", "est. 5-10K"):
                with self.subTest(status=status, tokens=tokens):
                    rows = default_rows()
                    rows[1] = row(2, "W1", status, tokens, "00:20", "00:00")
                    self.assert_fails(ledger(rows=rows), f"row 2: Status {status} requires Tokens")

    def test_terminal_row_with_estimated_tokens_passes(self) -> None:
        rows = default_rows()
        rows[1] = row(2, "W1", "completed", "~20.5K", "00:20", "00:00")
        code, out = self.run_check(ledger(rows=rows))
        self.assertEqual(code, 0, out)

    def test_failed_row_with_remaining_sla_fails(self) -> None:
        rows = default_rows()
        rows[1] = row(2, "W1", "failed", "20.5K", "00:20", "00:05")
        self.assert_fails(ledger(rows=rows), "row 2: Status failed requires Remaining SLA 00:00")

    def test_sla_above_cap_fails(self) -> None:
        for sla in ("00:31", "01:00"):
            with self.subTest(sla=sla):
                rows = default_rows()
                rows[3] = row(4, "W3", "pending", "—", sla, "00:05")
                self.assert_fails(ledger(rows=rows), "row 4: SLA", "exceeds the 00:30 cap")

    def test_sla_at_cap_passes(self) -> None:
        rows = default_rows()
        rows[3] = row(4, "W3", "pending", "—", "00:30", "00:05")
        code, out = self.run_check(ledger(rows=rows, footers=footer(sla="01:05")))
        self.assertEqual(code, 0, out)

    def test_remaining_above_baseline_warns_without_failing(self) -> None:
        rows = default_rows()
        rows[2] = row(3, "W2", "running", "~4.0K", "00:10", "00:15")
        code, out = self.run_check(ledger(rows=rows, footers=footer(remaining="00:20", path_sla="00:20")))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN", out)
        self.assertIn("possible breach", out)
        self.assertIn("0 fail, 1 warn", out)

    # -- legacy schema and section handling

    def test_legacy_header_warns_and_strict_fails(self) -> None:
        code, out = self.run_check(LEGACY)
        self.assertEqual(code, 0, out)
        self.assertIn("WARN Old row header: legacy schema", out)
        self.assertIn("0 fail, 1 warn", out)
        code, out = self.run_check(LEGACY, "--strict")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL Old row header: legacy schema", out)

    def test_session_filter_selects_sections(self) -> None:
        good = ledger(name="alpha run")
        bad = ledger(name="beta run", footers=footer(count=9))
        text = good + "\n" + bad
        code, out = self.run_check(text)
        self.assertEqual(code, 1, out)
        self.assertIn("checked 2 section(s)", out)
        self.assertIn("FAIL beta run (2026-10-27) row footer", out)
        code, out = self.run_check(text, "--session", "alpha")
        self.assertEqual(code, 0, out)
        self.assertIn("checked 1 section(s): 0 fail, 0 warn", out)
        code, out = self.run_check(text, "--session", "beta")
        self.assertEqual(code, 1, out)
        self.assertIn("checked 1 section(s)", out)

    def test_session_filter_without_match_fails(self) -> None:
        code, out = self.run_check(ledger(), "--session", "nonexistent")
        self.assertEqual(code, 1, out)
        self.assertIn("no section header contains", out)
        self.assertIn("checked 0 section(s)", out)

    def test_file_without_a_table_fails(self) -> None:
        self.assert_fails("## Session: Empty\n\nNo table here.\n", "no tasks table found")

    def test_headerless_file_is_one_anonymous_section(self) -> None:
        body = ledger().split("\n", 2)[2]  # drop the session header and manifest lines
        code, out = self.run_check(body, name="table-only.md")
        self.assertEqual(code, 1, out)
        self.assertIn("FAIL table-only.md row -: assets manifest", out)
        self.assertIn("checked 1 section(s)", out)

    def test_table_inside_code_fence_is_ignored(self) -> None:
        fenced = "## Session: Fenced\n" + MANIFEST + "\n\n```\n" + ledger().split("\n", 2)[2] + "```\n"
        self.assert_fails(fenced, "no tasks table found")

    def test_unreadable_file_exits_2(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = checker.main([str(self.dir / "missing.md")])
        self.assertEqual(code, 2)
        self.assertIn("cannot read", buf.getvalue())

    # -- CLI from another working directory

    def test_cli_runs_from_another_directory(self) -> None:
        path = self.dir / "TASKS_TABLE.md"
        path.write_text(ledger(), encoding="utf-8", newline="\n")
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(path)],
            cwd=self.dir, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("checked 1 section(s)", result.stdout)
        path.write_text(ledger(footers=footer(count=9)), encoding="utf-8", newline="\n")
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), str(path)],
            cwd=self.dir, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)

    def test_cli_help_works(self) -> None:
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--help"],
            cwd=self.dir, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--session", result.stdout)
        self.assertIn("--strict", result.stdout)


if __name__ == "__main__":
    unittest.main()
