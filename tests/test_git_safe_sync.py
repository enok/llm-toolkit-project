"""Tests for scripts/git_safe_sync.py, the guard against `git reset --hard`.

Every test builds throwaway repositories in a temp dir and runs the script as a
subprocess, so exit codes and output are the real ones. The scenario is the
recurring mistake: a shared clone holds uncommitted edits (a tracked edit,
untracked files, a staged file) and someone "syncs" it with `git reset --hard`.
`test_control_naive_reset_hard_loses_the_work` proves that scenario really
destroys work, so the other tests cannot pass vacuously.

Run: pytest -q tests/test_git_safe_sync.py   (or python -m unittest)
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "git_safe_sync.py"

BASE_LINES = [f"line {n}" for n in range(1, 11)]
LOCAL_EDIT = "line 1 LOCAL EDIT"
LOCAL_DRAFT = "local draft that upstream also adds\n"
UPSTREAM_FILE = "from upstream\n"
SPACED = "notes/my notes.txt"


def make_env(home: str) -> dict[str, str]:
    """Environment that ignores the developer's own git config and identity."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(
        HOME=home,
        USERPROFILE=home,
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_TERMINAL_PROMPT="0",
    )
    return env


class GitSafeSyncCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp(prefix="git-safe-sync-")).resolve()
        self.addCleanup(shutil.rmtree, str(self.tmp), ignore_errors=True)
        self.env = make_env(str(self.tmp))
        self.repo = self.tmp / "shared-clone"
        self.repo.mkdir()
        self.git("init", "-q")
        self.git("symbolic-ref", "HEAD", "refs/heads/main")
        self.git("config", "user.name", "Test User")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")

    # -- helpers -----------------------------------------------------------

    def git(self, *args: str, cwd: Path | None = None) -> str:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(cwd or self.repo),
            env=self.env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        if proc.returncode != 0:
            self.fail(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc.stdout.strip()

    def sync(self, *args: str, repo: Path | None = None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(repo or self.repo), *args],
            env=self.env,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )

    def write(self, rel: str, text: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode())

    def read(self, rel: str) -> str:
        return (self.repo / rel).read_bytes().decode()

    def commit_all(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "-m", message)
        return self.git("rev-parse", "HEAD")

    def build_scenario(self) -> str:
        """main = c1; branch `upstream` = c1 + one commit. Returns upstream SHA."""
        self.write("tracked.txt", "\n".join(BASE_LINES) + "\n")
        self.commit_all("c1")
        self.git("checkout", "-q", "-b", "upstream")
        lines = [*BASE_LINES[:-1], "line 10 upstream"]
        self.write("tracked.txt", "\n".join(lines) + "\n")
        self.write("added_upstream.txt", UPSTREAM_FILE)
        sha = self.commit_all("c2")
        self.git("checkout", "-q", "main")
        return sha

    def make_dirty(self, collide: bool = True) -> None:
        """A tracked edit, a staged file and untracked files (one with a space)."""
        lines = [LOCAL_EDIT, *BASE_LINES[1:]]
        self.write("tracked.txt", "\n".join(lines) + "\n")
        self.write(SPACED, "local notes\n")
        if collide:
            self.write("added_upstream.txt", LOCAL_DRAFT)
        self.write("staged.txt", "staged work\n")
        self.git("add", "staged.txt")

    def snapshot(self) -> dict[str, object]:
        files = {}
        for path in sorted(self.repo.rglob("*")):
            rel = path.relative_to(self.repo)
            if ".git" not in rel.parts and path.is_file():
                files[rel.as_posix()] = path.read_bytes()
        return {
            "files": files,
            "refs": self.git("for-each-ref", "--format=%(refname) %(objectname)"),
            "head": self.git("rev-parse", "HEAD"),
            "status": self.git("status", "--porcelain=v1", "--untracked-files=all"),
            "stash": self.git("stash", "list"),
        }

    def branches(self) -> list[str]:
        out = self.git("for-each-ref", "--format=%(refname:short)", "refs/heads")
        return sorted(out.splitlines())

    def assert_clean_at(self, sha: str) -> None:
        self.assertEqual(self.git("rev-parse", "HEAD"), sha)
        status = self.git("status", "--porcelain=v1", "--untracked-files=all")
        self.assertEqual(status, "")

    def assert_work_in_commit(self, sha: str) -> None:
        """The dirty scenario (with collision) is fully contained in commit `sha`."""
        self.assertEqual(self.git("cat-file", "-t", sha), "commit")
        self.assertIn(LOCAL_EDIT, self.git("show", f"{sha}:tracked.txt"))
        self.assertEqual(self.git("show", f"{sha}:{SPACED}"), "local notes")
        self.assertEqual(
            self.git("show", f"{sha}:added_upstream.txt"), LOCAL_DRAFT.strip()
        )
        self.assertEqual(self.git("show", f"{sha}:staged.txt"), "staged work")


