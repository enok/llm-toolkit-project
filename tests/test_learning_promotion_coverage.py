"""Coverage guard for the learning intake contract.

``learnings/`` is a short-lived intake (``rules/error-driven-learning.md``): a lesson is
written into its owning skill, rule or workflow, and a file ``learnings/<slug>.md`` exists
only while its owner is unclear. When it is migrated, the file and its INDEX line are
deleted in the same change. This guard checks two things:

1. every learning file present (other than ``INDEX.md`` and ``README.md``) has a line in
   ``learnings/INDEX.md`` containing its backticked file name, and every backticked
   ``<name>.md`` in the INDEX exists (the forms ``scripts/validate-toolkit-indexes.sh``
   checks), and
2. no file under ``skills/``, ``rules/``, ``workflows/``, ``tool-subagents/``, ``docs/``,
   ``scripts/`` or a root ``*.md`` file references ``learnings/<name>.md`` for a file that
   does not exist. Placeholders such as ``learnings/<slug>.md`` or ``learnings/*.md`` do
   not match, and the ledger ``docs/llm/value-checks.csv`` (history of removed
   resources) is skipped.

``check_tree`` holds the logic so the fixture tests can run it against temporary trees.
Learnings are never moved into subfolders: only ``learnings/*.md`` is scanned.
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]

SCANNED_DIRS = ("skills", "rules", "workflows", "tool-subagents", "docs", "scripts",
                "rubrics", "clients", "integrations", "kb", ".github")
NON_LEARNING_FILES = ("INDEX.md", "README.md")
SKIPPED_FILES = ("docs/llm/value-checks.csv",)
SKIPPED_DIR_NAMES = ("__pycache__", "node_modules")
SKIPPED_SUFFIXES = (".pyc",)

# A reference is ``learnings/<name>.md`` optionally behind ``./`` or ``../`` segments, and
# not the tail of a longer path such as ``other/learnings/x.md``. ``<name>`` must start
# with a letter or digit, so placeholders (``<slug>``, ``*``) never match.
INDEX_ENTRY = re.compile(r"`([a-z0-9][a-z0-9-]+\.md)`")
REFERENCE = re.compile(r"(?<![\w/.-])(?:\.{1,2}/)*learnings/([A-Za-z0-9][A-Za-z0-9_-]*)\.md")


def learning_slugs(root: Path) -> List[str]:
    """Return the sorted slugs of the learning files directly under ``root/learnings``."""
    directory = root / "learnings"
    if not directory.is_dir():
        return []
    return sorted(
        path.stem
        for path in directory.iterdir()
        if path.is_file() and path.suffix == ".md" and path.name not in NON_LEARNING_FILES
    )


def scanned_files(root: Path) -> List[Path]:
    """Return the root ``*.md`` files and every regular file under the scanned directories."""
    files: List[Path] = sorted(path for path in root.glob("*.md") if path.is_file())
    for name in SCANNED_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix in SKIPPED_SUFFIXES:
                continue
            rel = path.relative_to(root)
            if rel.as_posix() in SKIPPED_FILES:
                continue
            if any(part in SKIPPED_DIR_NAMES for part in rel.parts):
                continue
            files.append(path)
    return files


def dangling_references(root: Path) -> List[str]:
    """Return sorted ``<file>: learnings/<name>.md`` entries whose target does not exist."""
    found = set()
    for path in scanned_files(root):
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for name in REFERENCE.findall(text):
            if "%s.md" % name in NON_LEARNING_FILES:
                continue
            if not (root / "learnings" / ("%s.md" % name)).is_file():
                found.add("%s: learnings/%s.md" % (path.relative_to(root).as_posix(), name))
    return sorted(found)


def check_tree(root: Path) -> Dict[str, List[str]]:
    """Report breaches of the intake contract in the tree at ``root``.

    Returns ``{"missing_from_index": [...], "index_without_file": [...], "dangling": [...]}``;
    all lists are empty when every learning present is indexed, every INDEX entry exists,
    and no reference points at a missing file.
    """
    index_path = root / "learnings" / "INDEX.md"
    index_text = ""
    if index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8", errors="replace")
    index_lines = index_text.splitlines()
    missing_from_index = sorted(
        slug
        for slug in learning_slugs(root)
        if not any("`%s.md`" % slug in line for line in index_lines)
    )
    index_without_file = sorted(
        name
        for name in set(INDEX_ENTRY.findall(index_text))
        if not (root / "learnings" / name).is_file()
    )
    return {
        "missing_from_index": missing_from_index,
        "index_without_file": index_without_file,
        "dangling": dangling_references(root),
    }


def format_report(report: Dict[str, List[str]]) -> str:
    """Render a failing report with the remediation for each list."""
    lines: List[str] = []
    if report["missing_from_index"]:
        lines.append(
            "Learnings with no line in learnings/INDEX.md: %s. "
            "Add one line per pending intake item under '## Pending intake'."
            % ", ".join(report["missing_from_index"])
        )
    if report["index_without_file"]:
        lines.append(
            "learnings/INDEX.md lists files that do not exist: %s. "
            "Delete the line together with its migrated file." % ", ".join(report["index_without_file"])
        )
    if report["dangling"]:
        lines.append(
            "References to learning files that do not exist (a migrated learning is deleted; "
            "point at the owning asset instead): %s." % "; ".join(report["dangling"])
        )
    return "\n".join(lines)


class RepositoryCoverageTest(unittest.TestCase):
    """The toolkit itself keeps the contract."""

    def test_learnings_are_indexed_and_no_reference_dangles(self) -> None:
        report = check_tree(ROOT)
        self.assertEqual({"missing_from_index": [], "index_without_file": [], "dangling": []}, report, format_report(report))


class FixtureTreeTest(unittest.TestCase):
    """The checks fail on a broken tree, proved on temporary trees."""

    def build_tree(self, root: Path, learnings: List[str], indexed: List[str], files: Dict[str, str]) -> None:
        (root / "learnings").mkdir(parents=True)
        (root / "learnings" / "README.md").write_text("# Learnings\n", encoding="utf-8")
        for slug in learnings:
            (root / "learnings" / ("%s.md" % slug)).write_text("# %s\n" % slug, encoding="utf-8")
        index_lines = ["- [`%s.md`](./%s.md) - summary" % (slug, slug) for slug in indexed]
        (root / "learnings" / "INDEX.md").write_text("# Index\n\n" + "\n".join(index_lines) + "\n", encoding="utf-8")
        for rel, text in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def test_reports_a_reference_to_a_deleted_learning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=[],
                indexed=[],
                files={"skills/demo/SKILL.md": "## Known pitfalls\n\n- Check it. See learnings/migrated-lesson.md.\n"},
            )
            report = check_tree(root)
        self.assertEqual(["skills/demo/SKILL.md: learnings/migrated-lesson.md"], report["dangling"])
        self.assertEqual([], report["missing_from_index"])
        self.assertIn("migrated-lesson", format_report(report))

    def test_reports_dangling_references_in_every_scanned_location(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=[],
                indexed=[],
                files={
                    "rules/demo.md": "See `learnings/gone-a.md`.\n",
                    "workflows/demo.md": "See [x](../learnings/gone-b.md).\n",
                    "tool-subagents/demo.toml": 'developer_instructions = """See learnings/gone-c.md."""\n',
                    "docs/notes.md": "See ./learnings/gone-d.md.\n",
                    "scripts/demo.sh": "# learnings/gone-e.md\n",
                    "README.md": "See learnings/gone-f.md.\n",
                    "rubrics/demo.md": "See learnings/gone-g.md.\n",
                    "clients/demo.md": "See learnings/gone-h.md.\n",
                    "integrations/demo.md": "See learnings/gone-i.md.\n",
                    "kb/demo.md": "See learnings/gone-j.md.\n",
                    ".github/demo.md": "See learnings/gone-k.md.\n",
                },
            )
            report = check_tree(root)
        self.assertEqual(
            [
                ".github/demo.md: learnings/gone-k.md",
                "README.md: learnings/gone-f.md",
                "clients/demo.md: learnings/gone-h.md",
                "docs/notes.md: learnings/gone-d.md",
                "integrations/demo.md: learnings/gone-i.md",
                "kb/demo.md: learnings/gone-j.md",
                "rubrics/demo.md: learnings/gone-g.md",
                "rules/demo.md: learnings/gone-a.md",
                "scripts/demo.sh: learnings/gone-e.md",
                "tool-subagents/demo.toml: learnings/gone-c.md",
                "workflows/demo.md: learnings/gone-b.md",
            ],
            report["dangling"],
        )

    def test_reports_an_index_line_target_missing_from_the_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(root, learnings=["indexed-lesson", "unindexed-lesson"], indexed=["indexed-lesson"], files={})
            report = check_tree(root)
        self.assertEqual(["unindexed-lesson"], report["missing_from_index"])
        self.assertEqual([], report["dangling"])
        self.assertIn("unindexed-lesson", format_report(report))

    def test_reports_an_index_line_pointing_at_a_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(root, learnings=["kept-lesson"], indexed=["kept-lesson", "deleted-lesson"], files={})
            report = check_tree(root)
        self.assertEqual(["deleted-lesson.md"], report["index_without_file"])
        self.assertEqual([], report["missing_from_index"])
        self.assertIn("deleted-lesson.md", format_report(report))

    def test_passes_with_pending_items_indexed_and_referenced(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=["pending-lesson"],
                indexed=["pending-lesson"],
                files={"rules/demo.md": "Pending: learnings/pending-lesson.md.\n"},
            )
            report = check_tree(root)
        self.assertEqual({"missing_from_index": [], "index_without_file": [], "dangling": []}, report)
        self.assertEqual("", format_report(report))

    def test_placeholders_index_readme_ledger_and_foreign_paths_are_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=[],
                indexed=[],
                files={
                    "rules/demo.md": (
                        "learnings/<slug>.md learnings/<topic>.md learnings/<kebab-topic>.md "
                        "learnings/<file>.md learnings/*.md learnings/README.md learnings/INDEX.md "
                        "other/learnings/elsewhere.md\n"
                    ),
                    "docs/llm/value-checks.csv": "removed,learnings/history-only.md\n",
                    "tests/test_demo.py": "# learnings/test-only.md\n",
                    "examples/notes.md": "learnings/example-only.md\n",
                    "skills/demo/__pycache__/x.md": "learnings/cache-only.md\n",
                },
            )
            report = check_tree(root)
        self.assertEqual({"missing_from_index": [], "index_without_file": [], "dangling": []}, report)

    def test_a_longer_name_does_not_satisfy_a_shorter_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=["pipe-quoting"],
                indexed=["pipe-quoting"],
                files={"skills/demo/SKILL.md": "See learnings/pipe-quoting.md and learnings/pipe.md.\n"},
            )
            report = check_tree(root)
        self.assertEqual(["skills/demo/SKILL.md: learnings/pipe.md"], report["dangling"])

    def test_index_and_readme_are_not_learnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(root, learnings=[], indexed=[], files={})
            self.assertEqual([], learning_slugs(root))
            self.assertEqual({"missing_from_index": [], "index_without_file": [], "dangling": []}, check_tree(root))

    def test_a_learning_with_no_index_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "learnings").mkdir()
            (root / "learnings" / "lonely-lesson.md").write_text("# lonely\n", encoding="utf-8")
            report = check_tree(root)
        self.assertEqual(["lonely-lesson"], report["missing_from_index"])


if __name__ == "__main__":
    unittest.main()
