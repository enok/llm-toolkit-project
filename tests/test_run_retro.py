from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "run-retrospective" / "scripts" / "run_retro.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "run-retrospective"
VALID_LOG = FIXTURES / "valid-log.jsonl"
INVALID_LOG = FIXTURES / "invalid-log.jsonl"
SPEC = importlib.util.spec_from_file_location("run_retro", SCRIPT)
assert SPEC and SPEC.loader
retro = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = retro
SPEC.loader.exec_module(retro)

SIG = "tool-misuse/sample-slug"
SAFETY = "safety-near-miss/sample-slug"
METRICS = {"tasks": 4, "first_pass": 4, "iterations": 5, "user_corrections": 0, "escaped_defects": 0, "tool_errors": 0}


def make_mistake(sig=SIG, severity="low", source="self-review", summary="a generic mistake", fix="a generic fix", prevented_by=None):
    return {
        "signature": sig,
        "category": sig.split("/")[0],
        "severity": severity,
        "source": source,
        "summary": summary,
        "fix": fix,
        "prevented_by": prevented_by,
    }


def make_record(date="2026-10-01", workflow="example-flow", mistakes=None, promotions=None, metrics=None, **extra):
    record = {
        "schema": 1,
        "date": date,
        "workflow": workflow,
        "outcome": "success",
        "metrics": dict(METRICS, **(metrics or {})),
        "mistakes": mistakes if mistakes is not None else [],
        "promotions": promotions if promotions is not None else [],
    }
    record.update(extra)
    return record


def run_with(date, workflow="flow-a", sigs=(), promos=(), severity="low"):
    """A record that records `sigs` and promotions `promos` = [(signature, level)]."""
    return make_record(
        date=date,
        workflow=workflow,
        mistakes=[make_mistake(sig, severity=severity) for sig in sigs],
        promotions=[{"signature": sig, "level": level, "asset": "rules/sample.md"} for sig, level in promos],
    )


BASE = make_record(
    mistakes=[make_mistake(prevented_by="learnings/sample.md")],
    promotions=[{"signature": SIG, "level": "learning", "asset": "learnings/sample.md"}],
    agent="agent-orchestrator",
    task_shape="generic task shape",
    notes="generic note",
)


def load_fixture_records():
    records, errors = retro.load_records(VALID_LOG)
    assert not errors, errors
    return records