class RefusalTests(GitSafeSyncCase):
    def test_dirty_tree_is_refused_and_left_untouched(self) -> None:
        self.build_scenario()
        self.make_dirty()
        before = self.snapshot()

        result = self.sync("--to", "upstream")

        self.assertEqual(result.returncode, 3, result.stderr)
        for path in ("tracked.txt", SPACED, "added_upstream.txt", "staged.txt"):
            self.assertIn(path, result.stderr)
        self.assertIn("REFUSED", result.stderr)
        self.assertEqual(self.snapshot(), before)
        self.assertIn(LOCAL_EDIT, self.read("tracked.txt"))
        self.assertEqual(self.read("added_upstream.txt"), LOCAL_DRAFT)

    def test_control_naive_reset_hard_loses_the_work(self) -> None:
        """The original mistake: the same scenario under `git reset --hard`."""
        self.build_scenario()
        self.make_dirty()

        self.git("reset", "--hard", "upstream")

        self.assertNotIn(LOCAL_EDIT, self.read("tracked.txt"))
        self.assertEqual(self.read("added_upstream.txt"), UPSTREAM_FILE)
        self.assertEqual(self.git("stash", "list"), "")

    def test_staged_only_change_is_dirty(self) -> None:
        self.build_scenario()
        self.write("staged.txt", "staged work\n")
        self.git("add", "staged.txt")

        result = self.sync("--to", "upstream")

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("staged.txt", result.stderr)
        self.assertEqual(self.read("staged.txt"), "staged work\n")

    def test_renamed_path_is_listed_with_both_names(self) -> None:
        self.build_scenario()
        self.git("mv", "tracked.txt", "renamed.txt")

        result = self.sync("--to", "upstream")

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("tracked.txt -> renamed.txt", result.stderr)
        self.assertTrue((self.repo / "renamed.txt").exists())

    def test_ignored_file_the_ref_would_overwrite_is_refused(self) -> None:
        self.write(".gitignore", "*.log\n")
        self.write("tracked.txt", "base\n")
        self.commit_all("c1")
        self.git("checkout", "-q", "-b", "upstream")
        self.write("build.log", "committed log\n")
        self.git("add", "-f", "build.log")
        self.git("commit", "-q", "-m", "c2")
        self.git("checkout", "-q", "main")
        self.write("build.log", "my only copy\n")
        self.assertEqual(self.git("status", "--porcelain"), "")  # looks clean

        result = self.sync("--to", "upstream")

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("build.log", result.stderr)
        self.assertEqual(self.read("build.log"), "my only copy\n")
        self.git("reset", "--hard", "upstream")  # control: plain reset eats it
        self.assertEqual(self.read("build.log"), "committed log\n")

    def test_operation_in_progress_is_refused(self) -> None:
        upstream = self.build_scenario()
        head = self.git("rev-parse", "HEAD")
        git_dir = self.git("rev-parse", "--absolute-git-dir")
        Path(git_dir, "CHERRY_PICK_HEAD").write_text(upstream + "\n")

        result = self.sync("--to", "upstream")

        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("CHERRY_PICK_HEAD", result.stderr)
        self.assertEqual(self.git("rev-parse", "HEAD"), head)


