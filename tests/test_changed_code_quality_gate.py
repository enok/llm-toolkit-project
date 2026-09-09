from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "changed_code_quality_gate.py"
WORKFLOW = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "changed-code-quality-gate.yml"
SPEC = importlib.util.spec_from_file_location("changed_code_quality_gate", SCRIPT)
assert SPEC and SPEC.loader
gate = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = gate
SPEC.loader.exec_module(gate)


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    return result.stdout.strip()


class ConfigTests(unittest.TestCase):
    def test_rejects_duplicate_and_unknown_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            duplicate = root / "duplicate.json"
            duplicate.write_text('{"version":1,"version":1}', encoding="utf-8")
            with self.assertRaisesRegex(gate.GateError, "duplicate"):
                gate.load_config(root, duplicate)
            unknown = root / "unknown.json"
            unknown.write_text('{"version":1,"command":"bad"}', encoding="utf-8")
            with self.assertRaisesRegex(gate.GateError, "unknown"):
                gate.load_config(root, unknown)

    def test_rejects_analyzer_override_and_oversized_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            unsupported = root / "unsupported.json"
            unsupported.write_text('{"version":1,"analyzers":[]}', encoding="utf-8")
            with self.assertRaisesRegex(gate.GateError, "unknown"):
                gate.load_config(root, unsupported)
            oversized = root / "oversized.json"
            oversized.write_bytes(b" " * (gate.MAX_CONFIG_BYTES + 1))
            with self.assertRaisesRegex(gate.GateError, "64 KiB"):
                gate.load_config(root, oversized)


