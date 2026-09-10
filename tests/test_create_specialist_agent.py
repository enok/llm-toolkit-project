from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "create-specialist-agent.js"
SUBAGENTS_DIR = REPO_ROOT / "tool-subagents"

SOURCE_MD_COUNT = len(list(SUBAGENTS_DIR.glob("*.md")))
SOURCE_TOML_COUNT = len(list(SUBAGENTS_DIR.glob("*.toml")))


def node_path() -> str | None:
    return shutil.which("node")


def run_apply(provider: str, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["node", str(SCRIPT), "--apply-subagents", provider, *extra],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def read_frontmatter_block(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"{path} has no frontmatter"
    end = text.index("\n---\n", 4)
    return text[4:end]


def has_frontmatter(path: Path) -> bool:
    return path.read_text(encoding="utf-8").startswith("---\n")


@unittest.skipUnless(node_path(), "node is required to render subagent surfaces")
class CreateSpecialistAgentRenderTests(unittest.TestCase):
    """Exercises `--apply-subagents` provider filtering and frontmatter rewrites."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = Path(self._tmp.name)

    def test_codex_render_copies_toml_only(self) -> None:
        result = run_apply("codex", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)

        codex_dir = self.project / ".codex" / "agents"
        md_files = list(codex_dir.glob("*.md"))
        toml_files = list(codex_dir.glob("*.toml"))
        self.assertEqual(md_files, [], f"codex render must not include .md files: {md_files}")
        self.assertEqual(len(toml_files), SOURCE_TOML_COUNT)

    def test_cursor_and_claude_render_md_only(self) -> None:
        for provider in ("cursor", "claude"):
            with self.subTest(provider=provider):
                result = run_apply(provider, str(self.project))
                self.assertEqual(result.returncode, 0, result.stderr)

                provider_dir = self.project / f".{provider}" / "agents"
                toml_files = list(provider_dir.glob("*.toml"))
                md_files = list(provider_dir.glob("*.md"))
                self.assertEqual(toml_files, [], f"{provider} render must not include .toml files: {toml_files}")
                # README.md plus every canonical specialist prompt.
                self.assertEqual(len(md_files), SOURCE_MD_COUNT)

    def test_claude_render_never_contains_cursor_model_vocabulary(self) -> None:
        result = run_apply("claude", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)

        claude_dir = self.project / ".claude" / "agents"
        for md_file in claude_dir.glob("*.md"):
            if not has_frontmatter(md_file):
                continue  # e.g. README.md, which documents the mapping in prose
            frontmatter = read_frontmatter_block(md_file)
            for line in frontmatter.splitlines():
                key, _, value = line.partition(":")
                if key.strip() == "model":
                    self.assertNotEqual(
                        value.strip(), "fast", f"{md_file} still carries Cursor's 'fast' model vocabulary"
                    )

    def test_claude_render_strips_readonly_and_tier_and_maps_light_to_haiku(self) -> None:
        result = run_apply("claude", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)

        rendered = self.project / ".claude" / "agents" / "ci-triage.md"
        frontmatter = read_frontmatter_block(rendered)
        self.assertNotIn("readonly:", frontmatter)
        self.assertNotIn("tier:", frontmatter)
        self.assertIn("model: haiku", frontmatter)

        # Canonical source keeps its tier hint; only the render drops it.
        source_frontmatter = read_frontmatter_block(SUBAGENTS_DIR / "ci-triage.md")
        self.assertIn("tier: light", source_frontmatter)
        self.assertIn("model: inherit", source_frontmatter)

    def test_cursor_render_strips_readonly_and_tier_and_maps_light_to_fast(self) -> None:
        result = run_apply("cursor", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)

        rendered = self.project / ".cursor" / "agents" / "ci-triage.md"
        frontmatter = read_frontmatter_block(rendered)
        self.assertNotIn("readonly:", frontmatter)
        self.assertNotIn("tier:", frontmatter)
        self.assertIn("model: fast", frontmatter)

    def test_render_without_tier_leaves_model_untouched(self) -> None:
        result = run_apply("claude", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)

        # code-reviewer.md has no tier hint in the canonical source; the
        # render must leave its model value alone.
        source_frontmatter = read_frontmatter_block(SUBAGENTS_DIR / "code-reviewer.md")
        self.assertNotIn("tier:", source_frontmatter)

        rendered = self.project / ".claude" / "agents" / "code-reviewer.md"
        rendered_frontmatter = read_frontmatter_block(rendered)
        self.assertIn("model: inherit", rendered_frontmatter)

    def test_only_changed_files_are_rewritten(self) -> None:
        first = run_apply("claude", str(self.project))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("file update(s)", first.stdout)

        second = run_apply("claude", str(self.project))
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("(0 file update(s))", second.stdout)
        self.assertNotIn("APPLY", second.stdout)

    def test_all_provider_applies_each_rule_to_its_own_directory(self) -> None:
        result = run_apply("all", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)

        self.assertEqual(len(list((self.project / ".codex" / "agents").glob("*.toml"))), SOURCE_TOML_COUNT)
        self.assertEqual(list((self.project / ".codex" / "agents").glob("*.md")), [])
        self.assertEqual(len(list((self.project / ".cursor" / "agents").glob("*.md"))), SOURCE_MD_COUNT)
        self.assertEqual(len(list((self.project / ".claude" / "agents").glob("*.md"))), SOURCE_MD_COUNT)


@unittest.skipUnless(node_path(), "node is required to render subagent surfaces")
class CreateSpecialistAgentTargetOptionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.target_dir = Path(self._tmp.name) / "custom-agents-dir"

    def test_target_renders_single_provider_into_explicit_directory(self) -> None:
        result = run_apply("claude", "--target", str(self.target_dir))
        self.assertEqual(result.returncode, 0, result.stderr)

        md_files = list(self.target_dir.glob("*.md"))
        self.assertEqual(len(md_files), SOURCE_MD_COUNT)
        rendered = self.target_dir / "ci-triage.md"
        self.assertTrue(rendered.exists())
        self.assertIn("model: haiku", read_frontmatter_block(rendered))

    def test_target_rejects_relative_path(self) -> None:
        result = run_apply("claude", "--target", "relative/dir")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--target must be an absolute path", result.stderr)

    def test_target_rejects_all_provider(self) -> None:
        result = run_apply("all", "--target", str(self.target_dir))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--target requires a single provider", result.stderr)


class CreateSpecialistAgentSyntaxTests(unittest.TestCase):
    @unittest.skipUnless(node_path(), "node is required to syntax-check the script")
    def test_script_is_syntactically_valid(self) -> None:
        result = subprocess.run(
            ["node", "--check", str(SCRIPT)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
