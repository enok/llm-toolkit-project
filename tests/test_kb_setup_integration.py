"""Pins the knowledge-base setup integration contract (bootstrap, INFRA, templates)."""

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SH = ROOT / "scripts" / "bootstrap-dev.sh"
BOOTSTRAP_PS1 = ROOT / "scripts" / "bootstrap-dev.ps1"
KB_STEPS = ("init", "up --build", "index", "schedule install")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def dry_run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(BOOTSTRAP_SH), "--dry-run", *args],
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
    )


def kb_dry_run_lines(output: str) -> list:
    return [
        line.split("kb.py", 1)[1].strip()
        for line in output.splitlines()
        if line.startswith("[dry-run]") and "kb.py" in line
    ]


class UsageTextTests(unittest.TestCase):
    def test_sh_usage_lists_new_options(self) -> None:
        text = read(BOOTSTRAP_SH)
        self.assertIn("--no-kb", text)
        self.assertIn("--kb-data-dir <path>", text)

    def test_ps1_usage_lists_new_options(self) -> None:
        text = read(BOOTSTRAP_PS1)
        self.assertIn("[-NoKb]", text)
        self.assertIn("[-KbDataDir <path>]", text)
        self.assertIn("[switch]$NoKb", text)
        self.assertIn("[string]$KbDataDir", text)

    def test_both_scripts_keep_step_order_and_never_install_the_hook(self) -> None:
        for path in (BOOTSTRAP_SH, BOOTSTRAP_PS1):
            text = read(path)
            self.assertIn("schedule", text)
            self.assertIn("hook install", text)  # printed as a next step only
            self.assertNotRegex(text, r"(run|&)[^\n]*hook['\", ]+install")
            self.assertIn("Docker with compose is missing or its daemon is not running", text)

    def test_ps1_resolves_python_separately_from_docker(self) -> None:
        text = read(BOOTSTRAP_PS1)
        self.assertLess(text.index("Test-Command 'py'"), text.index("Test-Command 'python')"))
        self.assertLess(text.index("Test-Command 'python')"), text.index("Test-Command 'python3'"))
        self.assertIn("@('py', '-3')", text)
        self.assertIn("Knowledge base skipped: python3 is missing", text)
        self.assertLess(
            text.index("-not $kbPython"),
            text.index("Docker with compose is missing"),
        )

    def test_ps1_hint_is_one_line_with_quoted_paths_and_no_ampersands(self) -> None:
        text = read(BOOTSTRAP_PS1)
        self.assertIn("-join '; '", text)
        self.assertIn("ConvertTo-QuotedArg", text)
        self.assertNotIn("-join ' && '", text)
        self.assertNotIn("chroma", text.lower())

    def test_sh_hint_quotes_paths(self) -> None:
        text = read(BOOTSTRAP_SH)
        self.assertIn("printf '%q '", text)
        self.assertNotIn('KB_LATER="${KB_INIT[*]}', text)
        self.assertNotIn("chroma", text.lower())

    def test_ps1_declares_steps_in_order(self) -> None:
        text = read(BOOTSTRAP_PS1)
        order = [text.index(token) for token in ("'init'", "'up', '--build'", "'index'", "'schedule', 'install'")]
        self.assertEqual(sorted(order), order)


@unittest.skipUnless(shutil.which("bash"), "bash is not available on PATH")
class DryRunTests(unittest.TestCase):
    def test_dry_run_prints_four_commands_in_order(self) -> None:
        result = dry_run()
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(list(KB_STEPS), kb_dry_run_lines(result.stdout))

    def test_dry_run_executes_nothing(self) -> None:
        result = dry_run()
        self.assertNotIn("\n+ ", "\n" + result.stdout)
        self.assertNotIn("Knowledge base skipped", result.stdout)

    def test_full_profile_includes_step(self) -> None:
        self.assertEqual(list(KB_STEPS), kb_dry_run_lines(dry_run("--full").stdout))

    def test_data_dir_is_passed_to_init(self) -> None:
        lines = kb_dry_run_lines(dry_run("--kb-data-dir", "/tmp/kb-data-example").stdout)
        self.assertEqual("init --data-dir /tmp/kb-data-example", lines[0])
        self.assertEqual(list(KB_STEPS[1:]), lines[1:])

    def test_dry_run_with_space_in_toolkit_path(self) -> None:
        with tempfile.TemporaryDirectory(prefix="kb setup ") as tmp:
            scripts = Path(tmp) / "tool kit" / "scripts"
            scripts.mkdir(parents=True)
            copy = scripts / "bootstrap-dev.sh"
            shutil.copy(BOOTSTRAP_SH, copy)
            result = subprocess.run(
                ["bash", str(copy), "--dry-run"], cwd=tmp, check=False, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(list(KB_STEPS), kb_dry_run_lines(result.stdout))

    def test_no_kb_skips_step(self) -> None:
        result = dry_run("--no-kb")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], kb_dry_run_lines(result.stdout))
        self.assertNotIn("== Knowledge base ==", result.stdout)

    def test_minimal_skips_step(self) -> None:
        result = dry_run("--minimal")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], kb_dry_run_lines(result.stdout))
        self.assertNotIn("== Knowledge base ==", result.stdout)

    def test_hook_is_only_a_printed_next_step(self) -> None:
        out = dry_run().stdout
        self.assertNotIn("[dry-run] python3 " + str(ROOT / "scripts" / "kb.py") + " hook", out)
        self.assertIn("explicit opt-in", out)

    def test_kb_data_dir_requires_value(self) -> None:
        result = subprocess.run(
            ["bash", str(BOOTSTRAP_SH), "--dry-run", "--kb-data-dir"],
            cwd=ROOT, check=False, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60,
        )
        self.assertEqual(2, result.returncode)


