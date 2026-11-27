"""Skill roots (C6): project and user level links only under `.agents/skills` and `.claude/skills`.

Runs the real scripts against throwaway directories (a scratch project and a scratch HOME, never the real one):
- sync-tool-configs.sh creates `.agents/skills` and `.claude/skills` but not `.codex/skills`, `.cursor/skills`, `.windsurf/skills`;
- existing old links are left in place and reported as removable;
- install-global-surfaces.sh links `~/.agents/skills/<name>` once for Codex, Cursor and Windsurf, creates none of the old
  user-level roots, never deletes existing ones and reports them.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYNC = ROOT / "scripts" / "sync-tool-configs.sh"
INSTALL = ROOT / "scripts" / "install-global-surfaces.sh"
OLD_PROJECT_ROOTS = (".codex", ".cursor", ".windsurf")


def _env(home: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("AWS_")}
    env["HOME"] = str(home)
    return env


@unittest.skipUnless(shutil.which("bash"), "bash is required")
class SkillRootsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.home = self.tmp / "home"
        self.home.mkdir()

    def _project(self) -> Path:
        project = self.tmp / "project"
        (project / "rules").mkdir(parents=True)
        (project / "workflows").mkdir()
        (project / "tool-subagents").mkdir()
        (project / "skills" / "demo").mkdir(parents=True)
        (project / "rules" / "r.md").write_text("---\ndescription: r\n---\n\n# R\n", encoding="utf-8")
        (project / "workflows" / "w.md").write_text("# W\n", encoding="utf-8")
        (project / "tool-subagents" / "a.md").write_text("# A\n", encoding="utf-8")
        (project / "skills" / "demo" / "SKILL.md").write_text(
            "---\nname: demo\ndescription: Demo skill.\n---\n\n# Demo\n", encoding="utf-8"
        )
        return project

    def _sync(self, project: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(SYNC), str(project), "--skip-agents-md", "--skip-github"],
            capture_output=True, text=True, env=_env(self.home), check=False,
        )

    def test_sync_creates_only_agents_and_claude_roots(self) -> None:
        project = self._project()
        result = self._sync(project)
        self.assertEqual(result.returncode, 0, result.stderr)
        for root in (".agents", ".claude"):
            self.assertTrue((project / root / "skills" / "demo" / "SKILL.md").is_file(), root)
        for root in OLD_PROJECT_ROOTS:
            self.assertFalse((project / root / "skills").exists(), root)
            self.assertFalse((project / root / "skills").is_symlink(), root)

    def test_sync_keeps_old_links_and_reports_them(self) -> None:
        project = self._project()
        self.assertEqual(self._sync(project).returncode, 0)
        for root in OLD_PROJECT_ROOTS:
            (project / root).mkdir(exist_ok=True)
            (project / root / "skills").symlink_to("../.agents/skills")
        result = self._sync(project)
        self.assertEqual(result.returncode, 0, result.stderr)
        for root in OLD_PROJECT_ROOTS:
            self.assertTrue((project / root / "skills").is_symlink(), root)
            self.assertIn(f"{root}/skills holds links that are no longer created", result.stdout)

    def _install(self, tools: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["bash", str(INSTALL), "--tools", tools, "--apply"],
            capture_output=True, text=True, env=_env(self.home), check=False,
        )

    def test_global_install_uses_shared_agents_root(self) -> None:
        result = self._install("codex,cursor,windsurf")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        shared = self.home / ".agents" / "skills"
        names = sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
        self.assertTrue(names)
        for name in names:
            self.assertTrue((shared / name).is_symlink(), name)
        self.assertEqual(sorted(p.name for p in shared.iterdir()), names)
        for old in (".codex/skills", ".cursor/skills", ".codeium/windsurf/skills"):
            self.assertFalse((self.home / old).exists(), old)
            self.assertFalse((self.home / old).is_symlink(), old)

    def test_global_install_keeps_old_links_and_reports_them(self) -> None:
        (self.home / ".codex" / "skills").mkdir(parents=True)
        (self.home / ".codex" / "skills" / "demo").symlink_to(ROOT / "skills")
        (self.home / ".cursor").mkdir()
        (self.home / ".cursor" / "skills").symlink_to(ROOT / "skills")
        result = self._install("codex,cursor")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / ".codex" / "skills" / "demo").is_symlink())
        self.assertTrue((self.home / ".cursor" / "skills").is_symlink())
        self.assertEqual(result.stdout.count("legacy skills"), 2)
        self.assertIn("can be removed", result.stdout)


if __name__ == "__main__":
    unittest.main()
