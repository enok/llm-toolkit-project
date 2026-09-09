from pathlib import Path
import os
import re
import shutil
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def function_body(script: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}\(\) \{{\n(.*?)^\}}", script, re.MULTILINE | re.DOTALL)
    if not match:
        raise AssertionError(f"missing shell function: {name}")
    return match.group(1)


def shell_function(script: str, name: str) -> str:
    return f"{name}() {{\n{function_body(script, name)}}}\n"


def bash_path() -> str | None:
    git_bash = Path(r"C:\Program Files\Git\bin\bash.exe")
    if git_bash.exists():
        return str(git_bash)
    return shutil.which("bash")


class ValidatorJunctionSafetyTest(unittest.TestCase):
    def test_markdown_scan_uses_git_inventory(self) -> None:
        script = (REPO_ROOT / "scripts" / "validate-toolkit-indexes.sh").read_text(encoding="utf-8")
        body = function_body(script, "iter_scoped_markdown_files")
        self.assertIn("git ls-files", body)
        self.assertNotIn("find ", body)

    def test_security_file_scans_avoid_recursive_overlay_walks(self) -> None:
        script = (REPO_ROOT / "scripts" / "security-check-toolkit.sh").read_text(encoding="utf-8")
        for name in ("has_files", "find_scoped_files_by_extension", "run_cloud_sync_duplicate_check"):
            with self.subTest(function=name):
                body = function_body(script, name)
                self.assertIn("git", body)
                self.assertNotIn("find ", body)

    def test_duplicate_name_check_uses_shell_builtins(self) -> None:
        script = (REPO_ROOT / "scripts" / "security-check-toolkit.sh").read_text(encoding="utf-8")
        name_check = function_body(script, "is_cloud_sync_duplicate_name")
        duplicate_scan = function_body(script, "run_cloud_sync_duplicate_check")
        self.assertIn("[[", name_check)
        self.assertNotIn("grep", name_check)
        self.assertNotIn("basename", duplicate_scan)

    @unittest.skipUnless(bash_path(), "Bash is required for shell behavior tests")
    def test_git_inventory_handles_spaces_untracked_files_and_cycles(self) -> None:
        index_script = (REPO_ROOT / "scripts" / "validate-toolkit-indexes.sh").read_text(encoding="utf-8")
        security_script = (REPO_ROOT / "scripts" / "security-check-toolkit.sh").read_text(encoding="utf-8")
        functions = "".join(
            (
                shell_function(index_script, "iter_scoped_markdown_files"),
                shell_function(security_script, "git_inventory"),
                shell_function(security_script, "has_files"),
                shell_function(security_script, "find_scoped_files_by_extension"),
                shell_function(security_script, "is_cloud_sync_duplicate_name"),
                shell_function(security_script, "run_cloud_sync_duplicate_check"),
            )
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            docs = root / "docs"
            docs.mkdir()
            (docs / "tracked file.md").write_text("tracked\n", encoding="utf-8")
            (docs / "untracked file.md").write_text("untracked\n", encoding="utf-8")
            (docs / "script with spaces.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            (root / "-leading.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
            subprocess.run(["git", "add", "docs/tracked file.md"], cwd=root, check=True)
            overlay = root / ".agents" / "skills"
            overlay.mkdir(parents=True)
            cycle = overlay / "cycle"
            cycle_created = False
            try:
                cycle.symlink_to(root, target_is_directory=True)
                cycle_created = True
            except OSError:
                if os.name == "nt":
                    junction = subprocess.run(
                        ["cmd", "/c", "mklink", "/J", str(cycle), str(root)],
                        capture_output=True,
                    )
                    cycle_created = junction.returncode == 0
            self.assertTrue(cycle_created, "symlink or junction cycle is required for coverage")

            inventory = subprocess.run(
                [bash_path(), "-c", functions + "iter_scoped_markdown_files | tr '\\0' '\\n'"],
                cwd=root,
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertIn("docs/tracked file.md", inventory.stdout)
            self.assertIn("docs/untracked file.md", inventory.stdout)

            newline_inventory = subprocess.run(
                [
                    bash_path(),
                    "-c",
                    shell_function(index_script, "iter_scoped_markdown_files")
                    + "git() { [[ \"$*\" == *--cached* ]] && printf 'docs/line\\nbreak.md\\0'; }; "
                    + "iter_scoped_markdown_files",
                ],
                check=True,
                capture_output=True,
                timeout=10,
            )
            self.assertEqual(b"./docs/line\nbreak.md\0", newline_inventory.stdout)

            shell_inventory = subprocess.run(
                [bash_path(), "-c", functions + 'REPO_ROOT="$PWD"; find_scoped_files_by_extension sh'],
                cwd=root,
                check=True,
                capture_output=True,
                timeout=10,
            )
            self.assertIn(b"./-leading.sh\0", shell_inventory.stdout)
            self.assertIn(b"./docs/script with spaces.sh\0", shell_inventory.stdout)

            has_shell = subprocess.run(
                [bash_path(), "-c", functions + 'REPO_ROOT="$PWD"; has_files "*.sh"'],
                cwd=root,
                timeout=10,
            )
            self.assertEqual(0, has_shell.returncode)

            (root / ".gitignore").write_text("* (*).md\n* (*).sh\n* (*).ps1\n.cache/\n", encoding="utf-8")
            ignored_duplicate = docs / "copy (1).md"
            ignored_duplicate.write_text("duplicate\n", encoding="utf-8")
            ignored_cache = root / ".cache"
            ignored_cache.mkdir()
            (ignored_cache / "data (2).json").write_text("{}\n", encoding="utf-8")
            ignored = subprocess.run(
                ["git", "check-ignore", "-q", str(ignored_duplicate.relative_to(root))],
                cwd=root,
            )
            self.assertEqual(0, ignored.returncode)
            duplicate = subprocess.run(
                [bash_path(), "-c", functions + 'REPO_ROOT="$PWD"; run_cloud_sync_duplicate_check'],
                cwd=root,
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(1, duplicate.returncode)
            self.assertIn(r"docs/copy\ \(1\).md", duplicate.stderr)
            self.assertIn(r".cache/data\ \(2\).json", duplicate.stderr)


if __name__ == "__main__":
    unittest.main()