class PreserveTests(GitSafeSyncCase):
    def test_wip_commit_keeps_every_kind_of_work_reachable(self) -> None:
        upstream = self.build_scenario()
        self.make_dirty()

        result = self.sync("--to", "upstream", "--wip-commit")

        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r"WIP commit ([0-9a-f]{40}) on (\S+)", result.stdout)
        self.assertIsNotNone(match, result.stdout)
        sha, branch = match.group(1), match.group(2)
        self.assert_work_in_commit(sha)
        holders = self.git("for-each-ref", "--contains", sha, "--format=%(refname)")
        self.assertIn(f"refs/heads/{branch}", holders.splitlines())
        self.assertIn("cherry-pick -n " + sha, result.stdout)
        self.assert_clean_at(upstream)
        self.assertEqual(self.read("added_upstream.txt"), UPSTREAM_FILE)

    def test_wip_commit_can_be_restored_with_the_printed_command(self) -> None:
        upstream = self.build_scenario()
        self.make_dirty(collide=False)

        result = self.sync("--to", "upstream", "--wip-commit")
        self.assertEqual(result.returncode, 0, result.stderr)
        sha = re.search(r"WIP commit ([0-9a-f]{40})", result.stdout).group(1)
        self.assert_clean_at(upstream)

        self.git("cherry-pick", "-n", sha)

        self.assertIn(LOCAL_EDIT, self.read("tracked.txt"))
        self.assertIn("line 10 upstream", self.read("tracked.txt"))
        self.assertEqual(self.read(SPACED), "local notes\n")
        self.assertEqual(self.read("staged.txt"), "staged work\n")

    def test_stash_keeps_every_kind_of_work(self) -> None:
        upstream = self.build_scenario()
        self.make_dirty()

        result = self.sync("--to", "upstream", "--stash")

        self.assertEqual(result.returncode, 0, result.stderr)
        match = re.search(r"stash ([0-9a-f]{40})", result.stdout)
        self.assertIsNotNone(match, result.stdout)
        sha = match.group(1)
        self.assertEqual(self.git("rev-parse", "refs/stash"), sha)
        self.assertEqual(len(self.git("stash", "list").splitlines()), 1)
        self.assertIn(LOCAL_EDIT, self.git("show", f"{sha}:tracked.txt"))
        self.assertEqual(self.git("show", f"{sha}:staged.txt"), "staged work")
        untracked = f"{sha}^3"
        self.assertEqual(self.git("show", f"{untracked}:{SPACED}"), "local notes")
        self.assertEqual(
            self.git("show", f"{untracked}:added_upstream.txt"), LOCAL_DRAFT.strip()
        )
        self.assertIn("stash apply " + sha, result.stdout)
        self.assert_clean_at(upstream)

    def test_stash_can_be_restored_with_the_printed_command(self) -> None:
        upstream = self.build_scenario()
        self.make_dirty(collide=False)

        result = self.sync("--to", "upstream", "--stash")
        self.assertEqual(result.returncode, 0, result.stderr)
        sha = re.search(r"stash ([0-9a-f]{40})", result.stdout).group(1)
        self.assert_clean_at(upstream)

        self.git("stash", "apply", sha)

        self.assertIn(LOCAL_EDIT, self.read("tracked.txt"))
        self.assertIn("line 10 upstream", self.read("tracked.txt"))
        self.assertEqual(self.read(SPACED), "local notes\n")

    def test_wip_commit_works_without_a_configured_identity(self) -> None:
        self.build_scenario()
        self.git("config", "--unset", "user.name")
        self.git("config", "--unset", "user.email")
        self.git("config", "user.useConfigOnly", "true")
        self.make_dirty()

        result = self.sync("--to", "upstream", "--wip-commit")

        self.assertEqual(result.returncode, 0, result.stderr)
        sha = re.search(r"WIP commit ([0-9a-f]{40})", result.stdout).group(1)
        self.assertEqual(self.git("log", "-1", "--format=%an", sha), "git-safe-sync")

    def test_failed_ref_lookup_happens_before_anything_is_preserved(self) -> None:
        self.build_scenario()
        self.make_dirty()
        before = self.snapshot()

        for flag in ("--wip-commit", "--stash"):
            with self.subTest(flag=flag):
                result = self.sync("--to", "no-such-ref", flag)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(self.snapshot(), before)


