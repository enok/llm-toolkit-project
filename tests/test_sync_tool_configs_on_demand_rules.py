"""On-demand rules (`trigger: model_decision`) in scripts/sync-tool-configs.sh.

Runs the real script against a throwaway consumer repo and checks:
- the Cursor converter (cursor_convert_rule, extracted from the script and run in bash) writes `alwaysApply: false` for model_decision (and glob),
  `alwaysApply: true` for always_on, unknown triggers and rules without frontmatter;
- the concatenated export pastes always-on rules in full and lists on-demand rules
  (path as the consumer sees it plus description) under "Rules loaded on demand";
- a consumer that selects no on-demand rule gets no such section.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "sync-tool-configs.sh"

RULES = {
    "always-rule.md": "---\ntrigger: always_on\ndescription: Always rule\n---\n\n# Always Rule\n\nALWAYS_BODY_MARKER\n",
    "glob-rule.md": "---\ntrigger: glob\nglobs: \"*.py\"\ndescription: Glob rule\n---\n\n# Glob Rule\n\nGLOB_BODY_MARKER\n",
    "demand-rule.md": "---\ntrigger: model_decision\ndescription: Load when the demand topic comes up\n---\n\n# Demand Rule\n\nDEMAND_BODY_MARKER\n",
    "odd-rule.md": "---\ntrigger: something_else\ndescription: Unknown trigger rule\n---\n\n# Odd Rule\n\nODD_BODY_MARKER\n",
    "plain-rule.md": "# Plain Rule\n\nPLAIN_BODY_MARKER\n",
}


CONVERTER_FUNCTIONS = (
    "strip_frontmatter",
    "file_has_frontmatter",
    "first_heading_or_basename",
    "escape_frontmatter_value",
    "cursor_convert_rule",
)


def shell_function(script: str, name: str) -> str:
    match = re.search(rf"^{re.escape(name)}\(\) \{{\n.*?^\}}\n", script, re.MULTILINE | re.DOTALL)
    if not match:
        raise AssertionError(f"missing shell function: {name}")
    return match.group(0)


def alwaysapply(text: str) -> list[str]:
    return [l for l in text.splitlines() if l.startswith("alwaysApply:")]


@unittest.skipUnless(shutil.which("bash"), "bash is not available on PATH")
class OnDemandRulesSyncTest(unittest.TestCase):
    def sync(self, rules: dict[str, str]) -> Path:
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        (tmp / "rules").mkdir()
        (tmp / "workflows").mkdir()
        (tmp / "workflows" / "example-workflow.md").write_text("# Example Workflow\n", encoding="utf-8")
        for name, text in rules.items():
            (tmp / "rules" / name).write_text(text, encoding="utf-8")
        result = subprocess.run(
            ["bash", str(SCRIPT), str(tmp), "--skip-agents-md"],
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return tmp

    def convert(self, name: str) -> str:
        """Run cursor_convert_rule (extracted from the script) on one fixture rule."""
        script = SCRIPT.read_text(encoding="utf-8")
        functions = "\n".join(shell_function(script, n) for n in CONVERTER_FUNCTIONS)
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, True)
        src = tmp / name
        src.write_text(RULES[name], encoding="utf-8")
        dest = tmp / "out.mdc"
        result = subprocess.run(
            ["bash", "-c", functions + '\ncursor_convert_rule "$1" "$2"', "bash", str(src), str(dest)],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return dest.read_text(encoding="utf-8")

    def test_cursor_always_on_is_always_apply_true(self):
        self.assertEqual(alwaysapply(self.convert("always-rule.md")), ["alwaysApply: true"])

    def test_cursor_glob_is_always_apply_false(self):
        out = self.convert("glob-rule.md")
        self.assertEqual(alwaysapply(out), ["alwaysApply: false"])
        self.assertIn('globs: "*.py"', out)

    def test_cursor_model_decision_is_always_apply_false_and_keeps_description(self):
        out = self.convert("demand-rule.md")
        self.assertEqual(alwaysapply(out), ["alwaysApply: false"])
        self.assertIn("description: Load when the demand topic comes up", out)
        self.assertNotIn("trigger:", out)
        self.assertIn("DEMAND_BODY_MARKER", out)

    def test_cursor_unknown_trigger_keeps_always_apply_true(self):
        self.assertEqual(alwaysapply(self.convert("odd-rule.md")), ["alwaysApply: true"])

    def test_cursor_rule_without_frontmatter_is_always_apply_true(self):
        out = self.convert("plain-rule.md")
        self.assertEqual(alwaysapply(out), ["alwaysApply: true"])
        self.assertIn('description: "Plain Rule"', out)

    def test_export_lists_on_demand_rule_without_pasting_it(self):
        tmp = self.sync(RULES)
        export = (tmp / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        self.assertIn("# Rules loaded on demand", export)
        self.assertIn("- `rules/demand-rule.md`: Load when the demand topic comes up", export)
        self.assertNotIn("DEMAND_BODY_MARKER", export)
        self.assertEqual(export.count("# Rules loaded on demand"), 1)
        self.assertNotIn("`rules/always-rule.md`:", export)

    def test_export_pastes_always_on_glob_unknown_and_plain_rules_in_full(self):
        tmp = self.sync(RULES)
        export = (tmp / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        for marker in ("ALWAYS_BODY_MARKER", "GLOB_BODY_MARKER", "ODD_BODY_MARKER", "PLAIN_BODY_MARKER"):
            self.assertEqual(export.count(marker), 1, marker)

    def test_export_without_on_demand_rule_has_no_on_demand_section(self):
        only_always = {k: v for k, v in RULES.items() if k != "demand-rule.md"}
        tmp = self.sync(only_always)
        export = (tmp / ".github" / "copilot-instructions.md").read_text(encoding="utf-8")
        self.assertNotIn("Rules loaded on demand", export)
        self.assertIn("ALWAYS_BODY_MARKER", export)


if __name__ == "__main__":
    unittest.main()
