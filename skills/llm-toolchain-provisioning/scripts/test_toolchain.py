#!/usr/bin/env python3
"""Unit tests for the toolchain export/restore scripts.

Builds synthetic assistant state in a temp directory and points discovery at it
via LLM_TOOLCHAIN_HOME, so tests never read the real workstation.

    python -m unittest discover -s skills/llm-toolchain-provisioning/scripts
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import export_toolchain  # noqa: E402
import restore_toolchain  # noqa: E402
import toolchain_lib  # noqa: E402


def _write(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle)


class ToolchainTestCase(unittest.TestCase):
    """Fixture: a synthetic home with Claude Code state."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.home = Path(self._tmp.name)
        os.environ["LLM_TOOLCHAIN_HOME"] = str(self.home)

        plugins = self.home / ".claude" / "plugins"
        _write(
            plugins / "installed_plugins.json",
            {
                "version": 1,
                "plugins": {
                    "alpha@official": [
                        {"scope": "user", "version": "1.0.0", "gitCommitSha": "abc123"}
                    ],
                    "beta@official": [
                        {"scope": "user", "version": None, "gitCommitSha": None}
                    ],
                },
            },
        )
        _write(
            plugins / "known_marketplaces.json",
            {
                "official": {
                    "source": {"source": "git", "url": "https://example.invalid/official.git"}
                },
                "org-short": {
                    "source": {"source": "url", "url": "https://example.invalid/org.json"}
                },
            },
        )
        _write(
            self.home / ".claude" / "settings.json",
            {"enabledPlugins": {"alpha@official": True, "beta@official": False,
                                "ghost@official": True}},
        )

    def tearDown(self) -> None:
        os.environ.pop("LLM_TOOLCHAIN_HOME", None)
        self._tmp.cleanup()


class TestDiscovery(ToolchainTestCase):
    def test_reports_installed_and_enabled_separately(self) -> None:
        manifest = toolchain_lib.build_manifest()
        claude = next(p for p in manifest["providers"] if p["provider"] == "claude-code")
        by_id = {e["id"]: e for e in claude["extensions"]}

        self.assertEqual(by_id["alpha@official"]["enabled"], True)
        # Installed but switched off: present in the inventory, not enabled.
        self.assertEqual(by_id["beta@official"]["enabled"], False)
        self.assertEqual(by_id["alpha@official"]["pin"], "abc123")

    def test_flags_enabled_but_not_installed(self) -> None:
        manifest = toolchain_lib.build_manifest()
        messages = [f["message"] for f in manifest["findings"]]
        self.assertTrue(any("ghost@official" in m and "not installed" in m for m in messages))

    def test_flags_unpinned_upstream_extension(self) -> None:
        manifest = toolchain_lib.build_manifest()
        messages = [f["message"] for f in manifest["findings"]]
        self.assertTrue(any("beta@official" in m and "pin" in m for m in messages))

    def test_flags_source_with_nothing_installed(self) -> None:
        manifest = toolchain_lib.build_manifest()
        messages = [f["message"] for f in manifest["findings"]]
        self.assertTrue(any("org-short" in m and "registered" in m for m in messages))

    def test_classifies_git_source_as_upstream(self) -> None:
        manifest = toolchain_lib.build_manifest()
        claude = next(p for p in manifest["providers"] if p["provider"] == "claude-code")
        self.assertEqual({e["origin"] for e in claude["extensions"]}, {"upstream"})

    def test_absent_provider_is_omitted(self) -> None:
        manifest = toolchain_lib.build_manifest()
        self.assertEqual([p["provider"] for p in manifest["providers"]], ["claude-code"])

    def test_provider_filter_limits_discovery(self) -> None:
        manifest = toolchain_lib.build_manifest(providers=["cursor"])
        self.assertEqual(manifest["providers"], [])

    def test_malformed_state_file_does_not_raise(self) -> None:
        broken = self.home / ".claude" / "plugins" / "installed_plugins.json"
        broken.write_text("{ not json", encoding="utf-8")
        manifest = toolchain_lib.build_manifest()
        claude = next(p for p in manifest["providers"] if p["provider"] == "claude-code")
        self.assertEqual(claude["extensions"], [])


class TestAliasNormalization(ToolchainTestCase):
    def test_same_url_under_two_names_is_flagged_and_merged(self) -> None:
        _write(
            self.home / ".claude" / "remote-settings.json",
            {
                "extraKnownMarketplaces": {
                    "org-long-canonical-name": {
                        "source": {"source": "url", "url": "https://example.invalid/org.json"}
                    }
                }
            },
        )
        manifest = toolchain_lib.build_manifest()
        claude = next(p for p in manifest["providers"] if p["provider"] == "claude-code")
        org = next(s for s in claude["sources"] if s["url"] == "https://example.invalid/org.json")

        self.assertCountEqual(org["aliases"], ["org-short", "org-long-canonical-name"])
        messages = [f["message"] for f in manifest["findings"]]
        self.assertTrue(any("differing names" in m for m in messages))


class TestRedaction(ToolchainTestCase):
    def test_secret_looking_keys_are_replaced(self) -> None:
        payload = {
            "apiKey": "live-value",
            "nested": {"authToken": "abc", "safe": "keep"},
            "list": [{"password": "p"}],
        }
        redacted = toolchain_lib.redact(payload)

        self.assertEqual(redacted["apiKey"], toolchain_lib.REDACTED)
        self.assertEqual(redacted["nested"]["authToken"], toolchain_lib.REDACTED)
        self.assertEqual(redacted["nested"]["safe"], "keep")
        self.assertEqual(redacted["list"][0]["password"], toolchain_lib.REDACTED)


