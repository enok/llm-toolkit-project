"""Coverage guard: every learning is linked from an owning asset and indexed.

A learning file in ``learnings/`` (other than ``INDEX.md`` and ``README.md``) must be

1. referenced as the string ``learnings/<slug>.md`` by at least one file under
   ``skills/``, ``rules/``, ``workflows/`` or ``tool-subagents/`` (the owning skill,
   rule, workflow or agent definition carries the lesson and links the evidence), and
2. listed in ``learnings/INDEX.md`` (a line containing the backticked file name, the
   same form ``scripts/validate-toolkit-indexes.sh`` checks).

``check_tree`` holds the logic so the second test class can run it against a temporary
fixture tree. See ``rules/error-driven-learning.md``: a new learning ships in the same
change as its link from the owning asset.

Learnings are never moved into subfolders: both this test and the index validator
(``scripts/validate-toolkit-indexes.sh``) scan ``learnings/*.md`` only. A promoted
learning keeps its file and its INDEX line; its owning asset links it.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]

OWNER_DIRS = ("skills", "rules", "workflows", "tool-subagents")
NON_LEARNING_FILES = ("INDEX.md", "README.md")
SKIPPED_DIR_NAMES = ("__pycache__",)
SKIPPED_SUFFIXES = (".pyc",)


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


def owner_files(root: Path) -> List[Path]:
    """Return every regular file under the owner directories of ``root``."""
    files: List[Path] = []
    for name in OWNER_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix in SKIPPED_SUFFIXES:
                continue
            if any(part in SKIPPED_DIR_NAMES for part in path.relative_to(root).parts):
                continue
            files.append(path)
    return files


def check_tree(root: Path) -> Dict[str, List[str]]:
    """Report learnings of the tree at ``root`` that break the promotion contract.

    Returns ``{"unlinked": [...], "missing_from_index": [...]}`` with sorted slugs.
    Both lists are empty when every learning is promoted and indexed.
    """
    slugs = learning_slugs(root)
    needles = {slug: ("learnings/%s.md" % slug).encode("utf-8") for slug in slugs}

    pending = set(slugs)
    for path in owner_files(root):
        if not pending:
            break
        try:
            data = path.read_bytes()
        except OSError:
            continue
        for slug in sorted(pending):
            if needles[slug] in data:
                pending.discard(slug)
    unlinked = sorted(pending)

    index_path = root / "learnings" / "INDEX.md"
    index_text = ""
    if index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8", errors="replace")
    index_lines = index_text.splitlines()
    missing_from_index = sorted(
        slug
        for slug in slugs
        if not any("`%s.md`" % slug in line for line in index_lines)
    )
    return {"unlinked": unlinked, "missing_from_index": missing_from_index}


def format_report(report: Dict[str, List[str]]) -> str:
    """Render a failing report with the remediation for each list."""
    lines: List[str] = []
    if report["unlinked"]:
        lines.append(
            "Learnings not referenced as learnings/<slug>.md by any file under %s: %s. "
            "Add a '## Known pitfalls' bullet (or the path in existing text) to the owning "
            "skill, rule, workflow or agent definition in the same change."
            % (", ".join(OWNER_DIRS), ", ".join(report["unlinked"]))
        )
    if report["missing_from_index"]:
        lines.append(
            "Learnings with no line in learnings/INDEX.md: %s. "
            "Append one line per learning under its category heading."
            % ", ".join(report["missing_from_index"])
        )
    return "\n".join(lines)


class RepositoryCoverageTest(unittest.TestCase):
    """The toolkit itself keeps the contract."""

    def test_every_learning_is_linked_and_indexed(self) -> None:
        report = check_tree(ROOT)
        self.assertEqual({"unlinked": [], "missing_from_index": []}, report, format_report(report))


class FixtureTreeTest(unittest.TestCase):
    """The check fails on an unlinked learning, proved on a temporary tree."""

    def build_tree(self, root: Path, learnings: List[str], indexed: List[str], links: Dict[str, str]) -> None:
        (root / "learnings").mkdir(parents=True)
        (root / "learnings" / "README.md").write_text("# Learnings\n", encoding="utf-8")
        for slug in learnings:
            (root / "learnings" / ("%s.md" % slug)).write_text("# %s\n" % slug, encoding="utf-8")
        index_lines = ["- [`%s.md`](./%s.md) - summary" % (slug, slug) for slug in indexed]
        (root / "learnings" / "INDEX.md").write_text("# Index\n\n" + "\n".join(index_lines) + "\n", encoding="utf-8")
        for rel, text in links.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")

    def test_reports_the_unlinked_learning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=["linked-lesson", "unlinked-lesson"],
                indexed=["linked-lesson", "unlinked-lesson"],
                links={
                    "skills/demo/SKILL.md": "## Known pitfalls\n\n- Check it. See learnings/linked-lesson.md.\n",
                },
            )
            report = check_tree(root)
        self.assertEqual(["unlinked-lesson"], report["unlinked"])
        self.assertEqual([], report["missing_from_index"])
        self.assertIn("unlinked-lesson", format_report(report))

    def test_passes_when_every_learning_is_linked_and_indexed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=["first-lesson", "second-lesson", "third-lesson", "fourth-lesson"],
                indexed=["first-lesson", "second-lesson", "third-lesson", "fourth-lesson"],
                links={
                    "skills/demo/references/notes.md": "See learnings/first-lesson.md.\n",
                    "rules/demo.md": "See learnings/second-lesson.md.\n",
                    "workflows/demo.md": "See learnings/third-lesson.md.\n",
                    "tool-subagents/demo.toml": 'developer_instructions = """See learnings/fourth-lesson.md."""\n',
                },
            )
            report = check_tree(root)
        self.assertEqual({"unlinked": [], "missing_from_index": []}, report)
        self.assertEqual("", format_report(report))

    def test_reports_a_learning_missing_from_the_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=["indexed-lesson", "unindexed-lesson"],
                indexed=["indexed-lesson"],
                links={
                    "rules/demo.md": "See learnings/indexed-lesson.md and learnings/unindexed-lesson.md.\n",
                },
            )
            report = check_tree(root)
        self.assertEqual([], report["unlinked"])
        self.assertEqual(["unindexed-lesson"], report["missing_from_index"])

    def test_references_outside_the_owner_directories_do_not_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=["only-in-docs"],
                indexed=["only-in-docs"],
                links={
                    "docs/notes.md": "See learnings/only-in-docs.md.\n",
                    "README.md": "See learnings/only-in-docs.md.\n",
                    "tests/test_demo.py": "# learnings/only-in-docs.md\n",
                },
            )
            report = check_tree(root)
        self.assertEqual(["only-in-docs"], report["unlinked"])

    def test_a_longer_slug_does_not_link_a_shorter_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(
                root,
                learnings=["pipe", "pipe-quoting"],
                indexed=["pipe", "pipe-quoting"],
                links={
                    "skills/demo/SKILL.md": "See learnings/pipe-quoting.md.\n",
                },
            )
            report = check_tree(root)
        self.assertEqual(["pipe"], report["unlinked"])

    def test_index_and_readme_are_not_learnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.build_tree(root, learnings=[], indexed=[], links={})
            self.assertEqual([], learning_slugs(root))
            self.assertEqual({"unlinked": [], "missing_from_index": []}, check_tree(root))

    def test_a_learning_with_no_index_file_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "learnings").mkdir()
            (root / "learnings" / "lonely-lesson.md").write_text("# lonely\n", encoding="utf-8")
            (root / "rules").mkdir()
            (root / "rules" / "demo.md").write_text("See learnings/lonely-lesson.md.\n", encoding="utf-8")
            report = check_tree(root)
        self.assertEqual([], report["unlinked"])
        self.assertEqual(["lonely-lesson"], report["missing_from_index"])


if __name__ == "__main__":
    unittest.main()
