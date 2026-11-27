from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "create-specialist-agent.js"
SUBAGENTS_DIR = REPO_ROOT / "tool-subagents"

SOURCE_MD_COUNT = len(list(SUBAGENTS_DIR.glob("*.md")))
# The Codex TOML is generated from each agent .md (README.md is not an agent).
SOURCE_TOML_COUNT = len([p for p in SUBAGENTS_DIR.glob("*.md") if p.name != "README.md"])


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

    def test_codex_render_generates_toml_only(self) -> None:
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

        rendered = self.project / ".claude" / "agents" / "test-runner.md"
        frontmatter = read_frontmatter_block(rendered)
        self.assertNotIn("readonly:", frontmatter)
        self.assertNotIn("tier:", frontmatter)
        self.assertIn("model: haiku", frontmatter)

        # Canonical source keeps its tier hint; only the render drops it.
        source_frontmatter = read_frontmatter_block(SUBAGENTS_DIR / "test-runner.md")
        self.assertIn("tier: light", source_frontmatter)
        self.assertIn("model: inherit", source_frontmatter)

    def test_cursor_render_strips_readonly_and_tier_and_maps_light_to_fast(self) -> None:
        result = run_apply("cursor", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)

        rendered = self.project / ".cursor" / "agents" / "test-runner.md"
        frontmatter = read_frontmatter_block(rendered)
        self.assertNotIn("readonly:", frontmatter)
        self.assertNotIn("tier:", frontmatter)
        self.assertIn("model: fast", frontmatter)

    def test_render_without_tier_leaves_model_untouched(self) -> None:
        result = run_apply("claude", str(self.project))
        self.assertEqual(result.returncode, 0, result.stderr)

        # release-coordinator.md has no tier hint in the canonical source; the
        # render must leave its model value alone.
        source_frontmatter = read_frontmatter_block(SUBAGENTS_DIR / "release-coordinator.md")
        self.assertNotIn("tier:", source_frontmatter)

        rendered = self.project / ".claude" / "agents" / "release-coordinator.md"
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
        rendered = self.target_dir / "test-runner.md"
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


@unittest.skipUnless(node_path(), "node is required to render subagent surfaces")
class CodexTomlGenerationTests(unittest.TestCase):
    """The Codex TOML is generated from the .md source and never committed."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def render(self, source: Path, out: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["node", str(SCRIPT), "--render-codex", "--source", str(source), str(out)],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )

    def test_no_toml_is_committed_in_tool_subagents(self) -> None:
        self.assertEqual(list(SUBAGENTS_DIR.glob("*.toml")), [])

    def test_render_codex_writes_one_toml_per_agent_with_required_fields(self) -> None:
        out = self.root / "codex"
        result = self.render(SUBAGENTS_DIR, out)
        self.assertEqual(result.returncode, 0, result.stderr)
        files = sorted(out.glob("*.toml"))
        self.assertEqual(len(files), SOURCE_TOML_COUNT)
        text = (out / "verifier.toml").read_text(encoding="utf-8")
        for field in ("name = ", "description = ", "developer_instructions = "):
            self.assertIn(field, text)
        orchestrator = (out / "agent-orchestrator.toml").read_text(encoding="utf-8")
        self.assertNotIn("external_side_effects", orchestrator)
        self.assertNotIn("readonly", orchestrator)

    def test_rendered_toml_matches_the_old_hand_written_twins(self) -> None:
        fixture = json.loads((REPO_ROOT / "tests" / "fixtures" / "codex_agent_toml_keys.json").read_text(encoding="utf-8"))
        self.assertEqual(len(fixture), SOURCE_TOML_COUNT)
        out = self.root / "codex"
        self.assertEqual(self.render(SUBAGENTS_DIR, out).returncode, 0)
        for agent, keys in fixture.items():
            parsed = tomllib.loads((out / f"{agent}.toml").read_text(encoding="utf-8"))
            self.assertEqual(sorted(parsed), keys, agent)
            self.assertEqual(parsed["name"], agent)
            source = (SUBAGENTS_DIR / f"{agent}.md").read_text(encoding="utf-8")
            self.assertIn(f"description: {parsed['description']}", source)
            body = source.split("\n---\n", 1)[1]
            self.assertEqual(parsed["developer_instructions"].strip(), body.strip(), agent)
            if "readonly" in parsed:
                self.assertIs(parsed["readonly"], True, agent)

    def test_render_escapes_control_characters_and_parses(self) -> None:
        src = self.root / "src"
        src.mkdir()
        (src / "ctl.md").write_text(
            "---\nname: ctl\ndescription: d\nmodel: inherit\n---\n\nBody \x01 and \x7f and \"\"\" and \\ end\n",
            encoding="utf-8",
        )
        out = self.root / "out"
        self.assertEqual(self.render(src, out).returncode, 0)
        parsed = tomllib.loads((out / "ctl.toml").read_text(encoding="utf-8"))
        self.assertEqual(parsed["developer_instructions"], 'Body \x01 and \x7f and """ and \\ end\n')

    def test_all_real_renders_parse_as_toml(self) -> None:
        out = self.root / "codex"
        self.assertEqual(self.render(SUBAGENTS_DIR, out).returncode, 0)
        for toml_file in out.glob("*.toml"):
            parsed = tomllib.loads(toml_file.read_text(encoding="utf-8"))
            for key in ("name", "description", "developer_instructions"):
                self.assertTrue(parsed.get(key), f"{toml_file.name}: {key}")

    def test_subagents_check_warns_on_a_stale_codex_link(self) -> None:
        repo = self.root / "repo"
        (repo / "scripts").mkdir(parents=True)
        for name in ("validate-specialist-agent.js", "subagent-render.js"):
            shutil.copy(REPO_ROOT / "scripts" / name, repo / "scripts" / name)
        shutil.copytree(SUBAGENTS_DIR, repo / "tool-subagents", ignore=shutil.ignore_patterns(".generated"))
        (repo / ".codex").mkdir()
        (repo / ".codex" / "agents").symlink_to("../tool-subagents")
        result = subprocess.run(
            ["node", str(repo / "scripts" / "validate-specialist-agent.js"), "--subagents-check"],
            cwd=repo, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("WARN", result.stderr)
        self.assertIn("Codex sees no agents until it is re-pointed", result.stderr)

    def test_render_codex_rejects_agent_missing_description(self) -> None:
        src = self.root / "src"
        src.mkdir()
        (src / "broken.md").write_text("---\nname: broken\nmodel: inherit\n---\n\nBody\n", encoding="utf-8")
        result = self.render(src, self.root / "out")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing description", result.stderr)

    def test_subagents_check_passes_without_a_generated_folder(self) -> None:
        result = subprocess.run(
            ["node", str(REPO_ROOT / "scripts" / "validate-specialist-agent.js"), "--subagents-check"],
            cwd=REPO_ROOT, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


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
