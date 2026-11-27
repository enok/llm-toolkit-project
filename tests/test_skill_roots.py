"""Skill roots (C6): project and user level links only under `.agents/skills` and `.claude/skills`.

Runs the real scripts against throwaway directories (a scratch project and a scratch HOME, never the real one):
- sync-tool-configs.sh creates `.agents/skills` and `.claude/skills` but not `.codex/skills`, `.cursor/skills`, `.windsurf/skills`;
- existing old links are left in place and reported as removable;
- install-global-surfaces.sh links `~/.agents/skills/<name>` once for Codex, Cursor and Windsurf, creates none of the old
  user-level roots, never deletes existing ones and reports them;
- install-global-surfaces.sh gives `~/.claude/skills` one link per skill inside a real directory (like `~/.agents/skills`),
  so a file another tool writes there lands in HOME and not in the toolkit checkout.
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

    def _toolkit_skills_state(self) -> str:
        status = subprocess.run(
            ["git", "-C", str(ROOT), "status", "--porcelain", "--", "skills"],
            capture_output=True, text=True, check=False,
        ).stdout
        listing = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "skills").rglob("*") if p.is_file())
        return status + "\n".join(listing)

    def _skill_names(self) -> list:
        return sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())

    def test_claude_fresh_install_has_real_dir_with_per_skill_links(self) -> None:
        result = self._install("claude")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        claude_skills = self.home / ".claude" / "skills"
        self.assertTrue(claude_skills.is_dir())
        self.assertFalse(claude_skills.is_symlink())
        names = self._skill_names()
        self.assertEqual(sorted(p.name for p in claude_skills.iterdir()), names)
        for name in names:
            self.assertTrue((claude_skills / name).is_symlink(), name)
            self.assertEqual((claude_skills / name).resolve(), (ROOT / "skills" / name).resolve())
        self.assertTrue((self.home / ".claude" / "agents").is_symlink())

    def test_claude_migrates_directory_link_without_touching_toolkit(self) -> None:
        before = self._toolkit_skills_state()
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(ROOT / "skills")
        result = self._install("claude")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        claude_skills = self.home / ".claude" / "skills"
        self.assertFalse(claude_skills.is_symlink())
        self.assertTrue(claude_skills.is_dir())
        self.assertEqual(sorted(p.name for p in claude_skills.iterdir()), self._skill_names())
        self.assertEqual(self._toolkit_skills_state(), before)
        again = self._install("claude")
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertEqual(self._toolkit_skills_state(), before)

    def test_claude_dry_run_changes_nothing_on_a_directory_link(self) -> None:
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(ROOT / "skills")
        result = subprocess.run(
            ["bash", str(INSTALL), "--tools", "claude"],
            capture_output=True, text=True, env=_env(self.home), check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.home / ".claude" / "skills").is_symlink())
        self.assertNotIn("blocked", result.stdout)

    def test_claude_existing_real_dir_keeps_contents_and_gains_links(self) -> None:
        mine = self.home / ".claude" / "skills" / "my-own-skill"
        mine.mkdir(parents=True)
        (mine / "SKILL.md").write_text("---\nname: my-own-skill\ndescription: Mine.\n---\n", encoding="utf-8")
        foreign = self.home / ".claude" / "skills" / "other-tool-link"
        foreign.symlink_to(self.tmp)
        result = self._install("claude")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        claude_skills = self.home / ".claude" / "skills"
        self.assertTrue((mine / "SKILL.md").is_file())
        self.assertFalse(mine.is_symlink())
        self.assertTrue(foreign.is_symlink())
        for name in self._skill_names():
            self.assertTrue((claude_skills / name).is_symlink(), name)

    def test_force_backup_of_a_same_name_folder_goes_outside_the_skills_root(self) -> None:
        name = self._skill_names()[0]
        claude_skills = self.home / ".claude" / "skills"
        (claude_skills / name).mkdir(parents=True)
        (claude_skills / name / "mine.txt").write_text("mine", encoding="utf-8")
        blocked = self._install("claude")
        self.assertNotEqual(blocked.returncode, 0)
        self.assertTrue((claude_skills / name / "mine.txt").is_file())
        forced = subprocess.run(
            ["bash", str(INSTALL), "--tools", "claude", "--apply", "--force"],
            capture_output=True, text=True, env=_env(self.home), check=False,
        )
        self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
        self.assertTrue((claude_skills / name).is_symlink())
        self.assertEqual(sorted(p.name for p in claude_skills.iterdir()), self._skill_names())
        backups = list((self.home / ".claude" / "skills.backup").glob(f"{name}-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual((backups[0] / "mine.txt").read_text(encoding="utf-8"), "mine")
        self.assertIn("skills.backup", forced.stdout)

    def test_force_on_a_foreign_directory_link_prints_the_real_previous_target(self) -> None:
        other = self.tmp / "other-skills"
        other.mkdir()
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(other)
        forced = subprocess.run(
            ["bash", str(INSTALL), "--tools", "claude", "--apply", "--force"],
            capture_output=True, text=True, env=_env(self.home), check=False,
        )
        self.assertEqual(forced.returncode, 0, forced.stdout + forced.stderr)
        self.assertIn(f"was a link to {other}", forced.stdout)
        self.assertNotIn("whole catalog", forced.stdout)
        self.assertEqual(list(other.iterdir()), [])

    def test_claude_removes_only_stale_links_into_the_toolkit(self) -> None:
        claude_skills = self.home / ".claude" / "skills"
        claude_skills.mkdir(parents=True)
        stale = claude_skills / "gone-skill"
        stale.symlink_to(ROOT / "skills" / "gone-skill")
        elsewhere = claude_skills / "dangling-elsewhere"
        elsewhere.symlink_to(self.tmp / "nowhere")
        result = self._install("claude")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse(stale.is_symlink())
        self.assertTrue(elsewhere.is_symlink())

    def test_foreign_file_written_through_claude_skills_lands_in_home(self) -> None:
        before = self._toolkit_skills_state()
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(ROOT / "skills")
        self.assertEqual(self._install("claude").returncode, 0)
        newdir = self.home / ".claude" / "skills" / "zz-foreign-new-skill"
        newdir.mkdir()
        (newdir / "SKILL.md").write_text("---\nname: zz-foreign-new-skill\n---\n", encoding="utf-8")
        self.assertTrue((self.home / ".claude" / "skills" / "zz-foreign-new-skill" / "SKILL.md").is_file())
        self.assertFalse((ROOT / "skills" / "zz-foreign-new-skill").exists())
        self.assertEqual(self._toolkit_skills_state(), before)


if __name__ == "__main__":
    unittest.main()
