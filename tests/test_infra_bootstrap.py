"""Cross-platform, plan-first INFRA entrypoint contract tests."""

import shutil
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InfraBootstrapContractTests(unittest.TestCase):
    def test_posix_entrypoint_is_plan_first_and_complete(self) -> None:
        text = (ROOT / "INFRA.sh").read_text(encoding="utf-8")
        self.assertIn("--full", text)
        self.assertIn("--agent all", text)
        self.assertIn("--dry-run", text)
        self.assertIn("--apply", text)
        self.assertNotIn("install_slack_cli.py", text)

    def test_windows_entrypoint_is_plan_first_and_complete(self) -> None:
        text = (ROOT / "INFRA.ps1").read_text(encoding="utf-8")
        self.assertIn("Full = $true", text)
        self.assertIn("Agent = 'all'", text)
        self.assertIn("DryRun = -not $Apply", text)
        self.assertIn("[switch]$Apply", text)
        self.assertNotIn("install_slack_cli.py", text)

    @unittest.skipUnless(shutil.which("bash"), "bash is not available on PATH")
    def test_posix_entrypoint_dry_run_plans_without_installing(self) -> None:
        result = subprocess.run(
            ["bash", str(ROOT / "INFRA.sh")],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("LLM toolkit bootstrap", result.stdout)
        self.assertIn("[dry-run]", result.stdout)
        self.assertNotIn("install_slack_cli.py", result.stdout)

    @unittest.skipUnless(
        shutil.which("pwsh") or shutil.which("powershell"),
        "PowerShell (pwsh/powershell) is not available on PATH",
    )
    def test_windows_entrypoint_dry_run_plans_without_installing(self) -> None:
        pwsh = shutil.which("pwsh") or shutil.which("powershell")
        result = subprocess.run(
            [pwsh, "-NoLogo", "-NoProfile", "-NonInteractive", "-File", str(ROOT / "INFRA.ps1")],
            cwd=ROOT,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=120,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("LLM toolkit bootstrap", result.stdout)
        self.assertNotIn("install_slack_cli.py", result.stdout)


if __name__ == "__main__":
    unittest.main()