class InfraPassThroughTests(unittest.TestCase):
    def test_infra_sh_passes_options_through(self) -> None:
        text = read(ROOT / "INFRA.sh")
        self.assertIn("--no-kb", text)
        self.assertIn("--kb-data-dir", text)
        self.assertIn("BOOTSTRAP_ARGS+=(--no-kb)", text)
        self.assertIn('BOOTSTRAP_ARGS+=(--kb-data-dir "$KB_DATA_DIR")', text)

    def test_infra_ps1_passes_options_through(self) -> None:
        text = read(ROOT / "INFRA.ps1")
        self.assertIn("[switch]$NoKb", text)
        self.assertIn("[string]$KbDataDir", text)
        self.assertIn("$bootstrapArgs.NoKb = $true", text)
        self.assertIn("$bootstrapArgs.KbDataDir = $KbDataDir", text)

    @unittest.skipUnless(shutil.which("bash"), "bash is not available on PATH")
    def test_infra_sh_default_is_plan_with_kb_and_options_forwarded(self) -> None:
        def run(*args: str) -> str:
            result = subprocess.run(
                ["bash", str(ROOT / "INFRA.sh"), *args], cwd=ROOT, check=False,
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            return result.stdout

        self.assertEqual(list(KB_STEPS), kb_dry_run_lines(run()))
        self.assertEqual([], kb_dry_run_lines(run("--no-kb")))
        self.assertEqual("init --data-dir /tmp/kb-x", kb_dry_run_lines(run("--kb-data-dir", "/tmp/kb-x"))[0])


class TemplateDirectiveTests(unittest.TestCase):
    def check_template(self, path: Path, section_start: str) -> None:
        text = read(path)
        self.assertIn("rules/knowledge-base.md", text)
        self.assertIn("kb.py", text)
        self.assertRegex(text, r"kb\.py[^\n]* search")
        self.assertRegex(text, r"kb\.py[^\n]* add|kb\.py`?\s+add")
        self.assertIn("learnings/INDEX.md", text)
        self.assertIn("say so", text)
        block = text[text.index(section_start):]
        directive = re.split(r"\n\n## ", block, maxsplit=1)[0].strip("\n").splitlines()
        self.assertLessEqual(len(directive) - (1 if directive[0].startswith("#") else 0), 6)

    def test_global_directive(self) -> None:
        self.check_template(
            ROOT / "scripts/templates/global-agent-directive.md",
            "## Knowledge base first, write back",
        )

    def test_consumer_template(self) -> None:
        path = ROOT / "scripts/templates/consumer-AGENTS.md"
        self.check_template(path, "4. **Knowledge base first, write back.**")
        # setup-repo extracts everything from this heading to end of file, so the
        # directive must stay inside that section.
        text = read(path)
        self.assertLess(
            text.index("## Mandatory agent orchestration (all LLM assistants)"),
            text.index("Knowledge base first, write back"),
        )

    def test_global_template_keeps_toolkit_root_placeholder_only(self) -> None:
        text = read(ROOT / "scripts/templates/global-agent-directive.md")
        self.assertNotIn("<!-- BEGIN LLM-TOOLKIT GLOBAL -->", text)
        self.assertIn("{{TOOLKIT_ROOT}}/scripts/kb.py", text)


class RepoSetupPromptTests(unittest.TestCase):
    def test_prompt_checks_status_only(self) -> None:
        text = read(ROOT / "docs/repo-setup-prompt.md")
        self.assertIn("kb.py status", text)
        self.assertIn("per machine", text)


if __name__ == "__main__":
    unittest.main()