class TestTransientExclusion(unittest.TestCase):
    def test_install_scratch_directories_are_transient(self) -> None:
        self.assertTrue(toolchain_lib.is_transient("temp_git_1787898933623_i8l9b3"))
        self.assertTrue(toolchain_lib.is_transient("temp_subdir_1787922488688_x.clone"))
        self.assertFalse(toolchain_lib.is_transient("aws-core"))
        self.assertFalse(toolchain_lib.is_transient("temporary-plugin"))


class TestExportCli(ToolchainTestCase):
    def test_writes_lf_manifest(self) -> None:
        out = self.home / "out" / "toolchain.json"
        self.assertEqual(export_toolchain.main(["--out", str(out)]), 0)

        raw = out.read_bytes()
        # LF-only so the manifest hashes identically on every platform.
        self.assertNotIn(b"\r\n", raw)
        self.assertEqual(json.loads(raw.decode("utf-8"))["manifest_version"],
                         toolchain_lib.MANIFEST_VERSION)

    def test_summary_counts_match_manifest(self) -> None:
        stats = toolchain_lib.summarize(toolchain_lib.build_manifest())
        self.assertEqual(stats["totals"]["extensions"], 2)
        self.assertEqual(stats["totals"]["enabled"], 1)


class TestRestorePlan(ToolchainTestCase):
    def _manifest_file(self, manifest: dict) -> Path:
        path = self.home / "manifest.json"
        _write(path, manifest)
        return path

    def test_missing_extension_produces_install_command(self) -> None:
        manifest = toolchain_lib.build_manifest()
        # Declare a plugin the synthetic workstation does not have.
        manifest["providers"][0]["extensions"].append(
            {
                "id": "gamma@official",
                "name": "gamma",
                "source_name": "official",
                "origin": "upstream",
                "version": "2.1.0",
                "pin": "def456",
                "scope": "user",
                "enabled": True,
                "linked_to": None,
            }
        )
        path = self._manifest_file(manifest)
        self.assertEqual(restore_toolchain.main(["--manifest", str(path)]), 0)

        with path.open(encoding="utf-8") as handle:
            loaded = json.load(handle)
        wanted = restore_toolchain._index(loaded)
        present = restore_toolchain._index(toolchain_lib.build_manifest())
        plan = restore_toolchain._plan_provider(
            "claude-code", wanted["claude-code"], present["claude-code"]
        )
        self.assertEqual([e["id"] for e in plan["missing"]], ["gamma@official"])

        commands = restore_toolchain._commands(loaded, [plan])
        self.assertTrue(any("gamma@official" in c for c in commands))
        # The source must be registered before installing from it.
        self.assertTrue(any("marketplace add" in c for c in commands))

    def test_extras_are_reported_never_removed(self) -> None:
        manifest = toolchain_lib.build_manifest()
        manifest["providers"][0]["extensions"] = [
            e for e in manifest["providers"][0]["extensions"] if e["id"] != "beta@official"
        ]
        wanted = restore_toolchain._index(manifest)
        present = restore_toolchain._index(toolchain_lib.build_manifest())
        plan = restore_toolchain._plan_provider(
            "claude-code", wanted["claude-code"], present["claude-code"]
        )

        self.assertEqual(plan["extra"], ["beta@official"])
        # No command should ever uninstall an extra.
        commands = restore_toolchain._commands(manifest, [plan])
        self.assertFalse(any("uninstall" in c or "remove" in c for c in commands))

    def test_version_mismatch_is_detected(self) -> None:
        manifest = toolchain_lib.build_manifest()
        for extension in manifest["providers"][0]["extensions"]:
            if extension["id"] == "alpha@official":
                extension["pin"] = "totally-different-sha"
        wanted = restore_toolchain._index(manifest)
        present = restore_toolchain._index(toolchain_lib.build_manifest())
        plan = restore_toolchain._plan_provider(
            "claude-code", wanted["claude-code"], present["claude-code"]
        )

        self.assertEqual([m["id"] for m in plan["mismatched"]], ["alpha@official"])

    def test_identical_manifest_plans_nothing(self) -> None:
        path = self._manifest_file(toolchain_lib.build_manifest())
        self.assertEqual(restore_toolchain.main(["--manifest", str(path)]), 0)

        with path.open(encoding="utf-8") as handle:
            loaded = json.load(handle)
        plan = restore_toolchain._plan_provider(
            "claude-code",
            restore_toolchain._index(loaded)["claude-code"],
            restore_toolchain._index(toolchain_lib.build_manifest())["claude-code"],
        )
        self.assertEqual(plan["missing"], [])
        self.assertEqual(plan["mismatched"], [])
        self.assertEqual(restore_toolchain._commands(loaded, [plan]), [])

    def test_missing_manifest_exits_nonzero(self) -> None:
        self.assertEqual(
            restore_toolchain.main(["--manifest", str(self.home / "absent.json")]), 2
        )

    def test_malformed_manifest_exits_nonzero(self) -> None:
        path = self.home / "bad.json"
        path.write_text("{ not json", encoding="utf-8")
        self.assertEqual(restore_toolchain.main(["--manifest", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