class RetroCase(unittest.TestCase):
    """Isolates every test from the real home directory and environment."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()
        patcher = mock.patch.object(Path, "home", return_value=self.home)
        patcher.start()
        self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ, {}, clear=False)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop(retro.ENV_LOG, None)
        self.log = self.tmp / "logs" / "run-log.jsonl"

    def run_cli(self, *args, stdin=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            if stdin is None:
                code = retro.main(list(args))
            else:
                stream = io.TextIOWrapper(io.BytesIO(stdin), encoding="utf-8") if isinstance(stdin, bytes) else io.StringIO(stdin)
                with mock.patch.object(sys, "stdin", stream):
                    code = retro.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def write_log(self, records, path=None):
        path = path or self.log
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes("".join(retro.canonical_json(r) + "\n" for r in records).encode("utf-8"))
        return path

    def write_record_file(self, record, name="record.json"):
        path = self.tmp / name
        path.write_text(json.dumps(record), encoding="utf-8")
        return path

    def assertHasError(self, errors, fragment):
        self.assertTrue(any(fragment in error for error in errors), "%r not found in %r" % (fragment, errors))


# --------------------------------------------------------------------------- validation


class RecordValidationTests(RetroCase):
    def check(self, mutate, fragment):
        record = copy.deepcopy(BASE)
        mutate(record)
        self.assertHasError(retro.validate_record(record), fragment)

    def test_base_and_minimal_records_are_valid(self):
        self.assertEqual(retro.validate_record(BASE), [])
        self.assertEqual(retro.validate_record(make_record()), [])

    def test_non_object_records_are_rejected(self):
        for value in ([], "text", 3, None):
            self.assertEqual(retro.validate_record(value), ["record must be a JSON object"])

    def test_every_required_key_is_required(self):
        for key in retro.REQUIRED_KEYS:
            with self.subTest(key=key):
                self.check(lambda r, k=key: r.pop(k), "missing required key '%s'" % key)

    def test_optional_keys_may_be_absent(self):
        record = make_record()
        for key in retro.OPTIONAL_KEYS:
            self.assertNotIn(key, record)
        self.assertEqual(retro.validate_record(record), [])

    def test_unknown_top_level_keys_are_rejected_in_sorted_order(self):
        record = copy.deepcopy(BASE)
        record["zeta"] = 1
        record["alpha"] = 2
        errors = retro.validate_record(record)
        self.assertEqual([e for e in errors if e.startswith("unknown key")], ["unknown key 'alpha'", "unknown key 'zeta'"])

    def test_unknown_keys_in_nested_objects_are_rejected(self):
        self.check(lambda r: r["metrics"].update(extra=1), "metrics: unknown key 'extra'")
        self.check(lambda r: r["mistakes"][0].update(extra=1), "mistakes[0]: unknown key 'extra'")
        self.check(lambda r: r["promotions"][0].update(extra=1), "promotions[0]: unknown key 'extra'")

    def test_schema_must_be_integer_one(self):
        for value in (0, 2, True, "1", 1.0, None):
            with self.subTest(value=value):
                self.check(lambda r, v=value: r.update(schema=v), "schema: must be the integer 1")

    def test_date_must_be_a_real_iso_date(self):
        for value in ("2026-13-01", "2026-02-30", "2026/10/07", "20261007", "2026-1-7", "2026-10-07\n", "", 20261007, None):
            with self.subTest(value=value):
                self.check(lambda r, v=value: r.update(date=v), "date:")
        self.assertEqual(retro.validate_record(make_record(date="2028-02-29")), [])

    def test_workflow_must_be_kebab_case(self):
        for value in ("Upper-Case", "snake_case", "-leading", "trailing-", "double--hyphen", "has space", "", 5):
            with self.subTest(value=value):
                self.check(lambda r, v=value: r.update(workflow=v), "workflow:")
        for value in ("a", "abc-def-1", "ad-hoc-study-repo"):
            self.assertEqual(retro.validate_record(make_record(workflow=value)), [])

    def test_outcome_enum(self):
        for value in retro.OUTCOMES:
            self.assertEqual(retro.validate_record(make_record(outcome=value)), [])
        for value in ("done", "SUCCESS", "", None):
            with self.subTest(value=value):
                self.check(lambda r, v=value: r.update(outcome=v), "outcome: must be one of")

    def test_optional_text_fields(self):
        self.check(lambda r: r.update(agent=3), "agent: must be a string")
        self.check(lambda r: r.update(agent=""), "agent: must not be empty")
        self.check(lambda r: r.update(task_shape=None), "task_shape: must be a string")
        self.check(lambda r: r.update(notes=["x"]), "notes: must be a string")

    def test_length_limits_are_inclusive(self):
        limits = [("task_shape", 120), ("notes", 500)]
        for key, limit in limits:
            with self.subTest(key=key):
                self.assertEqual(retro.validate_record(make_record(**{key: "x" * limit})), [])
                self.check(lambda r, k=key, n=limit: r.update({k: "x" * (n + 1)}), "%s: must be at most %d" % (key, limit))
        record = copy.deepcopy(BASE)
        record["mistakes"][0]["summary"] = "x" * 200
        record["mistakes"][0]["fix"] = "y" * 200
        self.assertEqual(retro.validate_record(record), [])
        self.check(lambda r: r["mistakes"][0].update(summary="x" * 201), "mistakes[0].summary: must be at most 200")
        self.check(lambda r: r["mistakes"][0].update(fix="y" * 201), "mistakes[0].fix: must be at most 200")

    def test_signature_length_limit_is_80(self):
        ok = "tool-misuse/" + "a" * (80 - len("tool-misuse/"))
        self.assertEqual(len(ok), 80)
        record = make_record(mistakes=[make_mistake(ok)])
        self.assertEqual(retro.validate_record(record), [])
        too_long = ok + "a"
        record = make_record(mistakes=[make_mistake(too_long)])
        self.assertHasError(retro.validate_record(record), "mistakes[0].signature: must be at most 80")

    def test_run_id_format(self):
        self.assertEqual(retro.validate_record(make_record(run_id="2026-10-07-study-repo-to-publication-1a2b3c")), [])
        for value in ("Has-Upper", "has space", "", "-lead", 5, None, "a" * 129):
            with self.subTest(value=value):
                self.check(lambda r, v=value: r.update(run_id=v), "run_id:")

    def test_run_id_uniqueness_against_existing_ids(self):
        record = make_record(run_id="2026-10-01-example-flow-aaaaaa")
        self.assertEqual(retro.validate_record(record, ["other-id"]), [])
        self.assertHasError(retro.validate_record(record, {"2026-10-01-example-flow-aaaaaa"}), "already exists")

    def test_metrics_must_be_complete_non_negative_ints(self):
        for key in retro.METRIC_KEYS:
            with self.subTest(missing=key):
                self.check(lambda r, k=key: r["metrics"].pop(k), "metrics: missing required key '%s'" % key)
            for bad in (-1, 1.5, "3", True, None):
                with self.subTest(key=key, bad=bad):
                    self.check(lambda r, k=key, b=bad: r["metrics"].update({k: b}), "metrics.%s: must be a non-negative integer" % key)
        self.check(lambda r: r.update(metrics=[]), "metrics: must be an object")

    def test_metrics_invariants(self):
        self.check(lambda r: r["metrics"].update(tasks=3, first_pass=4), "first_pass: must not exceed")
        self.check(lambda r: r["metrics"].update(tasks=5, iterations=4), "iterations: must be >= metrics.tasks")
        self.assertEqual(retro.validate_record(make_record(metrics={"tasks": 3, "first_pass": 3, "iterations": 3})), [])
        # tasks == 0: no iterations floor, first_pass must be 0
        self.assertEqual(retro.validate_record(make_record(metrics={"tasks": 0, "first_pass": 0, "iterations": 0})), [])
        self.assertEqual(retro.validate_record(make_record(metrics={"tasks": 0, "first_pass": 0, "iterations": 2})), [])
        self.check(lambda r: r["metrics"].update(tasks=0, first_pass=1, iterations=0), "first_pass: must not exceed")

    def test_mistakes_and_promotions_must_be_lists_of_objects(self):
        self.check(lambda r: r.update(mistakes={}), "mistakes: must be a list")
        self.check(lambda r: r.update(promotions="x"), "promotions: must be a list")
        self.check(lambda r: r["mistakes"].append("x"), "mistakes[1]: must be an object")
        self.check(lambda r: r["promotions"].append(3), "promotions[1]: must be an object")

    def test_every_mistake_key_is_required(self):
        for key in retro.MISTAKE_KEYS:
            with self.subTest(key=key):
                self.check(lambda r, k=key: r["mistakes"][0].pop(k), "mistakes[0]: missing required key '%s'" % key)

    def test_signature_pattern(self):
        for bad in ("noslash", "Upper/case-slug", "tool-misuse/Upper", "tool-misuse/under_score", "tool-misuse/", "/slug",
                    "tool-misuse/a--b", "tool-misuse/-a", "tool-misuse/a-", "tool-misuse/a/b", "tool_misuse/a", "tool-misuse/a b", "", 4):
            with self.subTest(bad=bad):
                record = make_record(mistakes=[make_mistake()])
                record["mistakes"][0]["signature"] = bad
                self.assertHasError(retro.validate_record(record), "mistakes[0].signature:")
        for good in ("tool-misuse/a", "tool-misuse/a1-b2-c3", "spec-gap/x9"):
            self.assertEqual(retro.validate_record(make_record(mistakes=[make_mistake(good)])), [])

    def test_category_must_be_known_and_match_the_signature_prefix(self):
        self.check(lambda r: r["mistakes"][0].update(category="spec-gap"), "category: must equal the signature prefix 'tool-misuse'")
        self.check(lambda r: r["mistakes"][0].update(category="made-up"), "category: must be one of")
        for category in retro.CATEGORIES:
            with self.subTest(category=category):
                self.assertEqual(retro.validate_record(make_record(mistakes=[make_mistake(category + "/slug")])), [])
        record = make_record(mistakes=[make_mistake("made-up/slug")])
        self.assertHasError(retro.validate_record(record), "category: must be one of")

    def test_severity_and_source_enums(self):
        for value in retro.SEVERITIES:
            self.assertEqual(retro.validate_record(make_record(mistakes=[make_mistake(severity=value)])), [])
        for value in retro.SOURCES:
            self.assertEqual(retro.validate_record(make_record(mistakes=[make_mistake(source=value)])), [])
        self.check(lambda r: r["mistakes"][0].update(severity="urgent"), "severity: must be one of")
        self.check(lambda r: r["mistakes"][0].update(source="gut-feeling"), "source: must be one of")

    def test_summary_fix_and_prevented_by_types(self):
        self.check(lambda r: r["mistakes"][0].update(summary=""), "summary: must not be empty")
        self.check(lambda r: r["mistakes"][0].update(summary=5), "summary: must be a string")
        self.check(lambda r: r["mistakes"][0].update(fix=None), "fix: must be a string")
        record = copy.deepcopy(BASE)
        record["mistakes"][0]["fix"] = ""
        self.assertEqual(retro.validate_record(record), [])
        record["mistakes"][0]["prevented_by"] = None
        self.assertEqual(retro.validate_record(record), [])

    def test_repo_relative_path_rules_for_prevented_by_and_asset(self):
        bad_paths = {
            "/etc/passwd": "leading '/'",
            "../outside.md": "'..'",
            "a/../b.md": "'..'",
            "a/b/..": "'..'",
            "C:/repo/file.md": "drive letter",
            "c:\\repo\\file.md": "drive letter",
            "dir\\file.md": "forward slashes",
            "": "must not be empty",
            "   ": "must not be empty",
            7: "must be a string",
        }
        for path, fragment in bad_paths.items():
            with self.subTest(path=path):
                self.check(lambda r, p=path: r["mistakes"][0].update(prevented_by=p), "mistakes[0].prevented_by: ")
                self.check(lambda r, p=path: r["promotions"][0].update(asset=p), "promotions[0].asset: ")
                self.assertIn(fragment, retro.asset_path_error(path))
        for good in ("learnings/x.md", "skills/a/scripts/b.py", "a..b.md", "file.md", "dir/.hidden", "a/./b"):
            with self.subTest(good=good):
                self.assertIsNone(retro.asset_path_error(good))

    def test_promotion_fields(self):
        for key in retro.PROMOTION_KEYS:
            with self.subTest(key=key):
                self.check(lambda r, k=key: r["promotions"][0].pop(k), "promotions[0]: missing required key '%s'" % key)
        for level in retro.LEVELS:
            record = make_record(promotions=[{"signature": SIG, "level": level, "asset": "rules/x.md"}])
            self.assertEqual(retro.validate_record(record), [])
        self.check(lambda r: r["promotions"][0].update(level="record"), "promotions[0].level: must be one of")
        self.check(lambda r: r["promotions"][0].update(signature="Bad Signature"), "promotions[0].signature:")
        self.check(lambda r: r["promotions"][0].update(asset=None), "promotions[0].asset: must be a string")

    def test_multiple_errors_are_all_reported(self):
        errors = retro.validate_record({"schema": 2, "bogus": 1})
        self.assertHasError(errors, "schema:")
        self.assertHasError(errors, "unknown key 'bogus'")
        self.assertHasError(errors, "missing required key 'date'")


class PrivacyLintTests(RetroCase):
    POSITIVE = [
        ("an email address", "ask owner@example.com about it"),
        ("an AWS access key id", "key AKIAIOSFODNN7EXAMPLE leaked"),
        ("a GitHub token", "ghp_" + "a" * 20),
        ("a GitHub token", "gho_" + "B1" * 12),
        ("a GitHub token", "ghu_" + "c" * 30),
        ("a GitHub token", "ghs_" + "d" * 20),
        ("a GitHub token", "ghr_" + "e" * 20),
        ("a Slack token", "xoxb-12345"),
        ("a Slack token", "xoxa-1"),
        ("a Slack token", "xoxp-1"),
        ("a Slack token", "xoxr-1"),
        ("a private key block", "-----BEGIN PRIVATE KEY-----"),
        ("a credential assignment", "password: hunter2"),
        ("a credential assignment", "Secret=abc"),
        ("a credential assignment", "TOKEN : abc123"),
        ("a credential assignment", "set the token=value first"),
        ("a URL with a query string", "see https://example.com/page?id=1"),
        ("a URL with a query string", "ftp://example.com/x?y"),
    ]
    NEGATIVE = [
        "visit https://example.com/docs for details",
        "does this work?",
        "the token expires hourly",
        "password rotation policy",
        "tokens=3 per window",
        "the secret ",
        "ghp_short",
        "AKIASHORT",
        "xox-without-kind",
        "use @decorator syntax",
        "BEGIN of the section",
    ]

    def lint(self, value, field="notes"):
        record = copy.deepcopy(BASE)
        record[field] = value
        return retro.validate_record(record)

    def test_each_pattern_is_flagged(self):
        for label, text in self.POSITIVE:
            with self.subTest(text=text):
                self.assertHasError(self.lint(text), "notes: privacy lint: contains %s" % label)

    def test_safe_text_is_not_flagged(self):
        for text in self.NEGATIVE:
            with self.subTest(text=text):
                self.assertEqual(self.lint(text), [])

    def test_lint_covers_every_string_location(self):
        secret = "contact owner@example.com"
        cases = {
            "task_shape": lambda r: r.update(task_shape=secret),
            "agent": lambda r: r.update(agent=secret),
            "mistakes[0].summary": lambda r: r["mistakes"][0].update(summary=secret),
            "mistakes[0].fix": lambda r: r["mistakes"][0].update(fix=secret),
            "mistakes[0].prevented_by": lambda r: r["mistakes"][0].update(prevented_by="learnings/a?b.md https://example.com/x?y=1"),
            "promotions[0].asset": lambda r: r["promotions"][0].update(asset="https://example.com/a?b=1"),
        }
        for path, mutate in cases.items():
            with self.subTest(path=path):
                record = copy.deepcopy(BASE)
                mutate(record)
                self.assertHasError(retro.validate_record(record), "%s: privacy lint" % path)

    def test_lint_message_never_echoes_the_secret(self):
        errors = self.lint("password: hunter2-very-secret")
        self.assertFalse(any("hunter2" in error for error in errors))


class RunIdTests(RetroCase):
    def test_format_and_known_value(self):
        record = make_record()
        run_id = retro.generate_run_id(record)
        body = json.dumps(record, sort_keys=True, ensure_ascii=False)
        digest = hashlib.sha1(body.encode("utf-8")).hexdigest()[:6]
        self.assertEqual(run_id, "2026-10-01-example-flow-" + digest)
        self.assertRegex(run_id, r"^\d{4}-\d{2}-\d{2}-example-flow-[0-9a-f]{6}$")
        self.assertEqual(run_id, "2026-10-01-example-flow-cce8fd")  # golden: detects accidental algorithm drift

    def test_independent_of_key_order_and_of_an_existing_run_id(self):
        record = make_record(notes="n")
        reordered = dict(reversed(list(record.items())))
        self.assertEqual(retro.generate_run_id(record), retro.generate_run_id(reordered))
        with_id = dict(record, run_id="whatever-abcdef")
        self.assertEqual(retro.generate_run_id(record), retro.generate_run_id(with_id))

    def test_changes_when_content_changes(self):
        first = retro.generate_run_id(make_record(notes="one"))
        second = retro.generate_run_id(make_record(notes="two"))
        self.assertNotEqual(first, second)

    def test_non_ascii_is_hashed_unescaped(self):
        record = make_record(notes="caf\u00e9 \u2713")
        raw = json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
        escaped = json.dumps(record, sort_keys=True, ensure_ascii=True).encode("utf-8")
        self.assertNotEqual(raw, escaped)
        self.assertTrue(retro.generate_run_id(record).endswith(hashlib.sha1(raw).hexdigest()[:6]))

    def test_fixture_run_ids_are_canonical(self):
        for line in VALID_LOG.read_text(encoding="utf-8").splitlines():
            record = json.loads(line)
            self.assertEqual(record["run_id"], retro.generate_run_id(record))
            self.assertEqual(line, retro.canonical_json(record))


# --------------------------------------------------------------------------- log loading and validate


class LoadRecordsTests(RetroCase):
    def test_missing_log_is_empty(self):
        self.assertEqual(retro.load_records(self.tmp / "nope.jsonl"), ([], []))

    def test_valid_fixture_loads_in_log_order(self):
        records, errors = retro.load_records(VALID_LOG)
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 10)
        self.assertEqual([r["date"] for r in records], sorted(r["date"] for r in records))
        self.assertEqual({r["workflow"] for r in records}, {"release-notes-drafting", "dataset-validation", "report-publishing"})

    def test_invalid_fixture_reports_exact_physical_line_numbers(self):
        records, errors = retro.load_records(INVALID_LOG)
        self.assertEqual(len(records), 2)  # lines 1 and 9
        prefixes = [
            "line 3: invalid JSON:",
            "line 4: record must be a JSON object",
            "line 5: unknown key 'bogus'",
            "line 5: outcome: must be one of",
            "line 6: run_id: '2026-09-01-release-notes-drafting-fc1ef6' duplicates line 1",
            "line 7: notes: privacy lint: contains an email address",
            "line 8: metrics.first_pass: must not exceed metrics.tasks",
            "line 8: mistakes[0].category: must equal the signature prefix 'spec-gap'",
        ]
        self.assertEqual(len(errors), len(prefixes), errors)
        for error, prefix in zip(errors, prefixes):
            self.assertTrue(error.startswith(prefix), (error, prefix))

    def test_blank_lines_are_ignored_and_crlf_bom_are_tolerated(self):
        line = retro.canonical_json(make_record())
        path = self.tmp / "crlf.jsonl"
        path.write_bytes(b"\xef\xbb\xbf" + line.encode() + b"\r\n\r\n   \r\n" + line.replace("example-flow", "other-flow").encode() + b"\r\n")
        records, errors = retro.load_records(path)
        self.assertEqual(errors, [])
        self.assertEqual(len(records), 2)

    def test_last_line_without_newline_is_read(self):
        path = self.tmp / "no-newline.jsonl"
        path.write_text(retro.canonical_json(make_record()), encoding="utf-8")
        self.assertEqual(len(retro.load_records(path)[0]), 1)

    def test_invalid_utf8_line_is_reported(self):
        path = self.tmp / "bad-utf8.jsonl"
        path.write_bytes(retro.canonical_json(make_record()).encode() + b"\n" + b"\xff\xfe broken\n")
        records, errors = retro.load_records(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(errors, ["line 2: not valid UTF-8"])

    def test_duplicate_json_keys_and_nan_are_rejected(self):
        path = self.tmp / "dups.jsonl"
        path.write_text('{"schema": 1, "schema": 1}\n{"schema": NaN}\n', encoding="utf-8")
        _records, errors = retro.load_records(path)
        self.assertHasError(errors, "line 1: invalid JSON: duplicate key 'schema'")
        self.assertHasError(errors, "line 2: invalid JSON: invalid JSON constant NaN")

    def test_line_size_cap_is_8_kib(self):
        self.assertEqual(retro.MAX_LINE_BYTES, 8192)
        self.assertIsNone(retro.line_size_error("a" * 8192))
        self.assertIn("8193 bytes", retro.line_size_error("a" * 8193))
        self.assertIsNone(retro.line_size_error("\u00e9" * 4096))  # 8192 bytes
        self.assertIsNotNone(retro.line_size_error("\u00e9" * 4097))  # 8194 bytes

    def test_oversized_line_in_log_is_an_error(self):
        record = make_record(mistakes=[make_mistake("tool-misuse/slug-%02d" % n, summary="s" * 200, fix="f" * 200) for n in range(30)])
        self.assertEqual(retro.validate_record(record), [])  # valid otherwise
        path = self.write_log([record])
        records, errors = retro.load_records(path)
        self.assertEqual(records, [])
        self.assertEqual(len(errors), 1)
        self.assertRegex(errors[0], r"^line 1: line is \d+ bytes; the maximum is 8192")

    def test_directory_as_log_raises_oserror(self):
        with self.assertRaises(OSError):
            retro.load_records(self.tmp)


class ValidateCommandTests(RetroCase):
    def test_valid_log(self):
        code, out, err = self.run_cli("validate", "--log", str(VALID_LOG))
        self.assertEqual((code, out, err), (0, "ok: 10 records\n", ""))

    def test_missing_log_is_ok(self):
        code, out, _ = self.run_cli("validate", "--log", str(self.tmp / "absent.jsonl"))
        self.assertEqual((code, out), (0, "ok: 0 records\n"))

    def test_invalid_log_prints_line_errors_and_exits_1(self):
        code, out, _ = self.run_cli("validate", "--log", str(INVALID_LOG))
        self.assertEqual(code, 1)
        lines = out.splitlines()
        self.assertEqual(len(lines), 8)
        self.assertTrue(all(line.startswith("line ") for line in lines))
        self.assertNotIn("ok:", out)


# --------------------------------------------------------------------------- append


class AppendTests(RetroCase):
    def test_appends_one_canonical_line_and_prints_the_run_id(self):
        record = make_record(notes="caf\u00e9 \u2713")
        code, out, err = self.run_cli("append", "--record", str(self.write_record_file(record)), "--log", str(self.log))
        self.assertEqual((code, err), (0, ""))
        run_id = out.strip()
        self.assertEqual(run_id, retro.generate_run_id(record))
        data = self.log.read_bytes()
        self.assertTrue(data.endswith(b"\n"))
        self.assertNotIn(b"\r", data)
        self.assertIn("caf\u00e9 \u2713".encode("utf-8"), data)  # raw UTF-8, not \u escapes
        self.assertNotIn(b"\\u00e9", data)
        stored = json.loads(data.decode("utf-8"))
        self.assertEqual(stored, dict(record, run_id=run_id))
        self.assertEqual(data.decode("utf-8"), retro.canonical_json(stored) + "\n")

    def test_creates_missing_parent_directories(self):
        deep = self.tmp / "a" / "b" / "c" / "log.jsonl"
        code, _, _ = self.run_cli("append", "--record", str(self.write_record_file(make_record())), "--log", str(deep))
        self.assertEqual(code, 0)
        self.assertTrue(deep.is_file())

    def test_appends_to_existing_log_and_log_stays_valid(self):
        self.write_log([make_record(date="2026-10-01")])
        self.run_cli("append", "--record", str(self.write_record_file(make_record(date="2026-10-02"))), "--log", str(self.log))
        lines = self.log.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(self.run_cli("validate", "--log", str(self.log))[:2], (0, "ok: 2 records\n"))

    def test_unterminated_last_line_is_not_glued_to_the_new_record(self):
        self.log.parent.mkdir(parents=True)
        self.log.write_text(retro.canonical_json(make_record(date="2026-10-01")), encoding="utf-8")
        code, _, _ = self.run_cli("append", "--record", str(self.write_record_file(make_record(date="2026-10-02"))), "--log", str(self.log))
        self.assertEqual(code, 0)
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 2)
        self.assertEqual(retro.load_records(self.log)[1], [])

    def test_explicit_run_id_is_kept(self):
        record = make_record(run_id="my-custom-run-id")
        code, out, _ = self.run_cli("append", "--record", str(self.write_record_file(record)), "--log", str(self.log))
        self.assertEqual((code, out), (0, "my-custom-run-id\n"))
        self.assertEqual(json.loads(self.log.read_text(encoding="utf-8"))["run_id"], "my-custom-run-id")

    def test_reads_record_from_stdin(self):
        code, out, _ = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(make_record()))
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), retro.generate_run_id(make_record()))
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 1)

    def test_pretty_printed_record_file_is_accepted(self):
        path = self.tmp / "pretty.json"
        path.write_text(json.dumps(make_record(), indent=2), encoding="utf-8")
        self.assertEqual(self.run_cli("append", "--record", str(path), "--log", str(self.log))[0], 0)

    def test_invalid_record_writes_nothing_and_creates_no_directories(self):
        bad_records = [
            make_record(outcome="nope"),
            make_record(notes="mail owner@example.com"),
            dict(make_record(), bogus=1),
            make_record(metrics={"tasks": 1, "first_pass": 2}),
        ]
        for bad in bad_records:
            with self.subTest(bad=bad):
                code, out, err = self.run_cli("append", "--record", str(self.write_record_file(bad)), "--log", str(self.log))
                self.assertEqual((code, out), (1, ""))
                self.assertIn("error:", err)
                self.assertFalse(self.log.parent.exists())
                self.assertFalse(self.log.exists())

    def test_invalid_record_leaves_existing_log_untouched(self):
        self.write_log([make_record()])
        before = self.log.read_bytes()
        code, _, _ = self.run_cli("append", "--record", str(self.write_record_file(make_record(outcome="nope"))), "--log", str(self.log))
        self.assertEqual(code, 1)
        self.assertEqual(self.log.read_bytes(), before)

    def test_invalid_json_and_non_object_exit_1(self):
        for text in ("{not json", "[1]", '{"a": 1, "a": 2}', ""):
            with self.subTest(text=text):
                code, out, err = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=text)
                self.assertEqual(code, 1)
                self.assertEqual(out, "")
                self.assertFalse(self.log.exists())

    def test_non_utf8_record_file_exits_1(self):
        path = self.tmp / "latin1.json"
        path.write_bytes(b'{"notes": "caf\xe9"}')
        code, _, err = self.run_cli("append", "--record", str(path), "--log", str(self.log))
        self.assertEqual(code, 1)
        self.assertIn("UTF-8", err)

    def test_missing_record_file_is_an_io_error(self):
        code, _, err = self.run_cli("append", "--record", str(self.tmp / "absent.json"), "--log", str(self.log))
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_duplicate_explicit_run_id_is_rejected(self):
        record = make_record(run_id="dup-run-id")
        path = self.write_record_file(record)
        self.assertEqual(self.run_cli("append", "--record", str(path), "--log", str(self.log))[0], 0)
        before = self.log.read_bytes()
        code, _, err = self.run_cli("append", "--record", str(path), "--log", str(self.log))
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)
        self.assertEqual(self.log.read_bytes(), before)

    def test_identical_record_appended_twice_collides_on_generated_run_id(self):
        path = self.write_record_file(make_record())
        self.assertEqual(self.run_cli("append", "--record", str(path), "--log", str(self.log))[0], 0)
        code, _, err = self.run_cli("append", "--record", str(path), "--log", str(self.log))
        self.assertEqual(code, 1)
        self.assertIn("already exists", err)
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 1)

    def test_different_records_get_different_run_ids(self):
        ids = []
        for note in ("first", "second"):
            code, out, _ = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(make_record(notes=note)))
            self.assertEqual(code, 0)
            ids.append(out.strip())
        self.assertEqual(len(set(ids)), 2)

    def test_oversized_record_is_rejected_and_nothing_is_written(self):
        record = make_record(mistakes=[make_mistake("tool-misuse/slug-%02d" % n, summary="s" * 200, fix="f" * 200) for n in range(30)])
        code, _, err = self.run_cli("append", "--record", str(self.write_record_file(record)), "--log", str(self.log))
        self.assertEqual(code, 1)
        self.assertIn("8192", err)
        self.assertFalse(self.log.exists())

    def test_append_function_returns_errors_instead_of_raising(self):
        run_id, errors = retro.append_record(self.log, make_record(outcome="x"))
        self.assertIsNone(run_id)
        self.assertTrue(errors)
        run_id, errors = retro.append_record(self.log, make_record())
        self.assertEqual((run_id, errors), (retro.generate_run_id(make_record()), []))

    def test_log_is_a_directory_is_an_io_error(self):
        code, _, err = self.run_cli("append", "--record", "-", "--log", str(self.tmp), stdin=json.dumps(make_record()))
        self.assertEqual(code, 2)
        self.assertIn("error:", err)


# --------------------------------------------------------------------------- summary / windows


class WindowMathTests(RetroCase):
    def seven_runs(self):
        first_pass = [10, 5, 6, 7, 8, 9, 10]
        corrections = [0, 1, 1, 1, 2, 2, 2]
        escapes = [0, 0, 0, 0, 1, 0, 0]
        iterations = [10, 12, 12, 12, 10, 11, 12]
        return [
            make_record(
                date="2026-09-%02d" % (day + 1),
                workflow="flow-a",
                metrics={
                    "tasks": 10,
                    "first_pass": first_pass[day],
                    "iterations": iterations[day],
                    "user_corrections": corrections[day],
                    "escaped_defects": escapes[day],
                },
            )
            for day in range(7)
        ]

    def entry(self, records, window, workflow="flow-a"):
        data = retro.summarize(records, window=window)
        return next(w for w in data["workflows"] if w["workflow"] == workflow)

    def test_last_and_previous_window_known_numbers(self):
        wf = self.entry(self.seven_runs(), 3)
        self.assertEqual(wf["runs"], 7)
        self.assertEqual((wf["window_runs"], wf["prev_window_runs"]), (3, 3))
        self.assertAlmostEqual(wf["fpy_last"], 0.9)  # (8+9+10)/30; run 1 is outside both windows
        self.assertAlmostEqual(wf["fpy_prev"], 0.6)  # (5+6+7)/30
        self.assertAlmostEqual(wf["fpy_delta"], 0.3)
        self.assertAlmostEqual(wf["correction_rate"], 2.0)
        self.assertAlmostEqual(wf["correction_rate_delta"], 1.0)
        self.assertAlmostEqual(wf["escape_rate"], 1 / 3, places=4)
        self.assertAlmostEqual(wf["escape_rate_delta"], 1 / 3, places=4)
        self.assertAlmostEqual(wf["rework"], 0.1)  # (33-30)/30
        self.assertAlmostEqual(wf["rework_delta"], -0.1)  # prev (36-30)/30 = 0.2

    def test_window_one_compares_the_last_two_runs(self):
        wf = self.entry(self.seven_runs(), 1)
        self.assertEqual((wf["window_runs"], wf["prev_window_runs"]), (1, 1))
        self.assertAlmostEqual(wf["fpy_last"], 1.0)
        self.assertAlmostEqual(wf["fpy_prev"], 0.9)
        self.assertAlmostEqual(wf["fpy_delta"], 0.1)

    def test_window_larger_than_history_has_no_previous_window(self):
        wf = self.entry(self.seven_runs(), 10)
        self.assertEqual((wf["window_runs"], wf["prev_window_runs"]), (7, 0))
        self.assertAlmostEqual(wf["fpy_last"], 55 / 70, places=4)
        for key in ("fpy_prev", "fpy_delta", "correction_rate_delta", "escape_rate_delta", "rework_delta"):
            self.assertIsNone(wf[key])

    def test_partial_previous_window(self):
        wf = self.entry(self.seven_runs(), 4)  # last = runs 4-7, prev = runs 1-3
        self.assertEqual((wf["window_runs"], wf["prev_window_runs"]), (4, 3))
        self.assertAlmostEqual(wf["fpy_prev"], 21 / 30)

    def test_zero_tasks_gives_undefined_ratios(self):
        records = [make_record(metrics={"tasks": 0, "first_pass": 0, "iterations": 0})]
        wf = self.entry(records, 5, workflow="example-flow")
        self.assertIsNone(wf["fpy_last"])
        self.assertIsNone(wf["rework"])
        self.assertEqual(wf["correction_rate"], 0.0)

    def test_dates_not_log_order_define_the_windows(self):
        newest_first = list(reversed(self.seven_runs()))
        self.assertEqual(self.entry(newest_first, 3), self.entry(self.seven_runs(), 3))

    def test_same_date_ties_are_broken_by_log_order(self):
        records = [
            make_record(date="2026-10-01", metrics={"tasks": 10, "first_pass": 1, "iterations": 10}),
            make_record(date="2026-10-01", metrics={"tasks": 10, "first_pass": 9, "iterations": 10}),
        ]
        wf = self.entry(records, 1, workflow="example-flow")
        self.assertAlmostEqual(wf["fpy_last"], 0.9)
        self.assertAlmostEqual(wf["fpy_prev"], 0.1)

    def test_fixture_known_numbers(self):
        data = retro.summarize(load_fixture_records(), window=2)
        names = [w["workflow"] for w in data["workflows"]]
        self.assertEqual(names, ["dataset-validation", "release-notes-drafting", "report-publishing"])
        release = data["workflows"][1]
        self.assertEqual(release["runs"], 5)
        self.assertEqual(release["fpy_last"], 0.75)  # runs on 09-25, 10-02: (2+4)/8
        self.assertEqual(release["fpy_prev"], 0.625)  # runs on 09-08, 09-15: (2+3)/8
        self.assertEqual(release["fpy_delta"], 0.125)
        self.assertEqual(release["correction_rate"], 1.0)
        self.assertEqual(release["correction_rate_delta"], 0.5)
        self.assertEqual(release["escape_rate"], 0.5)
        self.assertEqual(release["escape_rate_delta"], 0.5)
        self.assertEqual(release["rework"], 0.125)
        self.assertEqual(release["rework_delta"], -0.25)
        full = retro.summarize(load_fixture_records(), window=5)["workflows"][1]
        self.assertEqual(full["fpy_last"], 0.7)  # 14/20, all five runs in one window
        self.assertIsNone(full["fpy_prev"])

    def test_summarize_rejects_a_non_positive_window(self):
        with self.assertRaises(ValueError):
            retro.summarize([], window=0)


class SummaryTests(RetroCase):
    def test_recurring_signatures_fields_and_order(self):
        data = retro.summarize(load_fixture_records())
        self.assertEqual(data["total_runs"], 10)
        self.assertEqual(
            [(s["signature"], s["count"], s["last_seen"], s["promoted_level"], s["ineffective"]) for s in data["recurring"]],
            [
                ("spec-gap/ambiguous-output-format", 3, "2026-09-25", "guard", False),
                ("tool-misuse/unquoted-path-with-spaces", 3, "2026-09-10", "none", False),
                ("validation-gap/schema-check-skips-empty-columns", 2, "2026-09-17", "learning", True),
            ],
        )
        cross = data["recurring"][1]
        self.assertEqual(cross["workflows"], ["dataset-validation", "release-notes-drafting", "report-publishing"])

    def test_single_occurrence_signatures_are_not_recurring(self):
        signatures = [s["signature"] for s in retro.summarize(load_fixture_records())["recurring"]]
        self.assertNotIn("safety-near-miss/write-to-wrong-target-without-approval", signatures)

    def test_count_is_distinct_runs_not_mistake_entries(self):
        records = [make_record(mistakes=[make_mistake(), make_mistake()])]
        self.assertEqual(retro.summarize(records)["recurring"], [])
        records.append(make_record(date="2026-10-02", mistakes=[make_mistake()]))
        self.assertEqual(retro.summarize(records)["recurring"][0]["count"], 2)

    def test_recurring_is_limited_to_the_top_ten(self):
        sigs = ["tool-misuse/slug-%02d" % n for n in range(12)]
        records = [make_record(date="2026-10-01", mistakes=[make_mistake(s) for s in sigs]),
                   make_record(date="2026-10-02", mistakes=[make_mistake(s) for s in sigs])]
        recurring = retro.summarize(records)["recurring"]
        self.assertEqual(len(recurring), 10)
        self.assertEqual([r["signature"] for r in recurring], sigs[:10])  # ties: first-seen log order

    def test_workflow_filter_limits_metrics_and_signatures(self):
        data = retro.summarize(load_fixture_records(), workflow="release-notes-drafting")
        self.assertEqual([w["workflow"] for w in data["workflows"]], ["release-notes-drafting"])
        self.assertEqual(data["total_runs"], 5)
        self.assertEqual([s["signature"] for s in data["recurring"]], ["spec-gap/ambiguous-output-format"])
        self.assertEqual(retro.summarize(load_fixture_records(), workflow="missing-flow")["workflows"], [])

    def test_text_output(self):
        code, out, err = self.run_cli("summary", "--log", str(VALID_LOG), "--window", "2")
        self.assertEqual((code, err), (0, ""))
        self.assertIn("workflow: release-notes-drafting", out)
        self.assertIn("first-pass yield: 0.750 (previous 0.625, delta +0.125)", out)
        self.assertIn("first-pass yield: 0.833 (previous n/a, delta n/a)", out)
        self.assertIn("3x spec-gap/ambiguous-output-format  last seen 2026-09-25  promoted: guard  ineffective: no", out)
        self.assertIn("2x validation-gap/schema-check-skips-empty-columns  last seen 2026-09-17  promoted: learning  ineffective: yes", out)
        self.assertLess(out.index("workflow: dataset-validation"), out.index("workflow: release-notes-drafting"))

    def test_json_output_matches_the_pure_function(self):
        code, out, _ = self.run_cli("summary", "--log", str(VALID_LOG), "--window", "2", "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out), retro.summarize(load_fixture_records(), window=2))

    def test_default_window_is_five(self):
        code, out, _ = self.run_cli("summary", "--log", str(VALID_LOG), "--json")
        self.assertEqual(json.loads(out)["window"], 5)

    def test_workflow_flag(self):
        code, out, _ = self.run_cli("summary", "--log", str(VALID_LOG), "--workflow", "report-publishing")
        self.assertEqual(code, 0)
        self.assertIn("workflow: report-publishing", out)
        self.assertNotIn("workflow: dataset-validation", out)

    def test_empty_and_unknown_workflow_messages(self):
        code, out, _ = self.run_cli("summary", "--log", str(self.tmp / "absent.jsonl"))
        self.assertEqual((code, out), (0, "no runs recorded\n"))
        code, out, _ = self.run_cli("summary", "--log", str(VALID_LOG), "--workflow", "missing-flow")
        self.assertEqual((code, out), (0, "no runs recorded for missing-flow\n"))
        code, out, _ = self.run_cli("summary", "--log", str(self.tmp / "absent.jsonl"), "--json")
        self.assertEqual(json.loads(out), {"recurring": [], "total_runs": 0, "window": 5, "workflows": []})

    def test_invalid_lines_are_skipped_with_a_warning(self):
        code, out, err = self.run_cli("summary", "--log", str(INVALID_LOG), "--json")
        self.assertEqual(code, 0)
        self.assertIn("warning: skipped 8 invalid log problem(s)", err)
        self.assertEqual(json.loads(out)["total_runs"], 2)


# --------------------------------------------------------------------------- candidates (ladder)


def level_of(records, sig=SIG, threshold=2):
    for item in retro.find_candidates(records, threshold):
        if item["signature"] == sig:
            return item["level"]
    return None


class LadderTests(RetroCase):
    def test_single_low_occurrence_is_not_a_candidate(self):
        self.assertIsNone(level_of([run_with("2026-10-01", sigs=[SIG])]))

    def test_second_occurrence_proposes_checklist(self):
        records = [run_with("2026-10-01", sigs=[SIG]), run_with("2026-10-02", sigs=[SIG])]
        self.assertEqual(level_of(records), "checklist")

    def test_third_and_later_occurrences_propose_guard(self):
        records = [run_with("2026-10-0%d" % d, sigs=[SIG]) for d in (1, 2, 3)]
        self.assertEqual(level_of(records), "guard")
        records.append(run_with("2026-10-04", sigs=[SIG]))
        self.assertEqual(level_of(records), "guard")

    def test_threshold_changes_when_a_never_promoted_signature_surfaces(self):
        two = [run_with("2026-10-01", sigs=[SIG]), run_with("2026-10-02", sigs=[SIG])]
        three = two + [run_with("2026-10-03", sigs=[SIG])]
        self.assertIsNone(level_of(two, threshold=3))
        self.assertEqual(level_of(three, threshold=3), "guard")
        self.assertEqual(level_of(three, threshold=2), "guard")
        self.assertEqual(level_of([run_with("2026-10-01", sigs=[SIG])], threshold=1), "learning")
        self.assertEqual(level_of(two, threshold=1), "checklist")

    def test_recurrence_in_the_same_run_counts_once(self):
        self.assertIsNone(level_of([run_with("2026-10-01", sigs=[SIG, SIG])]))

    def test_high_critical_and_safety_near_miss_go_straight_to_guard(self):
        for severity in ("high", "critical"):
            with self.subTest(severity=severity):
                self.assertEqual(level_of([run_with("2026-10-01", sigs=[SIG], severity=severity)]), "guard")
        self.assertEqual(level_of([run_with("2026-10-01", sigs=[SAFETY], severity="low")], sig=SAFETY), "guard")
        self.assertIsNone(level_of([run_with("2026-10-01", sigs=[SIG], severity="medium")]))

    def test_severe_signature_ignores_the_count_threshold(self):
        records = [run_with("2026-10-01", sigs=[SIG], severity="high")]
        self.assertEqual(level_of(records, threshold=9), "guard")

    def test_severe_signature_needs_a_guard_not_just_a_learning(self):
        # Decision: "never promoted" for severe signatures means no guard-or-higher promotion yet.
        for level, expected in (("learning", "guard"), ("checklist", "guard"), ("guard", None), ("rule", None)):
            with self.subTest(level=level):
                records = [run_with("2026-10-01", sigs=[SIG], promos=[(SIG, level)], severity="critical")]
                self.assertEqual(level_of(records), expected)

    def test_promoted_signatures_are_not_proposed_again_without_a_recurrence(self):
        records = [run_with("2026-10-01", sigs=[SIG]), run_with("2026-10-02", sigs=[SIG], promos=[(SIG, "checklist")])]
        self.assertIsNone(level_of(records))
        self.assertIsNone(level_of(records + [run_with("2026-10-03")]))

    def test_ineffective_prevention_climbs_one_level_above_the_highest(self):
        cases = [
            ("learning", "checklist"),
            ("checklist", "guard"),
            ("guard", "rule"),
            ("rule", "rule"),
        ]
        for promoted, expected in cases:
            with self.subTest(promoted=promoted):
                records = [
                    run_with("2026-10-01", sigs=[SIG], promos=[(SIG, promoted)]),
                    run_with("2026-10-02", sigs=[SIG]),
                ]
                self.assertEqual(level_of(records), expected)

    def test_rule_that_failed_is_flagged_for_escalation(self):
        records = [run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "rule")]), run_with("2026-10-02", sigs=[SIG])]
        reason = retro.find_candidates(records)[0]["reason"]
        self.assertIn("escalate", reason)

    def test_next_level_is_above_the_highest_recorded_not_the_latest(self):
        records = [
            run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "guard")]),
            run_with("2026-10-02", sigs=[SIG], promos=[(SIG, "checklist")]),  # lower level recorded later
            run_with("2026-10-03", sigs=[SIG]),
        ]
        self.assertEqual(level_of(records), "rule")

    def test_two_promotions_in_one_run_use_the_higher_one(self):
        records = [
            run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "learning"), (SIG, "checklist")]),
            run_with("2026-10-02", sigs=[SIG]),
        ]
        self.assertEqual(level_of(records), "guard")

    def test_promoting_the_next_level_clears_the_flag_until_it_fails_too(self):
        records = [
            run_with("2026-10-01", sigs=[SIG]),
            run_with("2026-10-02", sigs=[SIG], promos=[(SIG, "checklist")]),
            run_with("2026-10-03", sigs=[SIG], promos=[(SIG, "guard")]),  # recurrence answered by a guard
        ]
        self.assertIsNone(level_of(records))
        records.append(run_with("2026-10-04"))
        self.assertIsNone(level_of(records))
        records.append(run_with("2026-10-05", sigs=[SIG]))
        self.assertEqual(level_of(records), "rule")

    def test_repeating_the_same_level_does_not_clear_the_flag(self):
        # A second guard recorded in the run that recurred does not hide that the first guard failed.
        records = [
            run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "guard")]),
            run_with("2026-10-02", sigs=[SIG], promos=[(SIG, "guard")]),
        ]
        self.assertEqual(level_of(records), "rule")

    def test_same_date_runs_are_ordered_by_log_position(self):
        promote_then_recur = [
            run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "checklist")]),
            run_with("2026-10-01", sigs=[SIG]),
        ]
        self.assertEqual(level_of(promote_then_recur), "guard")
        recur_then_promote = [
            run_with("2026-10-01", sigs=[SIG]),
            run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "checklist")]),
        ]
        self.assertIsNone(level_of(recur_then_promote))

    def test_an_earlier_dated_run_logged_later_is_not_after_the_promotion(self):
        records = [
            run_with("2026-10-05", sigs=[SIG], promos=[(SIG, "checklist")]),
            run_with("2026-10-01", sigs=[SIG]),  # appended late, dated before the promotion
        ]
        self.assertIsNone(level_of(records))

    def test_three_distinct_workflows_propose_rule(self):
        records = [run_with("2026-10-0%d" % n, workflow="flow-" + w, sigs=[SIG]) for n, w in enumerate("abc", start=1)]
        self.assertEqual(level_of(records), "rule")
        reason = retro.find_candidates(records)[0]["reason"]
        self.assertIn("3 distinct workflows", reason)

    def test_cross_workflow_rule_beats_the_count_based_guard_and_ignores_threshold(self):
        records = [run_with("2026-10-0%d" % n, workflow="flow-" + w, sigs=[SIG]) for n, w in enumerate("abc", start=1)]
        self.assertEqual(level_of(records, threshold=1), "rule")
        self.assertEqual(level_of(records, threshold=50), "rule")

    def test_two_workflows_are_not_enough_for_rule(self):
        records = [run_with("2026-10-01", workflow="flow-a", sigs=[SIG]), run_with("2026-10-02", workflow="flow-b", sigs=[SIG])]
        self.assertEqual(level_of(records), "checklist")

    def test_cross_workflow_signature_already_covered_by_a_rule_is_quiet(self):
        records = [run_with("2026-10-0%d" % n, workflow="flow-" + w, sigs=[SIG]) for n, w in enumerate("abc", start=1)]
        records.append(run_with("2026-10-04", workflow="flow-a", promos=[(SIG, "rule")]))
        self.assertIsNone(level_of(records))
        records.append(run_with("2026-10-05", workflow="flow-a", sigs=[SIG]))
        self.assertEqual(level_of(records), "rule")  # rule failed: escalate

    def test_cross_workflow_signature_with_a_guard_still_proposes_rule(self):
        records = [run_with("2026-10-0%d" % n, workflow="flow-" + w, sigs=[SIG]) for n, w in enumerate("abc", start=1)]
        records.append(run_with("2026-10-04", workflow="flow-a", promos=[(SIG, "guard")]))
        self.assertEqual(level_of(records), "rule")

    def test_candidate_ordering_is_by_level_then_count_then_recency(self):
        a, b, c, d = ("tool-misuse/slug-" + x for x in "abcd")
        records = [
            run_with("2026-10-01", sigs=[a, b, c, d]),
            run_with("2026-10-02", sigs=[a, b, c, d]),
            run_with("2026-10-03", sigs=[a]),  # a: count 3 -> guard
            run_with("2026-10-04", sigs=[b]),  # b: count 3 -> guard, more recent than a
            run_with("2026-10-05", sigs=[c], severity="high"),  # c: count 3 -> guard, most recent
        ]
        records.append(run_with("2026-10-06", workflow="flow-x", sigs=[d]))
        records.append(run_with("2026-10-07", workflow="flow-y", sigs=[d]))  # d: 3 workflows -> rule
        order = [(i["signature"], i["level"]) for i in retro.find_candidates(records)]
        self.assertEqual(order, [(d, "rule"), (c, "guard"), (b, "guard"), (a, "guard")])

    def test_ties_fall_back_to_first_seen_log_order(self):
        x, y = "tool-misuse/slug-x", "tool-misuse/slug-y"
        records = [run_with("2026-10-01", sigs=[x, y]), run_with("2026-10-02", sigs=[x, y])]
        self.assertEqual([i["signature"] for i in retro.find_candidates(records)], [x, y])

    def test_threshold_must_be_positive(self):
        with self.assertRaises(ValueError):
            retro.find_candidates([], threshold=0)

    def test_fixture_candidates(self):
        found = retro.find_candidates(load_fixture_records())
        self.assertEqual(
            [(c["signature"], c["level"], c["promoted_level"]) for c in found],
            [
                ("tool-misuse/unquoted-path-with-spaces", "rule", "none"),
                ("safety-near-miss/write-to-wrong-target-without-approval", "guard", "none"),
                ("validation-gap/schema-check-skips-empty-columns", "checklist", "learning"),
            ],
        )

    def test_fixture_prefix_shows_the_ineffective_checklist_case(self):
        # Through 2026-09-25 the ambiguous-output-format checklist (09-15) has failed once; the guard (10-02) is not yet recorded.
        prefix = load_fixture_records()[:8]
        self.assertEqual(level_of(prefix, sig="spec-gap/ambiguous-output-format"), "guard")
        self.assertIsNone(level_of(load_fixture_records(), sig="spec-gap/ambiguous-output-format"))


class CandidatesCommandTests(RetroCase):
    def test_text_output(self):
        code, out, err = self.run_cli("candidates", "--log", str(VALID_LOG))
        self.assertEqual((code, err), (0, ""))
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("rule      tool-misuse/unquoted-path-with-spaces  (count 3, last seen 2026-09-10, promoted: none)"))
        self.assertIn("cross-workflow pattern: seen in 3 distinct workflows", lines[1])
        self.assertEqual(sum(1 for line in lines if not line.startswith(" ")), 3)

    def test_json_output(self):
        code, out, _ = self.run_cli("candidates", "--log", str(VALID_LOG), "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(data["threshold"], 2)
        self.assertEqual(data["candidates"], retro.find_candidates(load_fixture_records()))
        self.assertEqual(set(data["candidates"][0]), {"signature", "level", "reason", "count", "last_seen", "workflows", "promoted_level"})

    def test_empty_prints_no_candidates_and_exits_0(self):
        code, out, _ = self.run_cli("candidates", "--log", str(self.tmp / "absent.jsonl"))
        self.assertEqual((code, out), (0, "no candidates\n"))
        code, out, _ = self.run_cli("candidates", "--log", str(self.tmp / "absent.jsonl"), "--json")
        self.assertEqual((code, json.loads(out)), (0, {"candidates": [], "threshold": 2}))

    def test_threshold_flag(self):
        records = [run_with("2026-10-01", sigs=[SIG]), run_with("2026-10-02", sigs=[SIG])]
        path = self.write_log(records)
        self.assertEqual(self.run_cli("candidates", "--log", str(path), "--threshold", "3")[1], "no candidates\n")
        self.assertIn("checklist", self.run_cli("candidates", "--log", str(path), "--threshold", "2")[1])
        self.assertIn("learning", self.run_cli("candidates", "--log", str(self.write_log(records[:1], self.tmp / "one.jsonl")), "--threshold", "1")[1])


# --------------------------------------------------------------------------- preflight


class PreflightTests(RetroCase):
    def test_ranking_is_count_then_recency_then_first_seen(self):
        a, b, c, d = ("tool-misuse/slug-" + x for x in "abcd")
        records = [
            make_record(date="2026-10-01", mistakes=[make_mistake(a), make_mistake(b)]),
            make_record(date="2026-10-02", mistakes=[make_mistake(b), make_mistake(c), make_mistake(d)]),
        ]
        order = [p["signature"] for p in retro.preflight(records, "example-flow")["pitfalls"]]
        self.assertEqual(order, [b, c, d, a])  # b: count 2; c,d: newer than a, first-seen order c before d

    def test_older_signature_with_higher_count_outranks_newer_singletons(self):
        a, b = "tool-misuse/slug-a", "tool-misuse/slug-b"
        records = [
            make_record(date="2026-09-01", mistakes=[make_mistake(a)]),
            make_record(date="2026-09-02", mistakes=[make_mistake(a)]),
            make_record(date="2026-10-01", mistakes=[make_mistake(b)]),
        ]
        self.assertEqual([p["signature"] for p in retro.preflight(records, "example-flow")["pitfalls"]], [a, b])

    def test_limit(self):
        sigs = ["tool-misuse/slug-%d" % n for n in range(8)]
        records = [make_record(mistakes=[make_mistake(s) for s in sigs])]
        self.assertEqual(len(retro.preflight(records, "example-flow")["pitfalls"]), 5)  # default
        self.assertEqual(len(retro.preflight(records, "example-flow", limit=2)["pitfalls"]), 2)
        self.assertEqual(len(retro.preflight(records, "example-flow", limit=20)["pitfalls"]), 8)
        with self.assertRaises(ValueError):
            retro.preflight(records, "example-flow", limit=0)

    def test_latest_fix_and_prevented_by(self):
        records = [
            make_record(date="2026-10-01", mistakes=[make_mistake(fix="old fix", prevented_by="learnings/old.md")]),
            make_record(date="2026-10-03", mistakes=[make_mistake(fix="newest fix", prevented_by="learnings/new.md")]),
            make_record(date="2026-10-02", mistakes=[make_mistake(fix="middle fix", prevented_by=None)]),
        ]
        entry = retro.preflight(records, "example-flow")["pitfalls"][0]
        self.assertEqual((entry["fix"], entry["prevented_by"]), ("newest fix", "learnings/new.md"))
        self.assertEqual((entry["count"], entry["last_seen"]), (3, "2026-10-03"))

    def test_empty_fix_and_null_prevented_by_fall_back_to_the_latest_recorded_value(self):
        records = [
            make_record(date="2026-10-01", mistakes=[make_mistake(fix="useful fix", prevented_by="learnings/x.md")]),
            make_record(date="2026-10-02", mistakes=[make_mistake(fix="", prevented_by=None)]),
        ]
        entry = retro.preflight(records, "example-flow")["pitfalls"][0]
        self.assertEqual((entry["fix"], entry["prevented_by"]), ("useful fix", "learnings/x.md"))

    def test_only_the_named_workflow_is_counted(self):
        data = retro.preflight(load_fixture_records(), "dataset-validation")
        self.assertEqual(
            [(p["signature"], p["count"]) for p in data["pitfalls"]],
            [("validation-gap/schema-check-skips-empty-columns", 2), ("tool-misuse/unquoted-path-with-spaces", 1)],
        )
        self.assertEqual(data["global"], [])

    def test_include_global_adds_signatures_from_two_or_more_workflows(self):
        data = retro.preflight(load_fixture_records(), "report-publishing", limit=1, include_global=True)
        self.assertEqual([p["signature"] for p in data["pitfalls"]], ["safety-near-miss/write-to-wrong-target-without-approval"])
        self.assertEqual([g["signature"] for g in data["global"]], ["tool-misuse/unquoted-path-with-spaces"])
        entry = data["global"][0]
        self.assertEqual(entry["count"], 3)  # counted across the whole log
        self.assertEqual(entry["scope"], "global")
        self.assertEqual(len(entry["workflows"]), 3)

    def test_include_global_skips_signatures_already_listed(self):
        data = retro.preflight(load_fixture_records(), "release-notes-drafting", include_global=True)
        listed = [p["signature"] for p in data["pitfalls"]]
        self.assertIn("tool-misuse/unquoted-path-with-spaces", listed)
        self.assertEqual(data["global"], [])

    def test_include_global_works_for_a_workflow_with_no_history(self):
        data = retro.preflight(load_fixture_records(), "brand-new-flow", include_global=True)
        self.assertEqual(data["pitfalls"], [])
        self.assertEqual([g["signature"] for g in data["global"]], ["tool-misuse/unquoted-path-with-spaces"])

    def test_global_requires_two_distinct_workflows_not_two_runs(self):
        records = [make_record(date="2026-10-01", mistakes=[make_mistake()]), make_record(date="2026-10-02", mistakes=[make_mistake()])]
        self.assertEqual(retro.preflight(records, "other-flow", include_global=True)["global"], [])

    def test_without_the_flag_global_stays_empty(self):
        self.assertEqual(retro.preflight(load_fixture_records(), "brand-new-flow")["global"], [])

    def test_command_text_output(self):
        code, out, err = self.run_cli("preflight", "--workflow", "dataset-validation", "--log", str(VALID_LOG))
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(
            out.splitlines(),
            [
                "known pitfalls for dataset-validation:",
                "1. validation-gap/schema-check-skips-empty-columns - seen 2x, last 2026-09-17",
                "   fix: also assert non-null counts for optional columns",
                "   prevented by: learnings/schema-check-skips-empty-columns.md",
                "2. tool-misuse/unquoted-path-with-spaces - seen 1x, last 2026-09-03",
                "   fix: quote every path argument",
                "   prevented by: (none)",
            ],
        )

    def test_command_include_global_and_limit_flags(self):
        code, out, _ = self.run_cli("preflight", "--workflow", "report-publishing", "--limit", "1", "--include-global", "--log", str(VALID_LOG))
        self.assertEqual(code, 0)
        self.assertIn("known pitfalls for report-publishing:", out)
        self.assertIn("cross-workflow pitfalls (seen in 2+ workflows):", out)
        self.assertIn("seen 3x, last 2026-09-10, across 3 workflows", out)
        self.assertEqual(out.count("safety-near-miss/"), 1)

    def test_command_message_when_nothing_is_known(self):
        code, out, _ = self.run_cli("preflight", "--workflow", "unknown-flow", "--log", str(VALID_LOG))
        self.assertEqual((code, out), (0, "no known pitfalls for unknown-flow\n"))
        code, out, _ = self.run_cli("preflight", "--workflow", "unknown-flow", "--include-global", "--log", str(self.tmp / "absent.jsonl"))
        self.assertEqual((code, out), (0, "no known pitfalls for unknown-flow\n"))

    def test_command_global_only_output_when_workflow_is_new(self):
        code, out, _ = self.run_cli("preflight", "--workflow", "unknown-flow", "--include-global", "--log", str(VALID_LOG))
        self.assertEqual(code, 0)
        self.assertNotIn("known pitfalls for unknown-flow", out)
        self.assertIn("cross-workflow pitfalls", out)


# --------------------------------------------------------------------------- log resolution, CLI, exit codes


class LogResolutionTests(RetroCase):
    def test_flag_beats_env_beats_home(self):
        env_log = self.tmp / "env.jsonl"
        flag_log = self.tmp / "flag.jsonl"
        self.assertEqual(retro.resolve_log_path(), self.home / ".llm-toolkit" / "run-log.jsonl")
        os.environ[retro.ENV_LOG] = str(env_log)
        self.assertEqual(retro.resolve_log_path(), env_log)
        self.assertEqual(retro.resolve_log_path(str(flag_log)), flag_log)

    def test_empty_values_fall_through(self):
        os.environ[retro.ENV_LOG] = ""
        self.assertEqual(retro.resolve_log_path(""), self.home / ".llm-toolkit" / "run-log.jsonl")

    def test_environ_can_be_injected(self):
        self.assertEqual(retro.resolve_log_path(None, {retro.ENV_LOG: str(self.tmp / "x.jsonl")}), self.tmp / "x.jsonl")
        self.assertEqual(retro.resolve_log_path(None, {}), self.home / ".llm-toolkit" / "run-log.jsonl")

    def test_user_directory_is_expanded(self):
        with mock.patch.dict(os.environ, {"HOME": str(self.home), "USERPROFILE": str(self.home)}):
            self.assertEqual(retro.resolve_log_path("~/custom.jsonl"), self.home / "custom.jsonl")

    def test_commands_use_the_env_log_and_never_the_real_home(self):
        env_log = self.tmp / "from-env" / "log.jsonl"
        os.environ[retro.ENV_LOG] = str(env_log)
        code, out, _ = self.run_cli("append", "--record", "-", stdin=json.dumps(make_record()))
        self.assertEqual(code, 0)
        self.assertTrue(env_log.is_file())
        self.assertEqual(self.run_cli("validate")[1], "ok: 1 records\n")
        self.assertFalse((self.home / ".llm-toolkit").exists())

    def test_commands_default_to_the_home_log(self):
        code, _, _ = self.run_cli("append", "--record", "-", stdin=json.dumps(make_record()))
        self.assertEqual(code, 0)
        self.assertTrue((self.home / ".llm-toolkit" / "run-log.jsonl").is_file())

    def test_flag_overrides_env_in_commands(self):
        os.environ[retro.ENV_LOG] = str(self.tmp / "ignored.jsonl")
        code, out, _ = self.run_cli("validate", "--log", str(VALID_LOG))
        self.assertEqual((code, out), (0, "ok: 10 records\n"))

    def test_every_subcommand_accepts_the_log_flag(self):
        for command in (["validate"], ["summary"], ["candidates"], ["preflight", "--workflow", "example-flow"]):
            with self.subTest(command=command):
                self.assertEqual(self.run_cli(*command, "--log", str(VALID_LOG))[0], 0)
        record = self.write_record_file(make_record())
        self.assertEqual(self.run_cli("append", "--record", str(record), "--log", str(self.log))[0], 0)


class ExitCodeTests(RetroCase):
    def test_exit_0_for_successful_commands(self):
        for command in (["validate"], ["summary"], ["summary", "--json"], ["candidates"], ["candidates", "--json"], ["preflight", "--workflow", "x-flow"]):
            with self.subTest(command=command):
                self.assertEqual(self.run_cli(*command, "--log", str(VALID_LOG))[0], 0)

    def test_exit_0_for_help(self):
        self.assertEqual(self.run_cli("--help")[0], 0)
        self.assertEqual(self.run_cli("summary", "--help")[0], 0)

    def test_exit_1_for_failed_checks(self):
        self.assertEqual(self.run_cli("validate", "--log", str(INVALID_LOG))[0], 1)
        bad = self.write_record_file(make_record(outcome="nope"))
        self.assertEqual(self.run_cli("append", "--record", str(bad), "--log", str(self.log))[0], 1)

    def test_exit_2_for_usage_errors(self):
        usage_errors = [
            [],
            ["bogus"],
            ["summary", "--window", "0"],
            ["summary", "--window", "abc"],
            ["summary", "--window", "-3"],
            ["candidates", "--threshold", "0"],
            ["preflight"],
            ["preflight", "--workflow", "x-flow", "--limit", "0"],
            ["append"],
            ["validate", "--nope"],
        ]
        for command in usage_errors:
            with self.subTest(command=command):
                self.assertEqual(self.run_cli(*command, "--log", str(VALID_LOG))[0], 2)

    def test_exit_2_for_io_errors(self):
        for command in (["validate"], ["summary"], ["candidates"], ["preflight", "--workflow", "x-flow"]):
            with self.subTest(command=command):
                code, _, err = self.run_cli(*command, "--log", str(self.tmp))
                self.assertEqual(code, 2)
                self.assertIn("error:", err)
        code, _, _ = self.run_cli("append", "--record", str(self.tmp / "absent.json"), "--log", str(self.log))
        self.assertEqual(code, 2)

    def test_script_runs_as_a_program(self):
        env = {k: v for k, v in os.environ.items() if k != retro.ENV_LOG}

        def run(*args):
            return subprocess.run([sys.executable, str(SCRIPT), *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, encoding="utf-8")

        ok = run("validate", "--log", str(VALID_LOG))
        self.assertEqual((ok.returncode, ok.stdout), (0, "ok: 10 records\n"))
        self.assertEqual(run("validate", "--log", str(INVALID_LOG)).returncode, 1)
        self.assertEqual(run("summary", "--window", "0", "--log", str(VALID_LOG)).returncode, 2)


class FixtureHygieneTests(RetroCase):
    def test_fixtures_cover_the_required_scenarios(self):
        records = load_fixture_records()
        self.assertGreaterEqual(len({r["workflow"] for r in records}), 2)
        stats = retro.signature_stats(records)
        self.assertTrue(any(s["count"] >= 2 for s in stats.values()))  # recurrence
        self.assertTrue(any(s["ineffective"] for s in stats.values()))  # promotion followed by a recurrence
        self.assertTrue(any(s["severe"] and s["count"] == 1 for s in stats.values()))  # high-severity single occurrence
        self.assertTrue(any(len(s["workflows"]) >= 3 for s in stats.values()))  # cross-workflow signature

    def test_fixtures_are_generic(self):
        for path in (VALID_LOG, INVALID_LOG):
            text = path.read_text(encoding="utf-8")
            for forbidden in ("http", "://", "C:\\", "/home/", "/Users/"):
                self.assertNotIn(forbidden, text, (path.name, forbidden))
        text = VALID_LOG.read_text(encoding="utf-8")
        self.assertNotIn("@", text)


# --------------------------------------------------------------------------- rev 2: ladder count rung (V4 M1)


class CountRungTests(RetroCase):
    def candidate(self, records, threshold=2):
        found = [c for c in retro.find_candidates(records, threshold) if c["signature"] == SIG]
        return found[0] if found else None

    def test_deferred_checklist_keeps_being_proposed_after_a_learning(self):
        # V4 M1 reproduction 1: run 1 record-only, run 2 lands a learning and defers the checklist.
        records = [run_with("2026-10-01", sigs=[SIG]), run_with("2026-10-02", sigs=[SIG], promos=[(SIG, "learning")])]
        found = self.candidate(records)
        self.assertEqual(found["level"], "checklist")
        self.assertIn("not yet promoted to checklist", found["reason"])

    def test_learning_then_two_recurrences_proposes_guard_not_checklist(self):
        # V4 M1 reproduction 2: a learning in run 1, the mistake recurs in runs 2 and 3, nothing else lands.
        records = [
            run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "learning")]),
            run_with("2026-10-02", sigs=[SIG]),
            run_with("2026-10-03", sigs=[SIG]),
        ]
        self.assertEqual(self.candidate(records)["level"], "guard")

    def test_count_rung_matrix_against_the_highest_recorded_level(self):
        # (count, threshold, highest level recorded in the last run or None) -> proposed level or None
        matrix = [
            (1, 1, None, "learning"),
            (1, 1, "learning", None),
            (1, 2, None, None),
            (2, 2, None, "checklist"),
            (2, 2, "learning", "checklist"),
            (2, 2, "checklist", None),
            (2, 2, "guard", None),
            (2, 3, "learning", None),
            (3, 2, None, "guard"),
            (3, 2, "learning", "guard"),
            (3, 2, "checklist", "guard"),
            (3, 2, "guard", None),
            (3, 2, "rule", None),
            (4, 3, "checklist", "guard"),
            (4, 3, "guard", None),
        ]
        for count, threshold, highest, expected in matrix:
            with self.subTest(count=count, threshold=threshold, highest=highest):
                records = [run_with("2026-10-%02d" % (n + 1), sigs=[SIG]) for n in range(count)]
                if highest:
                    # promotion lands in the last run, so no occurrence follows it (not "ineffective")
                    records[-1]["promotions"] = [{"signature": SIG, "level": highest, "asset": "rules/sample.md"}]
                found = self.candidate(records, threshold)
                self.assertEqual(found["level"] if found else None, expected)

    def test_priority_breaks_ties_between_overlapping_decisions(self):
        records = load_fixture_records()
        found = next(c for c in retro.find_candidates(records) if c["signature"].startswith("validation-gap/"))
        self.assertEqual(found["level"], "checklist")  # ineffective and count rung both say checklist
        self.assertTrue(found["reason"].startswith("ineffective prevention"))

    def test_the_highest_overlapping_level_wins(self):
        # severe (guard) beats ineffective-after-learning (checklist) and the count rung (checklist)
        records = [
            run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "learning")], severity="critical"),
            run_with("2026-10-02", sigs=[SIG], severity="critical"),
        ]
        found = self.candidate(records)
        self.assertEqual(found["level"], "guard")
        self.assertIn("without a guard", found["reason"])
        # cross-workflow rule beats ineffective-after-checklist (guard)
        records = [
            run_with("2026-10-01", workflow="flow-a", sigs=[SIG], promos=[(SIG, "checklist")]),
            run_with("2026-10-02", workflow="flow-b", sigs=[SIG]),
            run_with("2026-10-03", workflow="flow-c", sigs=[SIG]),
        ]
        self.assertEqual(self.candidate(records)["level"], "rule")


# --------------------------------------------------------------------------- rev 2: workflow cap and re-validation (V2 R1)


class WorkflowCapTests(RetroCase):
    def test_workflow_is_capped_at_80_characters(self):
        self.assertEqual(retro.MAX_WORKFLOW, 80)
        self.assertEqual(retro.validate_record(make_record(workflow="a" * 80)), [])
        errors = retro.validate_record(make_record(workflow="a" * 81))
        self.assertHasError(errors, "workflow: must be a kebab-case name of at most 80 characters")

    def test_longest_workflow_still_yields_a_valid_generated_run_id(self):
        record = make_record(workflow="a" * 80)
        code, out, _ = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(record))
        self.assertEqual(code, 0)
        self.assertLessEqual(len(out.strip()), retro.MAX_RUN_ID)
        self.assertEqual(self.run_cli("validate", "--log", str(self.log))[:2], (0, "ok: 1 records\n"))

    def test_oversized_workflow_is_rejected_by_append_and_nothing_is_written(self):
        record = make_record(workflow="a" * 179)  # V2 R1: used to append, then fail `validate`
        code, out, err = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(record))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("workflow:", err)
        self.assertFalse(self.log.exists())

    def test_append_revalidates_the_generated_run_id_before_writing(self):
        with mock.patch.object(retro, "generate_run_id", return_value="x" * 200):
            run_id, errors = retro.append_record(self.log, make_record())
        self.assertIsNone(run_id)
        self.assertHasError(errors, "run_id:")
        self.assertFalse(self.log.exists())


# --------------------------------------------------------------------------- rev 2: hostile input never tracebacks (V2 R2/R3)


class HostileInputTests(RetroCase):
    def deep(self, depth, leaf=None):
        value = leaf
        for _ in range(depth):
            value = [value]
        return value

    def test_parse_json_turns_runaway_nesting_into_value_error(self):
        with self.assertRaises(ValueError) as caught:
            retro.parse_json("[" * 50000 + "]" * 50000)
        self.assertIn("too deep", str(caught.exception))

    def test_deeply_nested_log_line_is_a_line_error_and_other_lines_survive(self):
        good = retro.canonical_json(make_record())
        path = self.tmp / "deep.jsonl"
        path.write_bytes((good + "\n" + "[" * 4000 + "]" * 4000 + "\n").encode("utf-8"))
        records, errors = retro.load_records(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("line 2: "), errors)

    def test_commands_survive_a_nested_line(self):
        path = self.tmp / "deep.jsonl"
        path.write_bytes((retro.canonical_json(make_record()) + "\n" + "[" * 20000 + "]" * 20000 + "\n").encode("utf-8"))
        code, out, _ = self.run_cli("validate", "--log", str(path))
        self.assertEqual(code, 1)
        self.assertIn("line 2: invalid JSON: JSON nesting is too deep", out)
        for command in (["summary"], ["candidates"], ["signatures"], ["preflight", "--workflow", "example-flow"]):
            with self.subTest(command=command):
                code, _, err = self.run_cli(*command, "--log", str(path))
                self.assertEqual(code, 0)
                self.assertIn("warning: skipped", err)

    def test_append_of_nested_input_is_exit_1(self):
        code, out, err = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin="[" * 20000 + "]" * 20000)
        self.assertEqual((code, out), (1, ""))
        self.assertIn("too deep", err)
        self.assertFalse(self.log.exists())

    def test_validate_record_handles_programmatic_nesting_without_recursion(self):
        for leaf_wrapper in (lambda v: [v], lambda v: {"k": v}):
            with self.subTest():
                value = "plain"
                for _ in range(5000):
                    value = leaf_wrapper(value)
                record = make_record()
                record["extra"] = value
                errors = retro.validate_record(record)
                self.assertHasError(errors, "unknown key 'extra'")

    def test_privacy_lint_still_reports_a_secret_buried_in_nesting(self):
        record = make_record()
        record["extra"] = self.deep(200, "owner@example.com")
        errors = retro.validate_record(record)
        self.assertHasError(errors, "privacy lint: contains an email address")
        self.assertTrue(any(e.startswith("extra[0][0]") for e in errors), errors)

    def test_lone_surrogates_are_validation_errors_everywhere(self):
        lone = "bad\ud800text"
        cases = {
            "notes": lambda r: r.update(notes=lone),
            "task_shape": lambda r: r.update(task_shape=lone),
            "agent": lambda r: r.update(agent=lone),
            "mistakes[0].summary": lambda r: r["mistakes"][0].update(summary=lone),
            "mistakes[0].fix": lambda r: r["mistakes"][0].update(fix=lone),
            "mistakes[0].prevented_by": lambda r: r["mistakes"][0].update(prevented_by=lone),
            "promotions[0].asset": lambda r: r["promotions"][0].update(asset=lone),
        }
        for path, mutate in cases.items():
            with self.subTest(path=path):
                record = copy.deepcopy(BASE)
                mutate(record)
                errors = retro.validate_record(record)
                self.assertHasError(errors, "%s: contains a character that cannot be encoded as UTF-8" % path)
                for error in errors:
                    error.encode("utf-8")  # every message is printable

    def test_lone_surrogate_keys_and_ids_never_leak_into_messages(self):
        record = make_record()
        record["bad\ud800key"] = 1
        errors = retro.validate_record(record)
        self.assertHasError(errors, "unknown key 'bad\\ud800key'")
        text = '{"a\\ud800": 1, "a\\ud800": 2}'
        with self.assertRaises(ValueError) as caught:
            retro.parse_json(text)
        str(caught.exception).encode("utf-8")
        line = json.dumps(make_record(run_id="id-\ud800"))  # invalid id twice: duplicate message must stay encodable
        path = self.tmp / "ids.jsonl"
        path.write_bytes((line + "\n" + line + "\n").encode("ascii"))
        _records, errors = retro.load_records(path)
        self.assertHasError(errors, "duplicates line 1")
        for error in errors:
            error.encode("utf-8")

    def test_append_of_a_lone_surrogate_is_exit_1_not_a_traceback(self):
        record = make_record(notes="x\ud800")
        code, out, err = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(record))
        self.assertEqual((code, out), (1, ""))
        self.assertIn("cannot be encoded as UTF-8", err)
        self.assertFalse(self.log.exists())

    def test_log_with_a_lone_surrogate_line_is_skipped_with_a_warning(self):
        path = self.tmp / "surrogate.jsonl"
        path.write_bytes((retro.canonical_json(make_record()) + "\n" + json.dumps(make_record(notes="x\ud800")) + "\n").encode("ascii"))
        code, out, _ = self.run_cli("validate", "--log", str(path))
        self.assertEqual(code, 1)
        self.assertIn("line 2: notes: contains a character that cannot be encoded as UTF-8", out)
        code, _, err = self.run_cli("summary", "--log", str(path))
        self.assertEqual(code, 0)
        self.assertIn("warning: skipped 1", err)


# --------------------------------------------------------------------------- rev 2: duplicate signatures per record (V4 A10)


class DuplicateSignatureTests(RetroCase):
    def test_a_signature_may_appear_once_per_record(self):
        record = make_record(mistakes=[make_mistake(SIG), make_mistake("spec-gap/other-slug")])
        self.assertEqual(retro.validate_record(record), [])

    def test_repeating_a_signature_in_one_record_is_a_validation_error(self):
        record = make_record(mistakes=[make_mistake(SIG), make_mistake("spec-gap/other-slug"), make_mistake(SIG)])
        errors = retro.validate_record(record)
        self.assertHasError(errors, "mistakes[2].signature: duplicates mistakes[0]")
        self.assertEqual(len([e for e in errors if "duplicates" in e]), 1)

    def test_append_rejects_the_duplicate_and_writes_nothing(self):
        record = make_record(mistakes=[make_mistake(SIG), make_mistake(SIG)])
        code, _, err = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(record))
        self.assertEqual(code, 1)
        self.assertIn("duplicates mistakes[0]", err)
        self.assertFalse(self.log.exists())

    def test_validate_reports_the_duplicate_with_its_line_number(self):
        path = self.write_log([make_record(), make_record(date="2026-10-02", mistakes=[make_mistake(SIG), make_mistake(SIG)])])
        code, out, _ = self.run_cli("validate", "--log", str(path))
        self.assertEqual(code, 1)
        self.assertIn("line 2: mistakes[1].signature: duplicates mistakes[0]", out)

    def test_promotions_may_repeat_a_signature_at_different_levels(self):
        record = make_record(
            promotions=[
                {"signature": SIG, "level": "learning", "asset": "learnings/x.md"},
                {"signature": SIG, "level": "checklist", "asset": "workflows/y.md"},
            ]
        )
        self.assertEqual(retro.validate_record(record), [])

    def test_the_same_signature_in_different_records_is_the_normal_recurrence(self):
        self.assertEqual(retro.validate_record(make_record(date="2026-10-02", mistakes=[make_mistake(SIG)])), [])


# --------------------------------------------------------------------------- rev 2: signatures subcommand


def sig_records():
    sa, sb, sc, sd = ("tool-misuse/slug-" + x for x in "abcd")
    return (sa, sb, sc, sd), [
        run_with("2026-10-01", workflow="flow-a", sigs=[sb, sa]),
        run_with("2026-10-02", workflow="flow-b", sigs=[sa]),
        run_with("2026-10-02", workflow="flow-a", sigs=[sc, sd], promos=[(sc, "guard")]),
    ]


class SignaturesTests(RetroCase):
    def test_sorted_by_count_then_last_seen_then_signature(self):
        (sa, sb, sc, sd), records = sig_records()
        items = retro.list_signatures(records)
        self.assertEqual([i["signature"] for i in items], [sa, sc, sd, sb])  # a: 2 runs; c, d: newest, alphabetical; b: oldest
        self.assertEqual([i["count"] for i in items], [2, 1, 1, 1])

    def test_fields(self):
        (sa, sb, sc, sd), records = sig_records()
        by_sig = {i["signature"]: i for i in retro.list_signatures(records)}
        self.assertEqual(by_sig[sa]["workflows"], ["flow-a", "flow-b"])
        self.assertEqual(by_sig[sa]["last_seen"], "2026-10-02")
        self.assertEqual(by_sig[sa]["promoted_level"], "none")
        self.assertEqual(by_sig[sc]["promoted_level"], "guard")
        self.assertEqual(by_sig[sb]["last_seen"], "2026-10-01")
        for item in by_sig.values():
            self.assertEqual(set(item), {"signature", "count", "workflows", "last_seen", "promoted_level"})

    def test_single_occurrences_are_included(self):
        signatures = [i["signature"] for i in retro.list_signatures(load_fixture_records())]
        self.assertIn("safety-near-miss/write-to-wrong-target-without-approval", signatures)
        self.assertEqual(len(signatures), 4)

    def test_highest_promoted_level_is_reported(self):
        records = [run_with("2026-10-01", sigs=[SIG], promos=[(SIG, "checklist"), (SIG, "learning")]), run_with("2026-10-02", sigs=[SIG], promos=[(SIG, "guard")])]
        self.assertEqual(retro.list_signatures(records)[0]["promoted_level"], "guard")

    def test_workflow_filter_counts_only_that_workflow(self):
        (sa, sb, sc, sd), records = sig_records()
        items = retro.list_signatures(records, workflow="flow-b")
        self.assertEqual([(i["signature"], i["count"], i["workflows"]) for i in items], [(sa, 1, ["flow-b"])])
        self.assertEqual(retro.list_signatures(records, workflow="missing-flow"), [])

    def test_a_signature_in_two_mistake_entries_of_one_run_counts_once(self):
        # not reachable through validated input (see DuplicateSignatureTests) but the count stays per run
        self.assertEqual(retro.list_signatures([run_with("2026-10-01", sigs=[SIG, SIG])])[0]["count"], 1)

    def test_fixture_known_values(self):
        items = retro.list_signatures(load_fixture_records())
        self.assertEqual(
            [(i["signature"], i["count"], i["last_seen"], i["promoted_level"]) for i in items],
            [
                ("spec-gap/ambiguous-output-format", 3, "2026-09-25", "guard"),
                ("tool-misuse/unquoted-path-with-spaces", 3, "2026-09-10", "none"),
                ("validation-gap/schema-check-skips-empty-columns", 2, "2026-09-17", "learning"),
                ("safety-near-miss/write-to-wrong-target-without-approval", 1, "2026-09-22", "none"),
            ],
        )

    def test_text_output(self):
        code, out, err = self.run_cli("signatures", "--log", str(VALID_LOG))
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(
            out.splitlines(),
            [
                "3x spec-gap/ambiguous-output-format  last seen 2026-09-25  promoted: guard  workflows: release-notes-drafting",
                "3x tool-misuse/unquoted-path-with-spaces  last seen 2026-09-10  promoted: none  workflows: dataset-validation, release-notes-drafting, report-publishing",
                "2x validation-gap/schema-check-skips-empty-columns  last seen 2026-09-17  promoted: learning  workflows: dataset-validation",
                "1x safety-near-miss/write-to-wrong-target-without-approval  last seen 2026-09-22  promoted: none  workflows: report-publishing",
            ],
        )

    def test_json_output(self):
        code, out, _ = self.run_cli("signatures", "--json", "--log", str(VALID_LOG))
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertEqual(set(data), {"signatures"})
        self.assertEqual(data["signatures"], retro.list_signatures(load_fixture_records()))

    def test_workflow_flag(self):
        code, out, _ = self.run_cli("signatures", "--workflow", "dataset-validation", "--log", str(VALID_LOG))
        self.assertEqual(code, 0)
        self.assertEqual(len(out.splitlines()), 2)
        self.assertIn("2x validation-gap/schema-check-skips-empty-columns", out)
        self.assertNotIn("safety-near-miss", out)

    def test_empty_messages_and_exit_codes(self):
        absent = str(self.tmp / "absent.jsonl")
        self.assertEqual(self.run_cli("signatures", "--log", absent), (0, "no signatures recorded\n", ""))
        self.assertEqual(self.run_cli("signatures", "--workflow", "nope", "--log", str(VALID_LOG))[:2], (0, "no signatures recorded for nope\n"))
        code, out, _ = self.run_cli("signatures", "--json", "--log", absent)
        self.assertEqual((code, json.loads(out)), (0, {"signatures": []}))
        self.assertEqual(self.run_cli("signatures", "--log", str(self.tmp))[0], 2)
        self.assertEqual(self.run_cli("signatures", "--nope", "--log", absent)[0], 2)

    def test_signatures_uses_env_log_and_is_listed_in_help(self):
        os.environ[retro.ENV_LOG] = str(VALID_LOG)
        self.assertEqual(self.run_cli("signatures")[0], 0)
        out = self.run_cli("--help")[1]
        self.assertIn("signatures", out)


# --------------------------------------------------------------------------- rev 2: under-reporting warnings


def rec_with(metrics=None, mistakes=None):
    return make_record(metrics=metrics, mistakes=mistakes if mistakes is not None else [])


class UnderReportingTests(RetroCase):
    def warn(self, **kw):
        return retro.underreporting_warnings(rec_with(**kw))

    def test_clean_record_has_no_warnings(self):
        self.assertEqual(self.warn(), [])
        self.assertEqual(retro.underreporting_warnings(BASE), [])

    def test_escaped_defects_need_a_ci_user_or_post_release_mistake(self):
        for source, expected in (("ci", 0), ("user", 0), ("post-release", 0), ("self-review", 1), ("validator", 1), ("tool-error", 1)):
            with self.subTest(source=source):
                warnings = self.warn(metrics={"escaped_defects": 2}, mistakes=[make_mistake(source=source)])
                self.assertEqual(len([w for w in warnings if w.startswith("escaped_defects is 2")]), expected, warnings)
        self.assertEqual(len(self.warn(metrics={"escaped_defects": 1})), 1)  # no mistakes at all
        self.assertEqual(self.warn(metrics={"escaped_defects": 0}), [])

    def test_user_corrections_need_a_user_sourced_mistake(self):
        for source, expected in (("user", 0), ("ci", 1), ("self-review", 1)):
            with self.subTest(source=source):
                warnings = self.warn(metrics={"user_corrections": 3}, mistakes=[make_mistake(source=source)])
                self.assertEqual(len([w for w in warnings if w.startswith("user_corrections is 3")]), expected, warnings)

    def test_one_user_mistake_satisfies_both_checks(self):
        warnings = self.warn(metrics={"escaped_defects": 1, "user_corrections": 1}, mistakes=[make_mistake(source="user")])
        self.assertEqual(warnings, [])

    def test_empty_mistakes_with_first_pass_below_tasks_or_tool_errors(self):
        warnings = self.warn(metrics={"tasks": 4, "first_pass": 3})
        self.assertEqual(len(warnings), 1)
        self.assertIn("first_pass (3) < tasks (4) but mistakes is empty", warnings[0])
        warnings = self.warn(metrics={"tool_errors": 2})
        self.assertEqual(len(warnings), 1)
        self.assertIn("tool_errors is 2 but mistakes is empty", warnings[0])
        both = self.warn(metrics={"tasks": 4, "first_pass": 3, "tool_errors": 2})
        self.assertEqual(len(both), 1)
        self.assertIn("first_pass (3) < tasks (4) and tool_errors is 2", both[0])

    def test_non_empty_mistakes_silence_the_third_check(self):
        self.assertEqual(self.warn(metrics={"tasks": 4, "first_pass": 1, "tool_errors": 3}, mistakes=[make_mistake()]), [])

    def test_all_three_conditions_can_fire_together(self):
        warnings = self.warn(metrics={"tasks": 4, "first_pass": 2, "escaped_defects": 1, "user_corrections": 1, "tool_errors": 1})
        self.assertEqual(len(warnings), 3)

    def test_validate_prints_warnings_on_stderr_and_keeps_exit_0(self):
        path = self.write_log([make_record(), rec_with(metrics={"user_corrections": 1}), make_record(date="2026-10-02")])
        # make_record() above is clean; line 2 under-reports user corrections
        code, out, err = self.run_cli("validate", "--log", str(path))
        self.assertEqual((code, out), (0, "ok: 3 records\n"))
        self.assertEqual(err, "warning: line 2: user_corrections is 1 but no mistake has source user (possible under-reporting)\n")

    def test_validate_exit_1_is_unchanged_and_warnings_still_go_to_stderr(self):
        valid = rec_with(metrics={"escaped_defects": 1})
        invalid = make_record(date="2026-10-02", outcome="nope")
        path = self.write_log([valid, invalid])
        code, out, err = self.run_cli("validate", "--log", str(path))
        self.assertEqual(code, 1)
        self.assertTrue(out.startswith("line 2: outcome:"))
        self.assertNotIn("warning", out)
        self.assertEqual(err.count("warning: line 1: escaped_defects is 1"), 1)

    def test_validate_on_the_clean_fixture_prints_no_warnings(self):
        self.assertEqual(self.run_cli("validate", "--log", str(VALID_LOG))[2], "")

    def test_append_warns_on_stderr_but_still_appends_and_exits_0(self):
        record = rec_with(metrics={"tasks": 4, "first_pass": 3})
        code, out, err = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(record))
        self.assertEqual(code, 0)
        self.assertEqual(out, retro.generate_run_id(record) + "\n")  # stdout carries only the run_id
        self.assertEqual(err.count("warning: "), 1)
        self.assertIn("first_pass (3) < tasks (4) but mistakes is empty", err)
        self.assertEqual(len(self.log.read_text(encoding="utf-8").splitlines()), 1)

    def test_append_of_a_clean_record_is_silent(self):
        self.assertEqual(self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(make_record()))[2], "")

    def test_failed_append_prints_no_warnings(self):
        record = rec_with(metrics={"tool_errors": 1})
        record["outcome"] = "nope"
        code, _, err = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(record))
        self.assertEqual(code, 1)
        self.assertNotIn("warning:", err)

    def test_analysis_commands_stay_quiet_about_under_reporting(self):
        path = self.write_log([rec_with(metrics={"escaped_defects": 1})])
        for command in (["summary"], ["candidates"], ["signatures"], ["preflight", "--workflow", "example-flow"]):
            with self.subTest(command=command):
                self.assertEqual(self.run_cli(*command, "--log", str(path))[2], "")

    def test_load_records_collects_warnings_only_when_asked(self):
        path = self.write_log([rec_with(metrics={"tool_errors": 2})])
        warnings = []
        records, errors = retro.load_records(path, warnings)
        self.assertEqual((len(records), errors), (1, []))
        self.assertEqual(len(warnings), 1)
        self.assertTrue(warnings[0].startswith("line 1: tool_errors is 2"))
        self.assertEqual(retro.load_records(path), (records, []))


# --------------------------------------------------------------------------- rev 2: input encodings and remaining gaps (V2 R6/R8)


class InputEncodingAndGapTests(RetroCase):
    def test_utf16_record_file_with_a_bom_is_accepted(self):
        record = make_record(notes="café ✓")
        path = self.tmp / "utf16.json"
        path.write_bytes(json.dumps(record).encode("utf-16"))  # PowerShell 5.1 redirection writes this
        code, out, _ = self.run_cli("append", "--record", str(path), "--log", str(self.log))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(self.log.read_text(encoding="utf-8"))["notes"], "café ✓")

    def test_broken_utf16_is_exit_1(self):
        path = self.tmp / "bad16.json"
        path.write_bytes(b"\xff\xfe{")  # odd trailing byte
        code, _, err = self.run_cli("append", "--record", str(path), "--log", str(self.log))
        self.assertEqual(code, 1)
        self.assertIn("UTF-8", err)

    def test_stdin_bom_is_stripped(self):
        payload = b"\xef\xbb\xbf" + json.dumps(make_record()).encode("utf-8")
        code, out, _ = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=payload)
        self.assertEqual((code, out), (0, retro.generate_run_id(make_record()) + "\n"))

    def test_stdin_utf16_is_accepted(self):
        code, _, _ = self.run_cli("append", "--record", "-", "--log", str(self.log), stdin=json.dumps(make_record()).encode("utf-16"))
        self.assertEqual(code, 0)

    def test_preflight_ties_fall_back_to_log_order_not_alphabet(self):
        x, y = "tool-misuse/slug-x", "tool-misuse/slug-y"
        records = [make_record(date="2026-10-01", mistakes=[make_mistake(y)]), make_record(date="2026-10-01", mistakes=[make_mistake(x)])]
        self.assertEqual([p["signature"] for p in retro.preflight(records, "example-flow")["pitfalls"]], [y, x])

    def test_run_id_hash_is_not_flagged_as_security_use(self):
        # hashlib.sha1(..., usedforsecurity=False) keeps FIPS-enabled interpreters working
        with mock.patch.object(retro.hashlib, "sha1", wraps=hashlib.sha1) as spy:
            retro.generate_run_id(make_record())
        self.assertEqual(spy.call_args.kwargs.get("usedforsecurity"), False)



if __name__ == "__main__":
    unittest.main()