class WorkflowContractTests(unittest.TestCase):
    def test_new_branch_uses_repository_working_trunk(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("BASE_BRANCH: main", workflow)
        self.assertNotIn("github.event.repository.default_branch", workflow)

    def test_push_policy_uses_pre_push_or_working_trunk(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("ref: ${{ github.event.before }}", workflow)
        self.assertIn("ref: main", workflow)

    def test_executable_dependencies_are_immutable(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertNotIn("actions/checkout@v", workflow)
        self.assertNotIn("actions/setup-python@v", workflow)
        self.assertIn("pip install --require-hashes", workflow)
        self.assertIn(".github/requirements/semgrep.lock", workflow)


class ScopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        run_git(self.root, "init", "-q")
        run_git(self.root, "config", "user.email", "test@example.invalid")
        run_git(self.root, "config", "user.name", "Quality Gate Test")
        (self.root / "kept.py").write_text("first = 1\nsecond = 2\n", encoding="utf-8")
        (self.root / "deleted.py").write_text("delete_me = True\n", encoding="utf-8")
        (self.root / "vendor").mkdir()
        (self.root / "vendor" / "ignored.py").write_text("ignored = True\n", encoding="utf-8")
        run_git(self.root, "add", ".")
        run_git(self.root, "commit", "-qm", "base")
        self.base = run_git(self.root, "rev-parse", "HEAD")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def args(self, **overrides: object) -> argparse.Namespace:
        values = {"base": None, "head": None, "event": "local", "config": None, "scope_only": False}
        values.update(overrides)
        return argparse.Namespace(**values)

    def config(self) -> dict[str, object]:
        return {"version": 1}

    def test_local_scope_includes_all_changed_source_and_skips_deleted_binary(self) -> None:
        (self.root / "kept.py").write_text("first = 1\nsecond = 3\n", encoding="utf-8")
        (self.root / "staged.js").write_text("const staged = true;\n", encoding="utf-8")
        run_git(self.root, "add", "staged.js")
        (self.root / "untracked file.ts").write_text("const fresh = true;\n", encoding="utf-8")
        (self.root / "binary.py").write_bytes(b"x\0y")
        (self.root / "vendor" / "ignored.py").write_text("ignored = False\n", encoding="utf-8")
        (self.root / "dist").mkdir()
        (self.root / "dist" / "app.js").write_text("eval(userInput);\n", encoding="utf-8")
        (self.root / "payload.min.js").write_text("eval(userInput);", encoding="utf-8")
        (self.root / "deleted.py").unlink()
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertEqual(
            {"dist/app.js", "kept.py", "payload.min.js", "staged.js", "untracked file.ts", "vendor/ignored.py"},
            set(scope.files),
        )
        self.assertEqual(((2, 2),), scope.lines["kept.py"])
        self.assertEqual("binary file", scope.skipped["binary.py"])
        self.assertNotIn("deleted.py", scope.files)

    def test_gitignored_untracked_source_is_in_scope(self) -> None:
        (self.root / ".gitignore").write_text("ignored.js\n", encoding="utf-8")
        (self.root / "ignored.js").write_text("eval(userInput);\n", encoding="utf-8")
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertIn("ignored.js", scope.files)

    def test_binary_supported_source_blocks_gate(self) -> None:
        (self.root / "binary.py").write_bytes(b"x\0y")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.root)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(3, result.returncode)
        report = json.loads(result.stdout)
        self.assertEqual("blocked", report["status"])
        self.assertEqual("binary file", report["skipped"]["binary.py"])

    def test_semgrepignore_and_inline_suppression_stay_in_scope(self) -> None:
        (self.root / ".semgrepignore").write_text("kept.py\n", encoding="utf-8")
        (self.root / "kept.py").write_text(
            "first = eval(user_input)  # nosemgrep\nsecond = 2\n",
            encoding="utf-8",
        )
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertIn("kept.py", scope.files)
        self.assertEqual(((1, 1),), scope.lines["kept.py"])

    def test_base_scope_includes_committed_branch_change(self) -> None:
        (self.root / "kept.py").write_text("first = 9\nsecond = 2\n", encoding="utf-8")
        run_git(self.root, "add", "kept.py")
        run_git(self.root, "commit", "-qm", "branch change")
        scope = gate.build_scope(self.root, self.args(base=self.base), self.config())
        self.assertEqual(("kept.py",), scope.files)
        self.assertEqual(((1, 1),), scope.lines["kept.py"])

    def test_candidate_gitattributes_cannot_hide_changed_lines(self) -> None:
        (self.root / ".gitattributes").write_text("*.py -diff\n", encoding="utf-8")
        (self.root / "kept.py").write_text("first = eval(user_input)\nsecond = 2\n", encoding="utf-8")
        run_git(self.root, "add", ".gitattributes", "kept.py")
        run_git(self.root, "commit", "-qm", "candidate attributes")
        scope = gate.build_scope(self.root, self.args(base=self.base), self.config())
        self.assertEqual(((1, 1),), scope.lines["kept.py"])

    def test_pull_request_rejects_checkout_head_mismatch(self) -> None:
        (self.root / "kept.py").write_text("first = 2\nsecond = 2\n", encoding="utf-8")
        run_git(self.root, "add", "kept.py")
        run_git(self.root, "commit", "-qm", "new head")
        with self.assertRaisesRegex(gate.GateError, "checkout"):
            gate.resolve_range(self.root, self.args(event="pull_request", base=self.base, head=self.base), self.config())

    def test_branch_creation_requires_trusted_base(self) -> None:
        head = run_git(self.root, "rev-parse", "HEAD")
        with self.assertRaisesRegex(gate.GateError, "explicit trusted base"):
            gate.resolve_range(self.root, self.args(event="push", base="0" * 40, head=head), self.config())

    def test_push_rejects_checkout_head_mismatch(self) -> None:
        (self.root / "kept.py").write_text("first = 3\nsecond = 2\n", encoding="utf-8")
        run_git(self.root, "add", "kept.py")
        run_git(self.root, "commit", "-qm", "new push head")
        with self.assertRaisesRegex(gate.GateError, "checkout"):
            gate.resolve_range(self.root, self.args(event="push", base=self.base, head=self.base), self.config())

    def test_java_is_supported_and_other_unconfigured_languages_block(self) -> None:
        (self.root / "App.java").write_text("class App {}\n", encoding="utf-8")
        (self.root / "main.go").write_text("package main\n", encoding="utf-8")
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertIn("App.java", scope.files)
        self.assertEqual("unsupported code language", scope.skipped["main.go"])

    def test_trusted_semgrep_policy_contains_java_quality_rules(self) -> None:
        rules = (SCRIPT.parents[1] / ".semgrep.yml").read_text(encoding="utf-8")
        self.assertIn("languages: [java]", rules)
        for rule_id in (
            "changed-code-java-runtime-exec",
            "changed-code-java-processbuilder-shell",
            "changed-code-java-processbuilder-variable-command",
            "changed-code-java-print-stack-trace",
            "changed-code-java-system-output",
            "changed-code-java-direct-object-deserialization",
        ):
            self.assertIn(f"id: {rule_id}", rules)

    def test_alternate_javascript_typescript_extensions_are_supported(self) -> None:
        for name in ("a.mjs", "b.cjs", "c.mts", "d.cts"):
            (self.root / name).write_text("eval(userInput);\n", encoding="utf-8")
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertTrue({"a.mjs", "b.cjs", "c.mts", "d.cts"}.issubset(scope.files))

    def test_shell_and_powershell_scripts_are_supported(self) -> None:
        (self.root / "safe.sh").write_text("#!/usr/bin/env bash\necho safe\n", encoding="utf-8")
        (self.root / "safe.ps1").write_text("Write-Output 'safe'\n", encoding="utf-8")
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertTrue({"safe.sh", "safe.ps1"}.issubset(scope.files))

    def test_unknown_source_and_source_symlink_fail_closed(self) -> None:
        (self.root / "script.unknown").write_text("#!/usr/bin/env python\nprint('x')\n", encoding="utf-8")
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertEqual("unrecognized changed file type", scope.skipped["script.unknown"])
        with mock.patch.object(Path, "is_symlink", return_value=True):
            _, reason = gate.safe_code_file(self.root, "linked.py", gate.DEFAULT_EXCLUDES)
        self.assertEqual("unsafe changed source symlink", reason)

    def test_python_bytecode_is_non_code_build_output(self) -> None:
        (self.root / "module.pyc").write_bytes(b"compiled")
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertEqual("non-code file", scope.skipped["module.pyc"])

    def test_cursor_ignore_metadata_is_non_code(self) -> None:
        for name in (".cursorignore", ".cursorindexingignore"):
            (self.root / name).write_text("generated selection metadata\n", encoding="utf-8")
        scope = gate.build_scope(self.root, self.args(), self.config())
        self.assertEqual("non-code file", scope.skipped[".cursorignore"])
        self.assertEqual("non-code file", scope.skipped[".cursorindexingignore"])
        self.assertIn("unrecognized changed file type", gate.BLOCKING_SKIP_REASONS)
        self.assertIn("unsafe changed source symlink", gate.BLOCKING_SKIP_REASONS)


class AnalyzerTests(unittest.TestCase):
    def test_subscope_partitions_analyzers_without_losing_ranges(self) -> None:
        scope = gate.Scope(None, "b" * 40, ("App.java", "INFRA.sh"), {"App.java": ((2, 3),), "INFRA.sh": ((4, 4),)}, {})
        java_scope = gate.subscope(scope, gate.SEMGREP_SUFFIXES)
        script_scope = gate.subscope(scope, gate.SCRIPT_SUFFIXES)
        self.assertEqual(("App.java",), java_scope.files)
        self.assertEqual(((4, 4),), script_scope.lines["INFRA.sh"])

    def test_script_policy_filters_to_changed_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unsafe.ps1").write_text("iex $old\nWrite-Output safe\nInvoke-Expression $new\n", encoding="utf-8")
            scope = gate.Scope(None, "b" * 40, ("unsafe.ps1",), {"unsafe.ps1": ((3, 3),)}, {})
            completed = subprocess.CompletedProcess([], 0, b"", b"")
            with mock.patch.object(gate, "_script_syntax_command", return_value=["pwsh"]), mock.patch.object(gate.subprocess, "run", return_value=completed):
                result = gate.run_script_policy(root, scope)
            self.assertEqual("findings", result["status"])
            self.assertEqual([3], [item["startLine"] for item in result["findings"]])

    def test_script_policy_fails_closed_without_syntax_analyzer(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "safe.sh").write_text("echo safe\n", encoding="utf-8")
            scope = gate.Scope(None, "b" * 40, ("safe.sh",), {"safe.sh": ((1, 1),)}, {})
            with mock.patch.object(gate, "_script_syntax_command", return_value=None):
                result = gate.run_script_policy(root, scope)
            self.assertEqual("unavailable", result["status"])

    def test_bash_syntax_path_remains_posix_on_windows(self) -> None:
        with mock.patch.object(gate.shutil, "which", return_value="bash"):
            command = gate._script_syntax_command(Path("scripts/bootstrap-dev.sh"))
        self.assertEqual("scripts/bootstrap-dev.sh", command[-1])

    def test_script_policy_blocks_common_indirect_execution_primitives(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "unsafe.ps1").write_text("[ScriptBlock]::Create($input)\n", encoding="utf-8")
            scope = gate.Scope(None, "b" * 40, ("unsafe.ps1",), {"unsafe.ps1": ((1, 1),)}, {})
            completed = subprocess.CompletedProcess([], 0, b"", b"")
            with mock.patch.object(gate, "_script_syntax_command", return_value=["pwsh"]), mock.patch.object(gate.subprocess, "run", return_value=completed):
                result = gate.run_script_policy(root, scope)
            self.assertEqual("changed-code-powershell-scriptblock-create", result["findings"][0]["ruleId"])

    def test_script_policy_blocks_powershell_download_aliases(self) -> None:
        completed = subprocess.CompletedProcess([], 0, b"", b"")
        for command in ("curl.exe https://example.invalid/file", "wget https://example.invalid/file", "Start-BitsTransfer -Source https://example.invalid/file"):
            with self.subTest(command=command), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                (root / "unsafe.ps1").write_text(f"{command}\n", encoding="utf-8")
                scope = gate.Scope(None, "b" * 40, ("unsafe.ps1",), {"unsafe.ps1": ((1, 1),)}, {})
                with mock.patch.object(gate, "_script_syntax_command", return_value=["pwsh"]), mock.patch.object(gate.subprocess, "run", return_value=completed):
                    result = gate.run_script_policy(root, scope)
                self.assertEqual("changed-code-powershell-network-download", result["findings"][0]["ruleId"])
    def test_semgrep_filters_findings_to_changed_lines(self) -> None:
        scope = gate.Scope("a" * 40, "b" * 40, ("app.py",), {"app.py": ((5, 7),)}, {})
        payload = {
            "errors": [],
            "paths": {"scanned": ["app.py"], "skipped": []},
            "results": [
                {"check_id": "in", "path": "app.py", "start": {"line": 6}, "end": {"line": 6}, "extra": {"message": "inside"}},
                {"check_id": "out", "path": "app.py", "start": {"line": 2}, "end": {"line": 2}, "extra": {"message": "outside"}},
                {"check_id": "other", "path": "other.py", "start": {"line": 6}, "end": {"line": 6}, "extra": {"message": "other"}},
            ]
        }
        completed = subprocess.CompletedProcess([], 1, json.dumps(payload).encode(), b"")
        with mock.patch.object(gate.shutil, "which", return_value="/trusted/semgrep"), mock.patch.object(gate.subprocess, "run", return_value=completed), mock.patch.object(Path, "is_file", return_value=True):
            result = gate.run_semgrep(Path.cwd(), Path.cwd(), scope)
        self.assertEqual("findings", result["status"])
        self.assertEqual(["in"], [item["ruleId"] for item in result["findings"]])
        self.assertEqual(2, result["broaderRunOutOfScope"])

    def test_semgrep_disables_candidate_suppressions(self) -> None:
        scope = gate.Scope(None, "b" * 40, ("payload.min.js",), {"payload.min.js": ((1, 1),)}, {})
        payload = {"errors": [], "paths": {"scanned": ["payload.min.js"]}, "results": []}
        completed = subprocess.CompletedProcess([], 0, json.dumps(payload).encode(), b"")
        with mock.patch.object(gate.shutil, "which", return_value="/trusted/semgrep"), mock.patch.object(gate.subprocess, "run", return_value=completed) as run, mock.patch.object(Path, "is_file", return_value=True):
            result = gate.run_semgrep(Path.cwd(), Path.cwd(), scope)
        command = run.call_args.args[0]
        self.assertIn("--strict", command)
        for flag in ("--disable-nosem", "--no-git-ignore", "--x-ignore-semgrepignore-files"):
            self.assertIn(flag, command)
        self.assertNotIn("--no-exclude-binary-files", command)
        self.assertNotIn("--no-exclude-minified-files", command)
        self.assertEqual("pass", result["status"])

    def test_multiline_finding_overlaps_changed_line(self) -> None:
        scope = gate.Scope("a" * 40, "b" * 40, ("app.py",), {"app.py": ((5, 5),)}, {})
        payload = {
            "errors": [],
            "paths": {"scanned": ["app.py"], "skipped": []},
            "results": [{
                "check_id": "span", "path": "app.py", "start": {"line": 4},
                "end": {"line": 6}, "extra": {"message": "multiline"},
            }],
        }
        completed = subprocess.CompletedProcess([], 1, json.dumps(payload).encode(), b"")
        with mock.patch.object(gate.shutil, "which", return_value="/trusted/semgrep"), mock.patch.object(gate.subprocess, "run", return_value=completed), mock.patch.object(Path, "is_file", return_value=True):
            result = gate.run_semgrep(Path.cwd(), Path.cwd(), scope)
        self.assertEqual("findings", result["status"])
        self.assertEqual(6, result["findings"][0]["endLine"])

    def test_required_missing_semgrep_is_unavailable(self) -> None:
        scope = gate.Scope(None, "b" * 40, ("app.py",), {"app.py": ((1, 1),)}, {})
        with mock.patch.object(gate.shutil, "which", return_value=None):
            result = gate.run_semgrep(Path.cwd(), Path.cwd(), scope)
        self.assertEqual("unavailable", result["status"])
        self.assertEqual("always", result["required"])

    def test_malformed_semgrep_structure_is_execution_error(self) -> None:
        scope = gate.Scope(None, "b" * 40, ("app.py",), {"app.py": ((1, 1),)}, {})
        completed = subprocess.CompletedProcess([], 0, b'{"results":null,"errors":[],"paths":{"scanned":["app.py"],"skipped":[]}}', b"")
        with mock.patch.object(gate.shutil, "which", return_value="/trusted/semgrep"), mock.patch.object(gate.subprocess, "run", return_value=completed), mock.patch.object(Path, "is_file", return_value=True):
            result = gate.run_semgrep(Path.cwd(), Path.cwd(), scope)
        self.assertEqual("error", result["status"])
        self.assertIn("structure", result["reason"])

    def test_malformed_semgrep_metadata_is_execution_error(self) -> None:
        scope = gate.Scope(None, "b" * 40, ("app.py",), {"app.py": ((1, 1),)}, {})
        completed = subprocess.CompletedProcess([], 0, b'{"results":[{"path":"app.py","start":{"line":1},"end":{"line":1},"extra":[]}],"errors":[],"paths":{"scanned":["app.py"],"skipped":[]}}', b"")
        with mock.patch.object(gate.shutil, "which", return_value="/trusted/semgrep"), mock.patch.object(gate.subprocess, "run", return_value=completed), mock.patch.object(Path, "is_file", return_value=True):
            result = gate.run_semgrep(Path.cwd(), Path.cwd(), scope)
        self.assertEqual("error", result["status"])
        self.assertIn("metadata", result["reason"])

    def test_semgrep_errors_fail_closed(self) -> None:
        scope = gate.Scope(None, "b" * 40, ("app.py",), {"app.py": ((1, 1),)}, {})
        for payload in (
            {"results": [], "errors": [{}], "paths": {"scanned": ["app.py"], "skipped": []}},
            {"results": [], "errors": None, "paths": {"scanned": ["app.py"], "skipped": []}},
        ):
            completed = subprocess.CompletedProcess([], 0, json.dumps(payload).encode(), b"")
            with mock.patch.object(gate.shutil, "which", return_value="/trusted/semgrep"), mock.patch.object(gate.subprocess, "run", return_value=completed), mock.patch.object(Path, "is_file", return_value=True):
                result = gate.run_semgrep(Path.cwd(), Path.cwd(), scope)
            self.assertEqual("error", result["status"])

    def test_missing_or_incomplete_coverage_metadata_fails_closed(self) -> None:
        scope = gate.Scope(None, "b" * 40, ("app.py",), {"app.py": ((1, 1),)}, {})
        payloads = (
            {"results": [], "errors": []},
            {"results": [], "errors": [], "paths": {"scanned": [], "skipped": []}},
            {"results": [], "errors": [], "paths": {"scanned": ["app.py", "extra.py"], "skipped": []}},
            {"results": [], "errors": [], "paths": {"scanned": ["app.py"], "skipped": [{"path": "app.py"}]}},
        )
        for payload in payloads:
            completed = subprocess.CompletedProcess([], 0, json.dumps(payload).encode(), b"")
            with mock.patch.object(gate.shutil, "which", return_value="/trusted/semgrep"), mock.patch.object(gate.subprocess, "run", return_value=completed), mock.patch.object(Path, "is_file", return_value=True):
                result = gate.run_semgrep(Path.cwd(), Path.cwd(), scope)
            self.assertEqual("error", result["status"])


if __name__ == "__main__":
    unittest.main()
