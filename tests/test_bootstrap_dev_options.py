"""Pins the opt-in --security-tools / --rtk bootstrap switches and the RTK privacy block."""

import os
import shutil
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP_SH = ROOT / "scripts" / "bootstrap-dev.sh"
BOOTSTRAP_PS1 = ROOT / "scripts" / "bootstrap-dev.ps1"


def dry_run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(BOOTSTRAP_SH), "--dry-run", "--no-kb", *args],
        cwd=ROOT, check=False, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120,
    )


@unittest.skipUnless(shutil.which("bash"), "bash is not available on PATH")
class ShellOptionTests(unittest.TestCase):
    def test_security_tools_are_off_by_default(self) -> None:
        out = dry_run().stdout
        self.assertNotIn("== Security tools ==", out)
        self.assertNotIn("skillspector", out)

    def test_security_tools_switch_runs_the_toolchain_step_with_pinned_pip_tool(self) -> None:
        result = dry_run("--security-tools")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("== Security tools ==", result.stdout)
        # The pin lives in the script; the dry run prints it only when skillspector is missing
        # (CI runners install skillspector before the tests run).
        self.assertIn("skillspector==2.13.7", BOOTSTRAP_SH.read_text(encoding="utf-8"))
        self.assertTrue(
            "skillspector==2.13.7" in result.stdout or "skillspector (already installed)" in result.stdout,
            result.stdout[-2000:],
        )
        self.assertNotIn("\n+ ", "\n" + result.stdout)

    def test_rtk_is_off_by_default(self) -> None:
        self.assertNotIn("== RTK (reviewed version only) ==", dry_run().stdout)

    def test_rtk_switch_runs_the_reviewed_rtk_step(self) -> None:
        result = dry_run("--rtk")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("== RTK (reviewed version only) ==", result.stdout)
        self.assertNotIn("\n+ ", "\n" + result.stdout)

    @unittest.skipUnless(sys.platform.startswith(("linux", "darwin")), "runs a real (stubbed) install: Linux/macOS only")
    def test_a_failing_package_manager_does_not_stop_the_bootstrap(self) -> None:
        # A real (non dry-run) install that fails must be reported, not abort the script.
        # Every package manager the script can pick is stubbed, so nothing is ever installed.
        with tempfile.TemporaryDirectory() as tmp:
            for name in ("sudo", "brew", "apt-get", "dnf", "winget.exe"):
                stub = Path(tmp) / name
                stub.write_text("#!/bin/sh\nexit 100\n", encoding="utf-8")
                stub.chmod(0o755)
            env = dict(os.environ, HOME=tmp, PATH=tmp + os.pathsep + os.environ.get("PATH", ""))
            # Pretend jq is missing so the script must try (and fail) a package install.
            env["BASH_FUNC_command%%"] = (
                '() { if [[ "$1" == "-v" && "$2" == "jq" ]]; then return 1; fi; builtin command "$@"; }'
            )
            result = subprocess.run(
                ["bash", str(BOOTSTRAP_SH), "--minimal", "--no-kb"],
                cwd=ROOT, env=env, check=False, text=True,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120,
            )
        self.assertEqual(0, result.returncode, result.stdout[-2000:])
        self.assertIn("Never run 'rtk init'", result.stdout)
        self.assertIn("jq (install attempted", result.stdout)

    def test_maven_is_never_requested_from_winget(self) -> None:
        self.assertNotIn("Apache.Maven", BOOTSTRAP_SH.read_text(encoding="utf-8"))
        self.assertNotIn("Apache.Maven", BOOTSTRAP_PS1.read_text(encoding="utf-8"))


class SourceContractTests(unittest.TestCase):
    def test_rtk_privacy_block_has_five_variables_in_both_scripts(self) -> None:
        sh = BOOTSTRAP_SH.read_text(encoding="utf-8")
        ps1 = BOOTSTRAP_PS1.read_text(encoding="utf-8")
        for name in ("RTK_DB_PATH", "RTK_TELEMETRY_DISABLED", "RTK_TEE", "RTK_RECALL", "RTK_SUPPRESS_HOOK_WARNING"):
            self.assertIn(name, sh)
            self.assertIn(name, ps1)

    def test_ps1_declares_opt_in_switches_and_pinned_install(self) -> None:
        ps1 = BOOTSTRAP_PS1.read_text(encoding="utf-8")
        self.assertIn("[switch]$SecurityTools", ps1)
        self.assertIn("[switch]$Rtk", ps1)
        self.assertIn("--version $rtkReviewedVersion --exact", ps1)
        self.assertIn("winget pin add --id rtk-ai.rtk", ps1)
        self.assertIn("skillspector==2.13.7", ps1)

    def test_never_run_rtk_init_text_is_kept(self) -> None:
        for path in (BOOTSTRAP_SH, BOOTSTRAP_PS1):
            self.assertIn("Never run 'rtk init'", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