class SyncTests(GitSafeSyncCase):
    def test_clean_tree_syncs_to_the_ref(self) -> None:
        upstream = self.build_scenario()

        result = self.sync("--to", "upstream")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_clean_at(upstream)
        self.assertEqual(self.read("added_upstream.txt"), UPSTREAM_FILE)
        self.assertIn("line 10 upstream", self.read("tracked.txt"))
        self.assertEqual(self.branches(), ["main", "upstream"])

    def test_preserve_flags_on_a_clean_tree_create_nothing(self) -> None:
        upstream = self.build_scenario()
        c1 = self.git("rev-parse", "main")

        for flag in ("--wip-commit", "--stash"):
            with self.subTest(flag=flag):
                self.git("reset", "-q", "--hard", c1)
                result = self.sync("--to", "upstream", flag)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_clean_at(upstream)
                self.assertEqual(self.branches(), ["main", "upstream"])
                self.assertEqual(self.git("stash", "list"), "")

    def test_local_commits_missing_from_the_ref_are_kept_on_a_branch(self) -> None:
        upstream = self.build_scenario()
        self.write("local.txt", "unpushed\n")
        local = self.commit_all("local only")

        result = self.sync("--to", "upstream")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_clean_at(upstream)
        kept = [b for b in self.branches() if b.startswith("safe-sync/previous-")]
        self.assertEqual(len(kept), 1, self.branches())
        self.assertEqual(self.git("rev-parse", kept[0]), local)
        self.assertEqual(self.git("show", f"{local}:local.txt"), "unpushed")

    def test_remote_tracking_ref_is_fetched_first(self) -> None:
        self.write("tracked.txt", "v1\n")
        self.commit_all("c1")
        origin = self.tmp / "origin.git"
        self.git("init", "-q", "--bare", str(origin), cwd=self.tmp)
        self.git("remote", "add", "origin", str(origin))
        self.git("push", "-q", "origin", "main")
        self.git("fetch", "-q", "origin")
        other = self.tmp / "other"
        self.git("clone", "-q", "-b", "main", str(origin), str(other), cwd=self.tmp)
        self.git("config", "user.name", "Other", cwd=other)
        self.git("config", "user.email", "other@example.invalid", cwd=other)
        (other / "tracked.txt").write_text("v2\n")
        self.git("commit", "-q", "-am", "c2", cwd=other)
        self.git("push", "-q", "origin", "HEAD:main", cwd=other)
        new = self.git("rev-parse", "HEAD", cwd=other)
        tracking = self.git("rev-parse", "refs/remotes/origin/main")
        self.assertNotEqual(tracking, new)  # not fetched yet

        dry = self.sync("--to", "origin/main", "--dry-run")
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(self.git("rev-parse", "refs/remotes/origin/main"), tracking)

        result = self.sync("--to", "origin/main")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("fetching origin", result.stdout)
        self.assert_clean_at(new)
        self.assertEqual(self.read("tracked.txt"), "v2\n")


class DryRunTests(GitSafeSyncCase):
    def test_dry_run_changes_nothing(self) -> None:
        upstream = self.build_scenario()
        cases = [
            ("clean", [], 0),
            ("clean wip", ["--wip-commit"], 0),
            ("dirty", [], 3),
            ("dirty wip", ["--wip-commit"], 0),
            ("dirty stash", ["--stash"], 0),
        ]
        for name, flags, code in cases:
            with self.subTest(case=name):
                self.git("reset", "-q", "--hard", "main")
                self.git("clean", "-q", "-fd")
                if name.startswith("dirty"):
                    self.make_dirty()
                before = self.snapshot()

                result = self.sync("--to", "upstream", "--dry-run", *flags)

                self.assertEqual(result.returncode, code, result.stderr)
                self.assertEqual(self.snapshot(), before)
                self.assertNotEqual(before["head"], upstream)
                if code == 0:
                    self.assertIn("nothing was changed", result.stdout)


class UsageTests(GitSafeSyncCase):
    def test_wip_commit_and_stash_are_mutually_exclusive(self) -> None:
        self.build_scenario()
        result = self.sync("--to", "upstream", "--wip-commit", "--stash")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with", result.stderr)

    def test_missing_arguments_exit_2(self) -> None:
        self.build_scenario()
        for args in ([], ["--to", "upstream", "--bogus"]):
            with self.subTest(args=args):
                result = self.sync(*args)
                self.assertEqual(result.returncode, 2)
        missing_to = subprocess.run(
            [sys.executable, str(SCRIPT), "--repo", str(self.repo)],
            env=self.env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(missing_to.returncode, 2)
        self.assertIn("--to", missing_to.stderr)

    def test_path_that_is_not_a_work_tree_exits_2(self) -> None:
        plain = self.tmp / "plain"
        plain.mkdir()
        self.env["GIT_CEILING_DIRECTORIES"] = str(self.tmp)
        result = self.sync("--to", "main", repo=plain)
        self.assertEqual(result.returncode, 2)
        self.assertIn("not inside a git work tree", result.stderr)

    def test_unknown_ref_exits_2_and_changes_nothing(self) -> None:
        self.build_scenario()
        before = self.snapshot()
        result = self.sync("--to", "no-such-ref")
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot resolve", result.stderr)
        self.assertEqual(self.snapshot(), before)

    def test_help_documents_flags_and_exit_codes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        for text in ("--repo", "--to", "--wip-commit", "--stash", "--dry-run"):
            self.assertIn(text, result.stdout)
        self.assertIn(
            "exit codes: 0 ok, 2 usage or git error, 3 refused", result.stdout
        )


if __name__ == "__main__":
    unittest.main()
