from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-skills-with-skillspector.py"
SPEC = importlib.util.spec_from_file_location("validate_skills_with_skillspector", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)

UNSUPPORTED = "Error: Safe file output is unsupported on this platform. omit --output"
REPORT = {"issues": [], "risk_assessment": {"severity": "low", "score": 1}}


class FakeRunner:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, command, capture_separately):
        self.calls.append((command, capture_separately))
        return self.responses.pop(0)


class CommandBuilderTests(unittest.TestCase):
    def test_with_output_flag_by_default(self):
        cmd = mod.scanner_command(Path("s"), Path("r.json"), False)
        self.assertEqual(cmd[cmd.index("--output") + 1], "r.json")
        self.assertIn("--no-llm", cmd)

    def test_without_output_flag(self):
        cmd = mod.scanner_command(Path("s"), Path("r.json"), True, use_output_flag=False)
        self.assertNotIn("--output", cmd)
        self.assertNotIn("r.json", cmd)
        self.assertNotIn("--no-llm", cmd)


class ExtractJsonTests(unittest.TestCase):
    def test_clean_json(self):
        self.assertEqual(json.loads(mod.extract_json_document('{"a": 1}')), {"a": 1})

    def test_noise_around_json(self):
        text = 'INFO start\n{"a": {"b": 2}}\nINFO done }\n'
        self.assertIsNone(mod.extract_json_document(text))  # trailing "}" breaks parse
        text = 'INFO start\n{"a": {"b": 2}}\nINFO done\n'
        self.assertEqual(json.loads(mod.extract_json_document(text)), {"a": {"b": 2}})

    def test_invalid_text(self):
        self.assertIsNone(mod.extract_json_document("no json here"))
        self.assertIsNone(mod.extract_json_document("{not json}"))
        self.assertIsNone(mod.extract_json_document("} {"))


class RunScanTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)

    def test_fallback_then_remembered(self):
        runner = FakeRunner([
            (1, UNSUPPORTED, ""),
            (0, "log\n" + json.dumps(REPORT) + "\n", "warn"),
            (0, json.dumps(REPORT), ""),
        ])
        state = mod.ScanState()
        first = self.dir / "a.json"
        code, _, err = mod.run_scan(Path("a"), first, False, runner, state)
        self.assertEqual((code, err), (0, None))
        self.assertEqual(json.loads(first.read_text()), REPORT)
        self.assertIn("--output", runner.calls[0][0])
        self.assertNotIn("--output", runner.calls[1][0])
        self.assertTrue(runner.calls[1][1])

        second = self.dir / "b.json"
        code, _, err = mod.run_scan(Path("b"), second, False, runner, state)
        self.assertEqual((code, err), (0, None))
        self.assertEqual(len(runner.calls), 3)  # no --output attempt for 2nd skill
        self.assertNotIn("--output", runner.calls[2][0])
        self.assertTrue(second.is_file())

    def test_fallback_invalid_json_is_failure(self):
        runner = FakeRunner([(1, UNSUPPORTED, ""), (0, "garbage", "")])
        code, _, err = mod.run_scan(
            Path("a"), self.dir / "a.json", False, runner, mod.ScanState()
        )
        self.assertNotEqual(code, 0)
        self.assertIn("no valid JSON", err)
        self.assertNotIn("\n", err)
        self.assertFalse((self.dir / "a.json").exists())

    def test_other_error_is_failed_scan_without_fallback(self):
        runner = FakeRunner([(2, "Error: boom", "")])
        state = mod.ScanState()
        code, out, err = mod.run_scan(Path("a"), self.dir / "a.json", False, runner, state)
        self.assertEqual((code, err), (2, None))
        self.assertEqual(out, "Error: boom")
        self.assertEqual(len(runner.calls), 1)
        self.assertFalse(state.stdout_mode)

    def test_success_with_output_flag_unchanged(self):
        runner = FakeRunner([(0, "", "")])
        code, _, err = mod.run_scan(
            Path("a"), self.dir / "a.json", False, runner, mod.ScanState()
        )
        self.assertEqual((code, err), (0, None))
        self.assertEqual(len(runner.calls), 1)


if __name__ == "__main__":
    unittest.main()
