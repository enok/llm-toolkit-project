from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


TESTS = Path(__file__).resolve().parent
SCRIPTS = TESTS.parent / "skills" / "multi-language-study-repo" / "scripts"
FIXTURE = TESTS / "fixtures" / "multi-language-study-repo" / "repo"
CHECK_SCRIPT = SCRIPTS / "check_docs.py"
GEN_SCRIPT = SCRIPTS / "gen_code_by_component.py"
EXAMPLE_CONFIG = SCRIPTS / "components.example.json"


def load_script(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


check_docs = load_script("study_repo_check_docs", CHECK_SCRIPT)
gen = load_script("study_repo_gen_code_by_component", GEN_SCRIPT)


def run(module, *argv: str):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = module.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def to_crlf(path: Path) -> None:
    data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n")
    path.write_bytes(data)


class RepoCase(unittest.TestCase):
    """Each test works on its own copy of the fixture repo."""

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.repo = self.tmp / "repo"
        shutil.copytree(FIXTURE, self.repo)
        # the committed fixture keeps the diagram as .mmd.txt (repo policy: no .mmd files); the
        # tests work on a temp copy where it is the real docs/diagrams/overview.mmd
        stored = self.repo / "docs" / "diagrams" / "overview.mmd.txt"
        stored.rename(stored.with_name("overview.mmd"))

    def write(self, rel: str, text: str, root: Path = None) -> Path:
        path = (root or self.repo) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))  # bytes: no newline translation on any platform
        return path

    def read(self, rel: str) -> str:
        return (self.repo / rel).read_text(encoding="utf-8")

    def symlink(self, link: Path, target) -> None:
        try:
            link.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are not available here")

    def emulate_case_insensitive_volume(self) -> None:
        """Make Path.exists/is_file answer like Windows or macOS do (letter case ignored)."""
        def real_path(path: Path):
            current = Path(path.anchor)
            for part in path.parts[1:]:
                try:
                    matches = [name for name in os.listdir(str(current)) if name.lower() == part.lower()]
                except OSError:
                    return None
                if not matches:
                    return None
                current = current / matches[0]
            return current

        stack = contextlib.ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(mock.patch.object(Path, "exists", lambda self: real_path(self) is not None))
        stack.enter_context(mock.patch.object(
            Path, "is_file", lambda self: real_path(self) is not None and os.path.isfile(str(real_path(self)))))

    def program(self, script: Path, *argv: str, cwd: Path = None, encoding: str = None):
        """Run a script as a real process; `encoding` pins the std streams (PYTHONIOENCODING)."""
        env = {k: v for k, v in os.environ.items() if k not in ("PYTHONUTF8", "PYTHONIOENCODING")}
        if encoding:
            env["PYTHONIOENCODING"] = encoding
        done = subprocess.run([sys.executable, str(script), *argv], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              cwd=str(cwd or self.tmp), env=env)
        text_encoding = encoding or "utf-8"

        def text(data: bytes) -> str:  # Windows text-mode std streams write CRLF; compare with LF
            return data.decode(text_encoding).replace("\r\n", "\n")

        return done.returncode, text(done.stdout), text(done.stderr)

    def append(self, rel: str, text: str) -> None:
        self.write(rel, self.read(rel) + text)

    def line_of(self, rel: str, needle: str) -> int:
        for no, line in enumerate(self.read(rel).split("\n"), 1):
            if needle in line:
                return no
        raise AssertionError(f"{needle!r} not in {rel}")

    def check(self, *extra: str):
        return run(check_docs, "--root", str(self.repo), *extra)

    def issues(self, *extra: str):
        code, out, _ = self.check(*extra)
        return code, ([] if code == 0 else [line for line in out.split("\n") if line])

    def check_only(self, *docs: str):
        """Scan just `docs` (an empty diagrams folder keeps the fixture's .mmd out of the picture)."""
        (self.repo / "empty-diagrams").mkdir(exist_ok=True)
        return self.check("--diagrams", "empty-diagrams", "--docs", *docs)

    def issues_only(self, *docs: str):
        code, out, _ = self.check_only(*docs)
        return code, ([] if code == 0 else [line for line in out.split("\n") if line])

    def generate(self, *extra: str, config: str = "components.json"):
        return run(gen, "--config", str(self.repo / config), "--root", str(self.repo), *extra)

    def config(self) -> dict:
        return json.loads(self.read("components.json"))

    def write_config(self, data, name: str = "alt.json") -> Path:
        return self.write(name, json.dumps(data))


# --------------------------------------------------------------------------- check_docs


class FixtureTreeTests(unittest.TestCase):
    def test_committed_fixture_tree_uses_only_policy_allowed_suffixes(self) -> None:
        files = [path for path in FIXTURE.rglob("*") if path.is_file()]
        self.assertTrue(files)
        self.assertEqual(sorted({path.suffix for path in files} - {".py", ".js", ".md", ".json", ".txt"}), [])
        self.assertTrue((FIXTURE / "docs" / "diagrams" / "overview.mmd.txt").is_file())
        self.assertFalse(list(FIXTURE.rglob("*.mmd")))


class CheckDocsHappyPathTests(RepoCase):
    def test_fixture_repo_is_clean(self) -> None:
        self.assertEqual(self.check(), (0, "ok\n", ""))

    def test_crlf_everywhere_is_still_clean(self) -> None:
        for path in self.repo.rglob("*"):
            if path.is_file():
                to_crlf(path)
        self.assertEqual(self.check()[:2], (0, "ok\n"))

    def test_explicit_defaults_behave_like_implicit(self) -> None:
        self.assertEqual(self.check("--diagrams", "docs/diagrams", "--docs", "docs", "README.md")[:2], (0, "ok\n"))

    def test_extra_trailing_newline_policy(self) -> None:
        mmd = "docs/diagrams/overview.mmd"
        body = "flowchart LR\n  Client --> Context\n  Context --> Strategy"
        for text, expected in ((body, 0), (body + "\n", 0), (body + "\r\n", 0), (body + "\n\n", 1)):
            with self.subTest(trailing=repr(text[len(body):])):
                self.write(mmd, text)
                self.assertEqual(self.check()[0], expected)


class CheckDocsDiagramTests(RepoCase):
    def test_changed_mmd_is_drift(self) -> None:
        self.write("docs/diagrams/overview.mmd", "flowchart LR\n  Client --> Strategy\n")
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("docs/diagrams/overview.mmd: not identical"), lines[0])

    def test_mmd_without_any_block_is_reported(self) -> None:
        self.write("docs/diagrams/extra.mmd", "graph TD\n  A --> B\n")
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertEqual([line.split(":")[0] for line in lines], ["docs/diagrams/extra.mmd"])

    def test_nested_mmd_is_found_and_reported_with_posix_path(self) -> None:
        self.write("docs/diagrams/deep/er.mmd", "erDiagram\n  A ||--o{ B : has\n")
        self.assertEqual(self.issues()[1][0].split(":")[0], "docs/diagrams/deep/er.mmd")

    def test_block_must_be_equal_not_a_superset(self) -> None:
        self.write("docs/01-overview.md", self.read("docs/01-overview.md").replace(
            "  Context --> Strategy\n", "  Context --> Strategy\n  Strategy --> Concrete\n"))
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertIn("overview.mmd", lines[0])

    def test_only_mermaid_fences_count(self) -> None:
        self.write("docs/01-overview.md", self.read("docs/01-overview.md").replace("```mermaid", "```text"))
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertIn("overview.mmd", lines[0])

    def test_block_may_live_in_any_scanned_doc_including_nested_and_tilde_fences(self) -> None:
        self.write("docs/diagrams/other.mmd", "sequenceDiagram\n  A->>B: hi\n")
        self.write("docs/sub/other.md", "# Other\n\n~~~mermaid\nsequenceDiagram\n  A->>B: hi\n~~~\n")
        self.assertEqual(self.check()[:2], (0, "ok\n"))

    def test_mermaid_info_string_is_case_insensitive_and_may_have_attributes(self) -> None:
        self.write("docs/diagrams/other.mmd", "graph TD\n  A --> B\n")
        self.write("docs/other.md", "```Mermaid title=x\ngraph TD\n  A --> B\n```\n")
        self.assertEqual(self.check()[:2], (0, "ok\n"))

    def test_fenced_block_nested_in_a_list_is_deindented(self) -> None:
        self.write("docs/diagrams/other.mmd", "graph TD\n  A --> B\n")
        self.write("docs/other.md", "- step\n\n  ```mermaid\n  graph TD\n    A --> B\n  ```\n")
        self.assertEqual(self.check()[:2], (0, "ok\n"))

    def test_custom_diagrams_dir(self) -> None:
        self.write("art/x.mmd", "graph TD\n  X --> Y\n")
        code, lines = self.issues("--diagrams", "art")
        self.assertEqual((code, [line.split(":")[0] for line in lines]), (1, ["art/x.mmd"]))

    def test_diagram_check_is_skipped_when_default_dir_is_absent(self) -> None:
        shutil.rmtree(self.repo / "docs" / "diagrams")
        overview = self.read("docs/01-overview.md").replace("and the [diagram source](diagrams/overview.mmd).", "")
        self.write("docs/01-overview.md", overview)
        self.assertEqual(self.check()[:2], (0, "ok\n"))


class CheckDocsSourceTests(RepoCase):
    def test_drift_is_reported_in_every_page_that_embeds_the_file(self) -> None:
        self.append("javascript/src/strategy.js", "// drift\n")
        code, lines = self.issues()
        self.assertEqual(code, 1)
        overview = self.line_of("docs/01-overview.md", "<!-- source:")
        page = self.line_of("docs/05-code-by-component.md", "<!-- source: javascript/src/strategy.js")
        self.assertEqual(lines, [
            f"docs/01-overview.md: line {overview}: code block differs from source file -> javascript/src/strategy.js",
            f"docs/05-code-by-component.md: line {page}: code block differs from source file -> javascript/src/strategy.js",
        ])

    def test_missing_source_file(self) -> None:
        (self.repo / "javascript" / "src" / "strategy.js").unlink()
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertTrue(all("source file not found -> javascript/src/strategy.js" in line for line in lines), lines)
        self.assertEqual(len(lines), 2)

    def test_source_with_crlf_or_without_final_newline_matches(self) -> None:
        strategy = self.repo / "javascript" / "src" / "strategy.js"
        original = strategy.read_bytes()
        for label, data in (("crlf", original.replace(b"\n", b"\r\n")), ("no final newline", original.rstrip(b"\n"))):
            with self.subTest(label):
                strategy.write_bytes(data)
                self.assertEqual(self.check()[:2], (0, "ok\n"))

    def test_extra_blank_line_in_source_is_drift(self) -> None:
        self.append("javascript/src/strategy.js", "\n")
        self.assertEqual(self.check()[0], 1)

    def test_marker_not_followed_by_a_fence_is_reported(self) -> None:
        self.append("docs/01-overview.md", "\n<!-- source: python/src/strategy.py -->\n\nno fence here\n")
        code, lines = self.issues()
        line = self.line_of("docs/01-overview.md", "python/src/strategy.py")
        self.assertEqual((code, lines), (1, [
            f"docs/01-overview.md: line {line}: source marker not followed by a fenced block -> python/src/strategy.py"]))

    def test_marker_at_end_of_file_is_reported(self) -> None:
        self.append("docs/01-overview.md", "\n<!-- source: python/src/strategy.py -->")
        self.assertIn("not followed by a fenced block", self.issues()[1][0])

    def test_blank_line_between_marker_and_fence_does_not_count_as_immediately_preceded(self) -> None:
        self.append("docs/01-overview.md", "\n<!-- source: python/src/strategy.py -->\n\n```python\nwrong\n```\n")
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertIn("not followed by a fenced block", lines[0])

    def test_marker_paths_must_stay_inside_the_repo(self) -> None:
        outside = self.tmp / "outside.txt"
        outside.write_text("x\n", encoding="utf-8")
        for marker in ("../outside.txt", "python/../../outside.txt", str(outside)):
            with self.subTest(marker=marker):
                self.write("docs/extra.md", f"<!-- source: {marker} -->\n```text\nx\n```\n")
                code, lines = self.issues_only("docs/extra.md")
                self.assertEqual(code, 1)
                self.assertIn("source path must be repo-relative and inside the repo", lines[0])

    def test_marker_before_a_mermaid_block_guards_the_diagram_file_too(self) -> None:
        self.write("docs/extra.md",
                   "<!-- source: docs/diagrams/overview.mmd -->\n```mermaid\n"
                   "flowchart LR\n  Client --> Context\n  Context --> Strategy\n```\n")
        self.assertEqual(self.check()[:2], (0, "ok\n"))
        self.write("docs/diagrams/overview.mmd", "flowchart LR\n  Client --> Context\n")
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertTrue(any(line.startswith("docs/extra.md: line 1: code block differs") for line in lines), lines)

    def test_block_nested_in_a_list_is_compared_deindented(self) -> None:
        self.write("docs/extra.md",
                   "1. step\n\n   <!-- source: javascript/src/demo.js -->\n   ```javascript\n"
                   + "".join(f"   {line}\n" if line else "\n" for line in self.read("javascript/src/demo.js").split("\n")[:-1])
                   + "   ```\n")
        self.assertEqual(self.check_only("docs/extra.md")[:2], (0, "ok\n"))

    def test_longer_outer_fence_is_not_closed_by_inner_triple_backticks(self) -> None:
        # python/src/demo.py contains a ``` line; the fixture page wraps it in a 4-backtick fence
        self.assertIn("````python", self.read("docs/05-code-by-component.md"))
        self.assertEqual(self.check()[:2], (0, "ok\n"))


class CheckDocsLinkTests(RepoCase):
    def broken(self, text: str, *, rel: str = "README.md"):
        self.append(rel, text)
        code, lines = self.issues()
        return code, lines

    def test_broken_relative_link_is_reported_with_file_and_line(self) -> None:
        code, lines = self.broken("\n[gone](docs/missing.md)\n")
        line = self.line_of("README.md", "docs/missing.md")
        self.assertEqual((code, lines), (1, [f"README.md: line {line}: broken link -> docs/missing.md"]))

    def test_anchor_does_not_rescue_a_missing_target_and_query_is_ignored(self) -> None:
        code, lines = self.broken("\n[a](docs/missing.md#section) [b](docs/01-overview.md?plain=1#fixture-overview)\n")
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].endswith("broken link -> docs/missing.md#section"), lines[0])

    def test_external_mailto_and_pure_anchor_links_are_skipped(self) -> None:
        text = ("\n[a](https://example.invalid/nope) [b](http://example.invalid/nope) [c](mailto:x@example.com) "
                "[d](#nowhere) [e](//cdn.example.invalid/x.js) [f](tel:+100) [g](ftp://example.invalid/x)\n")
        self.assertEqual(self.broken(text), (0, []))

    def test_links_inside_fenced_or_inline_code_are_ignored(self) -> None:
        text = "\n```md\n[x](nope.md)\n```\n~~~\n[y](nope2.md)\n~~~\nInline `[z](nope3.md)` and ``[w](nope4.md)``.\n"
        self.assertEqual(self.broken(text), (0, []))

    def test_links_after_a_closed_fence_are_checked_again(self) -> None:
        code, lines = self.broken("\n```\n[x](nope.md)\n```\n[after](nope-after.md)\n")
        self.assertEqual((code, len(lines)), (1, 1))
        self.assertIn("nope-after.md", lines[0])

    def test_images_and_image_inside_link(self) -> None:
        code, lines = self.broken("\n![alt](docs/missing.png)\n[![badge](docs/diagrams/overview.mmd)](docs/missing2.md)\n")
        self.assertEqual(code, 1)
        self.assertEqual([line.rsplit("-> ", 1)[1] for line in lines], ["docs/missing.png", "docs/missing2.md"])

    def test_valid_link_forms(self) -> None:
        self.write("docs/a b.md", "x\n")
        self.write("docs/f_(1).md", "x\n")
        text = ("\n[1](docs/01-overview.md \"Title\") [2](<docs/a b.md>) [3](docs/a%20b.md) [4](docs/f_(1).md) "
                "[5](python/src/) [6](/docs/01-overview.md) [7](docs/01-overview.md#fixture-overview)\n")
        self.assertEqual(self.broken(text), (0, []))

    def test_broken_forms(self) -> None:
        text = "\n[1](<docs/no such.md>) [2](/docs/nope.md) [3](docs/nope%20x.md) [4](docs/nope/)\n"
        code, lines = self.broken(text)
        self.assertEqual(code, 1)
        self.assertEqual([line.rsplit("-> ", 1)[1] for line in lines],
                         ["docs/no such.md", "/docs/nope.md", "docs/nope%20x.md", "docs/nope/"])

    def test_link_text_wrapped_over_two_lines(self) -> None:
        self.append("README.md", "\n[text that\ncontinues](docs/missing.md)\n")
        line = self.line_of("README.md", "continues](")
        self.assertEqual(self.issues(), (1, [f"README.md: line {line}: broken link -> docs/missing.md"]))

    def test_links_resolve_relative_to_the_containing_file_in_nested_docs(self) -> None:
        self.write("docs/sub/page.md", "[ok](../01-overview.md) [bad](01-overview.md)\n")
        code, lines = self.issues()
        self.assertEqual((code, lines), (1, ["docs/sub/page.md: line 1: broken link -> 01-overview.md"]))

    def test_skipped_directories_are_not_scanned(self) -> None:
        for name in ("node_modules", ".git", "target", "__pycache__"):
            self.write(f"docs/{name}/bad.md", "[x](nope.md)\n")
        self.assertEqual(self.check()[:2], (0, "ok\n"))

    def test_issues_are_ordered_by_line_within_a_file_and_files_alphabetically(self) -> None:
        self.write("docs/b.md", "[x](nope1.md)\n\n[y](nope2.md)\n")
        self.write("docs/a.md", "[x](nope3.md)\n")
        _, lines = self.issues()
        self.assertEqual(lines, [
            "docs/a.md: line 1: broken link -> nope3.md",
            "docs/b.md: line 1: broken link -> nope1.md",
            "docs/b.md: line 3: broken link -> nope2.md",
        ])


class CheckDocsCliTests(RepoCase):
    def test_every_issue_line_is_path_colon_message(self) -> None:
        self.append("README.md", "\n[x](nope.md)\n")
        self.write("docs/diagrams/overview.mmd", "graph TD\n  Z\n")
        code, out, err = self.check()
        self.assertEqual((code, err), (1, ""))
        lines = out.rstrip("\n").split("\n")
        self.assertEqual(len(lines), 2)
        for line in lines:
            self.assertRegex(line, r"^[^:\s][^:]*: \S")

    def test_exit_2_for_bad_arguments_and_roots(self) -> None:
        file_root = self.write("not-a-dir.txt", "x")
        cases = {
            "missing root": ["--root", str(self.tmp / "nope")],
            "root is a file": ["--root", str(file_root)],
            "no --root": [],
            "unknown option": ["--root", str(self.repo), "--bogus"],
            "docs path missing": ["--root", str(self.repo), "--docs", "docs", "nope.md"],
            "diagrams missing": ["--root", str(self.repo), "--diagrams", "nope"],
            "docs outside root": ["--root", str(self.repo), "--docs", ".."],
            "diagrams outside root": ["--root", str(self.repo), "--diagrams", "../elsewhere"],
        }
        for label, argv in cases.items():
            with self.subTest(label):
                code, out, err = run(check_docs, *argv)
                self.assertEqual((code, out), (2, ""))
                self.assertTrue(err.strip())

    def test_exit_2_when_no_default_docs_exist(self) -> None:
        empty = self.tmp / "empty"
        empty.mkdir()
        code, _, err = run(check_docs, "--root", str(empty))
        self.assertEqual(code, 2)
        self.assertIn("--docs", err)

    def test_readme_only_repo_is_ok(self) -> None:
        solo = self.tmp / "solo"
        self.write("README.md", "# Solo\n", root=solo)
        self.assertEqual(run(check_docs, "--root", str(solo))[:2], (0, "ok\n"))

    def test_docs_argument_limits_what_is_scanned(self) -> None:
        self.append("docs/01-overview.md", "\n[bad](nope.md)\n")
        self.assertEqual(self.check_only("README.md")[:2], (0, "ok\n"))
        self.assertEqual(self.check_only("docs")[0], 1)
        self.assertEqual(self.check_only("docs/01-overview.md")[0], 1)

    def test_explicit_file_without_md_extension_is_scanned_and_duplicates_collapse(self) -> None:
        self.write("notes.txt", "[x](nope.md)\n")
        code, lines = self.issues_only("notes.txt", "notes.txt", "./notes.txt")
        self.assertEqual((code, lines), (1, ["notes.txt: line 1: broken link -> nope.md"]))

    def test_unreadable_markdown_is_an_issue_not_a_crash(self) -> None:
        (self.repo / "docs" / "bad.md").write_bytes(b"\xff\xfe\x00bad")
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertTrue(lines[0].startswith("docs/bad.md: cannot read file"), lines[0])

    def test_leading_bom_in_markdown_is_ignored(self) -> None:
        readme = self.repo / "README.md"
        readme.write_bytes(b"\xef\xbb\xbf" + readme.read_bytes())
        self.assertEqual(self.check()[:2], (0, "ok\n"))

    def test_help_exits_zero(self) -> None:
        self.assertEqual(run(check_docs, "--help")[0], 0)


class CheckDocsHardeningTests(RepoCase):
    def test_link_leaving_the_repo_is_reported_even_when_the_target_exists(self) -> None:
        (self.tmp / "outside.md").write_text("x\n", encoding="utf-8")
        for target in ("../outside.md", "/../outside.md", "docs/../../outside.md", "docs/sub/../../../outside.md"):
            with self.subTest(target=target):
                self.write("README.md", f"# R\n\n[x]({target})\n")
                self.assertEqual(self.issues_only("README.md"),
                                 (1, [f"README.md: line 3: link leaves the repository -> {target}"]))
        self.write("README.md", "[ok](docs/sub/../01-overview.md)\n")  # lexical ..: stays inside
        self.assertEqual(self.issues_only("README.md")[0], 0)

    def test_link_with_different_letter_case_is_broken(self) -> None:
        self.write("README.md", "[a](Docs/01-overview.md) [b](docs/01-OVERVIEW.md) [c](docs/01-overview.md)\n")
        code, lines = self.issues_only("README.md")
        self.assertEqual(code, 1)
        self.assertEqual([line.rsplit("-> ", 1)[1] for line in lines], ["Docs/01-overview.md", "docs/01-OVERVIEW.md"])

    def test_wrong_case_is_rejected_even_when_the_volume_is_case_insensitive(self) -> None:
        self.emulate_case_insensitive_volume()
        self.assertTrue((self.repo / "DOCS" / "01-OVERVIEW.md").exists())  # what Windows/macOS would answer
        self.write("README.md", "[a](DOCS/01-OVERVIEW.md) [b](docs/01-overview.md)\n")
        self.assertEqual(self.issues_only("README.md"),
                         (1, ["README.md: line 1: broken link -> DOCS/01-OVERVIEW.md"]))
        strategy = self.read("python/src/strategy.py")
        self.write("docs/extra.md", f"<!-- source: PYTHON/src/strategy.py -->\n```python\n{strategy}```\n")
        code, lines = self.issues_only("docs/extra.md")
        self.assertEqual(code, 1)
        self.assertIn("source file not found -> PYTHON/src/strategy.py", lines[0])

    def test_exists_exact_compares_every_component_by_directory_listing(self) -> None:
        root = self.repo.resolve()
        for ok in ("", "docs", "docs/diagrams", "docs/01-overview.md", "python/src/__main__.py"):
            self.assertTrue(check_docs.exists_exact(root, root / ok), ok)
        for bad in ("Docs/01-overview.md", "docs/01-OVERVIEW.md", "DOCS", "docs/nope.md", "nope/x.md",
                    "README.md/x"):
            self.assertFalse(check_docs.exists_exact(root, root / bad), bad)

    def test_marker_path_with_different_letter_case_is_not_found(self) -> None:
        self.write("docs/extra.md", "<!-- source: Python/src/strategy.py -->\n```text\nx\n```\n")
        code, lines = self.issues_only("docs/extra.md")
        self.assertEqual(code, 1)
        self.assertIn("source file not found -> Python/src/strategy.py", lines[0])

    def test_reference_style_definitions_are_checked(self) -> None:
        text = ("\n[gone]: docs/missing.md\n[ok]: docs/01-overview.md \"Title\"\n[ext]: https://example.com/x\n"
                "[angle]: <docs/no such.md>\n[^1]: footnote text\n[Note]: this is important\n"
                "   [indented]: docs/missing-indented.md\n    [code-block]: docs/not-a-definition.md\n"
                "```\n[fenced]: docs/missing-fenced.md\n```\n")
        self.append("README.md", text)
        code, lines = self.issues_only("README.md")
        self.assertEqual(code, 1)
        self.assertEqual([line.rsplit("-> ", 1)[1] for line in lines],
                         ["docs/missing.md", "docs/no such.md", "docs/missing-indented.md"])

    def test_html_src_and_href_attributes_are_checked(self) -> None:
        self.write("docs/a&b.png", "x")
        text = ("\n<img src=\"docs/missing.png\" alt=\"x\">\n<a href=\"docs/01-overview.md\">ok</a>\n"
                "<a href='https://example.com'>ext</a> <img src=\"data:image/png;base64,AAAA\"> <a href=\"#top\">t</a>\n"
                "<a name=\"n\" HREF=\"docs/nope.md\">attr order and case</a>\n<img src=\"docs/a&amp;b.png\">\n"
                "`<img src=\"docs/in-code.png\">`\n```html\n<img src=\"docs/fenced.png\">\n```\n"
                "<video src='docs/clip.mp4'></video> <p class=\"href\">not a tag attribute</p>\n")
        self.append("README.md", text)
        code, lines = self.issues_only("README.md")
        self.assertEqual(code, 1)
        self.assertEqual([line.rsplit("-> ", 1)[1] for line in lines], ["docs/missing.png", "docs/nope.md", "docs/clip.mp4"])

    def test_backslash_escaped_brackets_are_not_links(self) -> None:
        self.append("README.md", "\nLiteral \\[x\\](nope.md) and `code` and \\\\[real](nope2.md)\n")
        code, lines = self.issues_only("README.md")
        self.assertEqual((code, [line.rsplit("-> ", 1)[1] for line in lines]), (1, ["nope2.md"]))

    def test_one_line_triple_backtick_span_is_inline_code_not_a_fence(self) -> None:
        self.append("README.md", "\n```x``` and [bad](nope.md)\n[after](nope-after.md)\n")
        code, lines = self.issues_only("README.md")
        self.assertEqual([line.rsplit("-> ", 1)[1] for line in lines], ["nope.md", "nope-after.md"])

    def test_bom_at_file_start_does_not_hide_a_leading_source_marker(self) -> None:
        strategy = self.read("python/src/strategy.py")
        good = f"<!-- source: python/src/strategy.py -->\n```python\n{strategy}```\n"
        for label, body, expected in (("match", good, 0), ("drift", good.replace("Protocol", "Proto", 2), 1)):
            with self.subTest(label):
                (self.repo / "docs" / "extra.md").write_bytes(b"\xef\xbb\xbf" + body.encode("utf-8"))
                self.assertEqual(self.issues_only("docs/extra.md")[0], expected)

    def test_source_symlink_leaving_the_repo_is_rejected_but_an_inner_alias_is_fine(self) -> None:
        secret = self.tmp / "secret.txt"
        secret.write_bytes(b"TOP SECRET\n")
        self.symlink(self.repo / "python" / "src" / "leak.txt", secret)
        self.symlink(self.repo / "python" / "src" / "alias.py", "strategy.py")
        self.write("docs/extra.md", "<!-- source: python/src/leak.txt -->\n```text\nTOP SECRET\n```\n")
        self.assertEqual(self.issues_only("docs/extra.md"), (1, [
            "docs/extra.md: line 1: source file resolves outside the repository (symlink?) -> python/src/leak.txt"]))
        strategy = self.read("python/src/strategy.py")
        self.write("docs/extra.md", f"<!-- source: python/src/alias.py -->\n```python\n{strategy}```\n")
        self.assertEqual(self.issues_only("docs/extra.md")[0], 0)


class OutputEncodingTests(RepoCase):
    """A console or pipe that cannot encode a character must not lose the report."""

    def test_check_docs_reports_non_ascii_targets_as_escapes(self) -> None:
        self.append("README.md", "\n[x](docs/caf\u00e9-\u2192.md)\n")
        for encoding in ("ascii", "cp1252"):
            with self.subTest(encoding):
                code, out, err = self.program(CHECK_SCRIPT, "--root", str(self.repo), encoding=encoding)
                self.assertEqual((code, err), (1, ""))
                self.assertIn("broken link -> docs/caf", out)
                self.assertIn("\\u2192", out)
                self.assertEqual("\\xe9" in out, encoding == "ascii")

    def test_check_docs_usage_errors_with_non_ascii_paths_exit_2_cleanly(self) -> None:
        code, out, err = self.program(CHECK_SCRIPT, "--root", str(self.tmp / "d\u00e9j\u00e0-\u2192"), encoding="ascii")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("d\\xe9j\\xe0-\\u2192", err)
        self.assertNotIn("Traceback", err)

    def test_generator_reports_non_ascii_names_as_escapes_on_both_streams(self) -> None:
        data = self.config()
        data["components"][0]["files"]["python"].append("caf\u00e9-\u2192.py")
        config = self.write_config(data)
        code, out, err = self.program(GEN_SCRIPT, "--config", str(config), "--root", str(self.repo), encoding="ascii")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("caf\\xe9-\\u2192.py", err)
        self.assertNotIn("Traceback", err)
        code, out, err = self.program(GEN_SCRIPT, "--config", str(self.repo / "components.json"),
                                      "--root", str(self.repo), "--out", "docs/caf\u00e9.md", encoding="ascii")
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.strip().endswith("caf\\xe9.md"), out)
        self.assertTrue((self.repo / "docs" / "caf\u00e9.md").is_file())

    def test_harden_output_streams_switches_to_backslashreplace_and_keeps_the_newline_mode(self) -> None:
        for module in (check_docs, gen):
            for newline in ("\n", "\r\n"):  # "\r\n" is what a Windows text-mode console/pipe uses
                with self.subTest(module=module.__name__, newline=newline):
                    raw = io.BytesIO()
                    stream = io.TextIOWrapper(raw, encoding="ascii", newline=newline)  # errors strict
                    with mock.patch.object(sys, "stdout", stream), mock.patch.object(sys, "stderr", stream):
                        module.harden_output_streams()
                        print("caf\u00e9 \u2192")
                    stream.flush()
                    self.assertEqual(raw.getvalue(), b"caf\\xe9 \\u2192" + newline.encode("ascii"))
                    stream.detach()

    def test_harden_output_streams_tolerates_streams_without_reconfigure(self) -> None:
        for module in (check_docs, gen):
            with mock.patch.object(sys, "stdout", io.StringIO()), mock.patch.object(sys, "stderr", io.StringIO()):
                module.harden_output_streams()


class CliPathResolutionTests(RepoCase):
    def test_config_is_resolved_against_the_cwd_or_taken_as_absolute(self) -> None:
        nested = self.repo / ".github" / "scripts"
        nested.mkdir(parents=True)
        shutil.copy(self.repo / "components.json", nested / "components.json")
        page = self.repo / "docs" / "05-code-by-component.md"
        page.unlink()
        relative = [".github/scripts/components.json", "--root", "."]  # the documented CI form
        self.assertEqual(self.program(GEN_SCRIPT, "--config", *relative, cwd=self.repo)[0], 0)
        self.assertTrue(page.is_file())
        self.assertEqual(self.program(GEN_SCRIPT, "--config", *relative, "--check", cwd=self.repo)[0], 0)
        self.assertEqual(self.program(GEN_SCRIPT, "--config", str(nested / "components.json"),
                                      "--root", str(self.repo), "--check", cwd=self.tmp)[0], 0)
        shutil.copy(self.repo / "components.json", self.tmp / "cfg.json")
        self.assertEqual(self.program(GEN_SCRIPT, "--config", "cfg.json", "--root", "repo", "--check",
                                      cwd=self.tmp)[0], 0)  # relative to cwd, not to --root
        code, _, err = self.program(GEN_SCRIPT, "--config", "components.json", "--root", str(self.repo), cwd=self.tmp)
        self.assertEqual(code, 2)  # a config that only exists relative to --root is not found
        self.assertIn("cannot read config", err)

    def test_check_docs_accepts_a_relative_root(self) -> None:
        self.assertEqual(self.program(CHECK_SCRIPT, "--root", ".", cwd=self.repo)[:2], (0, "ok\n"))
        self.assertEqual(self.program(CHECK_SCRIPT, "--root", "repo", cwd=self.tmp)[:2], (0, "ok\n"))
        self.append("README.md", "\n[x](nope.md)\n")
        code, out, _ = self.program(CHECK_SCRIPT, "--root", ".", "--docs", "README.md", cwd=self.repo)
        self.assertEqual((code, out.count("README.md: line")), (1, 1))


# --------------------------------------------------------------------------- gen_code_by_component


class GeneratorOutputTests(RepoCase):
    def test_generating_reproduces_the_committed_golden_page(self) -> None:
        self.assertEqual(self.generate("--out", "docs/regenerated.md")[0], 0)
        self.assertEqual((self.repo / "docs" / "regenerated.md").read_bytes(),
                         (FIXTURE / "docs" / "05-code-by-component.md").read_bytes())

    def test_page_structure(self) -> None:
        self.generate("--out", "docs/page.md")
        text = self.read("docs/page.md")
        lines = text.split("\n")
        self.assertEqual(lines[0], "# Code by component - Python and JavaScript")
        self.assertEqual(lines[1], "")
        self.assertEqual(lines[2], "Each role of the pattern is shown in every language. Files are shown whole.")
        self.assertEqual(lines[3:7], ["", "1. [Strategy interface](#1-strategy-interface)",
                                      "2. [Client (demo)](#2-client-demo)", ""])
        self.assertEqual([line for line in lines if line.startswith("## ")],
                         ["## 1. Strategy interface", "## 2. Client (demo)"])
        self.assertIn("## 1. Strategy interface\n\nThe Strategy declares the single operation every "
                      "interchangeable algorithm offers.\n\n<details open>", text)

    def test_only_the_first_language_of_each_component_is_open(self) -> None:
        self.generate("--out", "docs/page.md")
        text = self.read("docs/page.md")
        self.assertEqual(text.count("<details open>"), 2)
        self.assertEqual(text.count("<details>"), 2)
        self.assertEqual(re.findall(r"<details( open)?>\n<summary><b>([^<]+)</b>", text), [
            (" open", "Python 3"), ("", "JavaScript (ES2026)"), (" open", "Python 3"), ("", "JavaScript (ES2026)")])

    def test_summary_lists_file_names_joined_by_comma(self) -> None:
        self.generate("--out", "docs/page.md")
        text = self.read("docs/page.md")
        self.assertIn("<summary><b>Python 3</b> · <code>demo.py, __main__.py</code></summary>\n\n", text)
        self.assertIn("<summary><b>JavaScript (ES2026)</b> · <code>demo.js</code></summary>\n\n", text)

    def test_every_file_gets_a_source_comment_and_a_fenced_block_with_exact_content(self) -> None:
        self.generate("--out", "docs/page.md")
        text = self.read("docs/page.md")
        self.assertEqual(re.findall(r"<!-- source: (\S+) -->", text), [
            "python/src/strategy.py", "javascript/src/strategy.js",
            "python/src/demo.py", "python/src/__main__.py", "javascript/src/demo.js"])
        self.assertIn("<!-- source: javascript/src/demo.js -->\n```javascript\n"
                      + self.read("javascript/src/demo.js") + "```\n\n</details>", text)
        self.assertIn("<!-- source: python/src/__main__.py -->\n```python\nfrom .demo import main\n\nmain()\n```\n\n", text)

    def test_fence_grows_when_the_code_contains_backticks(self) -> None:
        self.generate("--out", "docs/page.md")
        text = self.read("docs/page.md")
        self.assertIn("<!-- source: python/src/demo.py -->\n````python\n", text)
        self.assertIn("<!-- source: javascript/src/strategy.js -->\n```javascript\n", text)  # single backticks only

    def test_blank_lines_around_details_parts(self) -> None:
        self.generate("--out", "docs/page.md")
        text = self.read("docs/page.md")
        self.assertRegex(text, r"</summary>\n\n<!-- source:")
        self.assertEqual(text.count("</details>\n\n"), 3)  # the last one ends the file
        self.assertTrue(text.endswith("</details>\n"))

    def test_single_trailing_newline_and_lf_only(self) -> None:
        self.generate("--out", "docs/page.md")
        data = (self.repo / "docs" / "page.md").read_bytes()
        self.assertTrue(data.endswith(b"\n") and not data.endswith(b"\n\n"))
        self.assertNotIn(b"\r", data)

    def test_output_is_deterministic_and_lf_even_when_sources_are_crlf(self) -> None:
        self.generate("--out", "docs/a.md")
        for path in (self.repo / "python").rglob("*.py"):
            to_crlf(path)
        for path in (self.repo / "javascript").rglob("*.js"):
            to_crlf(path)
        self.generate("--out", "docs/b.md")
        self.assertEqual((self.repo / "docs" / "a.md").read_bytes(), (self.repo / "docs" / "b.md").read_bytes())

    def test_writes_default_out_and_prints_its_path(self) -> None:
        (self.repo / "docs" / "05-code-by-component.md").unlink()
        code, out, err = self.generate()
        self.assertEqual((code, err), (0, ""))
        expected = self.repo / "docs" / "05-code-by-component.md"
        self.assertTrue(expected.is_file())
        self.assertEqual(Path(out.strip()).resolve(), expected.resolve())

    def test_custom_out_creates_missing_folders(self) -> None:
        code, out, _ = self.generate("--out", "site/pages/code.md")
        self.assertEqual(code, 0)
        self.assertEqual(Path(out.strip()).resolve(), (self.repo / "site" / "pages" / "code.md").resolve())

    def test_component_without_files_for_a_language_is_skipped_and_first_shown_is_open(self) -> None:
        data = self.config()
        data["components"][0]["files"] = {"javascript": ["strategy.js"]}
        alt = self.write_config(data)
        self.assertEqual(run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")[0], 0)
        first_section = self.read("docs/page.md").split("## 2.")[0]
        self.assertEqual(first_section.count("<details"), 1)
        self.assertIn("<details open>\n<summary><b>JavaScript (ES2026)</b>", first_section)
        self.assertNotIn("Python 3", first_section)

    def test_language_order_follows_the_config(self) -> None:
        data = self.config()
        data["languages"].reverse()
        alt = self.write_config(data)
        run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")
        self.assertEqual(re.findall(r"<details( open)?>\n<summary><b>([^<]+)</b>", self.read("docs/page.md"))[:2],
                         [(" open", "JavaScript (ES2026)"), ("", "Python 3")])

    def test_summary_text_is_html_escaped(self) -> None:
        data = self.config()
        data["languages"][0]["label"] = "R&D <py>"
        alt = self.write_config(data)
        run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")
        self.assertIn("<summary><b>R&amp;D &lt;py&gt;</b>", self.read("docs/page.md"))

    def test_nested_paths_dir_variants_and_optional_intro(self) -> None:
        self.write("python/src/sub/mod.py", "VALUE = 1\n")
        self.write("top.py", "TOP = 1\n")
        data = self.config()
        data.pop("intro")
        data["languages"][0]["dir"] = "python/src/"  # trailing slash
        data["languages"].append({"key": "root", "label": "Root", "fence": "python", "dir": "."})
        data["components"][0]["files"] = {"python": ["sub/mod.py", "./strategy.py"], "root": ["top.py"]}
        alt = self.write_config(data)
        code, _, err = run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")
        self.assertEqual((code, err), (0, ""))
        text = self.read("docs/page.md")
        self.assertTrue(text.startswith("# Code by component - Python and JavaScript\n\n1. [Strategy interface]"))
        self.assertIn("<code>sub/mod.py, ./strategy.py</code>", text)
        self.assertEqual(re.findall(r"<!-- source: (\S+) -->", text)[:3],
                         ["python/src/sub/mod.py", "python/src/strategy.py", "top.py"])
        self.assertEqual(self.check_only("docs/page.md")[:2], (0, "ok\n"))


    def test_titles_are_plain_text_escaped_for_markdown_and_role_stays_markdown(self) -> None:
        self.write("python/src/a&b.py", "V = 1\n")
        data = self.config()
        data["title"] = "Comparator<T> & `x`"
        data["components"][0]["title"] = "Comparator<T> [x](y) & `z`_*"
        data["components"][0]["role"] = "Role with `code` and **bold**."
        data["components"][0]["files"]["python"].append("a&b.py")
        alt = self.write_config(data)
        self.assertEqual(run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")[0], 0)
        text = self.read("docs/page.md")
        lines = text.split("\n")
        self.assertEqual(lines[0], "# Comparator\\<T\\> \\& \\`x\\`")
        self.assertIn("1. [Comparator\\<T\\> \\[x\\](y) \\& \\`z\\`\\_\\*](#1-comparatort-xy--z_)\n", text)
        self.assertIn("## 1. Comparator\\<T\\> \\[x\\](y) \\& \\`z\\`\\_\\*\n\nRole with `code` and **bold**.\n", text)
        self.assertIn("<code>strategy.py, a&amp;b.py</code>", text)
        self.assertEqual(self.check_only("docs/page.md")[:2], (0, "ok\n"))  # escaped TOC text is not a link

    def test_backslash_paths_are_normalised_in_markers_and_summaries(self) -> None:
        self.write("python/src/sub/mod.py", "V = 1\n")
        data = self.config()
        data["components"][0]["files"]["python"] = ["sub\\mod.py"]
        alt = self.write_config(data)
        self.assertEqual(run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")[0], 0)
        text = self.read("docs/page.md")
        self.assertIn("<code>sub/mod.py</code>", text)
        self.assertIn("<!-- source: python/src/sub/mod.py -->", text)
        self.assertNotIn("\\", text.split("## 2.")[0])
        self.assertEqual(self.check_only("docs/page.md")[:2], (0, "ok\n"))

    def test_intro_is_stripped_of_surrounding_blank_space(self) -> None:
        data = self.config()
        data["intro"] = "\n\n  Intro text.  \n\n"
        alt = self.write_config(data)
        run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")
        lines = self.read("docs/page.md").split("\n")
        self.assertEqual(lines[2:4], ["Intro text.", ""])
        self.assertTrue(lines[4].startswith("1. ["))

    def test_page_is_written_with_write_bytes_never_write_text(self) -> None:
        original = gen.Path.write_bytes
        with mock.patch.object(gen.Path, "write_text",
                               side_effect=AssertionError("write_text translates newlines on Windows")):
            with mock.patch.object(gen.Path, "write_bytes", autospec=True, side_effect=original) as spy:
                self.assertEqual(self.generate("--out", "docs/page.md")[0], 0)
        self.assertEqual(spy.call_count, 1)
        written = spy.call_args[0][1]
        self.assertIsInstance(written, bytes)
        self.assertNotIn(b"\r", written)

    def test_regenerate_hint_uses_native_quoting(self) -> None:
        parts = ["python", "gen.py", "--config", "my dir/c.json", "--root", "."]
        self.assertEqual(gen.quote_command(parts, windows=False), "python gen.py --config 'my dir/c.json' --root .")
        self.assertEqual(gen.quote_command(parts, windows=True), 'python gen.py --config "my dir/c.json" --root .')
        self.assertIn(gen.quote_command(parts), (gen.quote_command(parts, True), gen.quote_command(parts, False)))


class GeneratorCheckModeTests(RepoCase):
    def test_check_exit_codes_both_ways(self) -> None:
        page = self.repo / "docs" / "05-code-by-component.md"
        self.assertEqual(self.generate("--check")[0], 0)  # committed golden page is current
        page.unlink()
        code, out, err = self.generate("--check")
        self.assertEqual((code, out), (1, ""))
        self.assertFalse(page.exists())  # --check never writes
        self.assertIn("docs/05-code-by-component.md is stale or missing", err)
        self.assertIn("gen_code_by_component.py", err)
        self.assertIn("--config", err)
        self.assertEqual(self.generate()[0], 0)
        self.assertEqual(self.generate("--check")[0], 0)

    def test_check_detects_source_config_and_page_edits(self) -> None:
        self.append("javascript/src/demo.js", "// changed\n")
        self.assertEqual(self.generate("--check")[0], 1)
        self.generate()
        self.assertEqual(self.generate("--check")[0], 0)
        self.append("docs/05-code-by-component.md", "\nhand edit\n")
        self.assertEqual(self.generate("--check")[0], 1)
        self.generate()
        data = self.config()
        data["components"][1]["role"] = "A different sentence."
        self.write("components.json", json.dumps(data))
        self.assertEqual(self.generate("--check")[0], 1)

    def test_check_tolerates_crlf_checkouts_of_the_page(self) -> None:
        to_crlf(self.repo / "docs" / "05-code-by-component.md")
        self.assertEqual(self.generate("--check")[0], 0)

    def test_check_honours_out(self) -> None:
        self.assertEqual(self.generate("--check", "--out", "docs/other.md")[0], 1)
        self.generate("--out", "docs/other.md")
        self.assertEqual(self.generate("--check", "--out", "docs/other.md")[0], 0)

    def test_check_with_invalid_config_is_a_usage_error_not_stale(self) -> None:
        self.write("components.json", "{}")
        self.assertEqual(self.generate("--check")[0], 2)


class GeneratorConfigValidationTests(RepoCase):
    def expect_error(self, mutate, fragment: str, *, check: bool = False) -> None:
        data = self.config()
        mutate(data)
        alt = self.write_config(data)
        out_page = self.repo / "docs" / "must-not-exist.md"
        argv = ["--config", str(alt), "--root", str(self.repo), "--out", "docs/must-not-exist.md"]
        code, out, err = run(gen, *argv, *(["--check"] if check else []))
        self.assertEqual(code, 2, err)
        self.assertEqual(out, "")
        self.assertIn(fragment, err)
        self.assertTrue(err.startswith("error: "), err)
        self.assertFalse(out_page.exists())

    def test_unknown_language_key_in_files(self) -> None:
        self.expect_error(lambda d: d["components"][0]["files"].update({"rust": ["a.rs"]}), "unknown language key 'rust'")

    def test_missing_source_file(self) -> None:
        self.expect_error(lambda d: d["components"][0]["files"]["python"].append("nope.py"),
                          "missing file: python/src/nope.py")

    def test_empty_components(self) -> None:
        self.expect_error(lambda d: d.update(components=[]), "config.components must be a non-empty list")

    def test_component_with_no_files(self) -> None:
        self.expect_error(lambda d: d["components"][1].update(files={}), "lists no files in any language")
        self.expect_error(lambda d: d["components"][1].update(files={"python": [], "javascript": []}),
                          "lists no files in any language")

    def test_languages_must_be_a_non_empty_list_with_unique_keys(self) -> None:
        self.expect_error(lambda d: d.update(languages=[]), "config.languages must be a non-empty list")
        self.expect_error(lambda d: d["languages"].append(dict(d["languages"][0])), "duplicate language key")

    def test_unknown_and_missing_keys(self) -> None:
        self.expect_error(lambda d: d.update(colour="red"), "unknown key(s) colour")
        self.expect_error(lambda d: d["languages"][0].update(extra=1), "config.languages[0]: unknown key(s) extra")
        self.expect_error(lambda d: d["components"][0].update(extra=1), "config.components[0]: unknown key(s) extra")
        self.expect_error(lambda d: d.pop("title"), "missing key(s) title")
        self.expect_error(lambda d: d["languages"][1].pop("fence"), "config.languages[1]: missing key(s) fence")
        self.expect_error(lambda d: d["components"][0].pop("role"), "config.components[0]: missing key(s) role")

    def test_wrong_types(self) -> None:
        self.expect_error(lambda d: d.update(title=""), "config.title must be a non-empty string")
        self.expect_error(lambda d: d.update(title=5), "config.title")
        self.expect_error(lambda d: d.update(intro=["x"]), "config.intro must be a string")
        self.expect_error(lambda d: d["components"][0].update(files=["a.py"]), "files must be an object")
        self.expect_error(lambda d: d["components"][0]["files"].update(python="strategy.py"),
                          "files.python must be a list")
        self.expect_error(lambda d: d["components"][0]["files"].update(python=[3]), "files.python[0]")

    def test_paths_must_stay_inside_the_repo(self) -> None:
        self.expect_error(lambda d: d["components"][0]["files"]["python"].append("../../../outside.py"),
                          "path leaves the repository")
        self.expect_error(lambda d: d["components"][0]["files"]["python"].append("/etc/passwd"),
                          "must be relative to the language dir")
        self.expect_error(lambda d: d["components"][0]["files"]["python"].append("C:\\x.py"),
                          "must be relative to the language dir")
        self.expect_error(lambda d: d["languages"][0].update(dir="../elsewhere"), "path leaves the repository")

    def test_invalid_json_duplicate_keys_and_non_object(self) -> None:
        for text, fragment in (("{", "not valid JSON"), ('{"title": "a", "title": "b"}', "duplicate key"),
                               ("[]", "config must be an object"), ("", "not valid JSON")):
            with self.subTest(text=text):
                self.write("bad.json", text)
                code, _, err = run(gen, "--config", str(self.repo / "bad.json"), "--root", str(self.repo))
                self.assertEqual(code, 2)
                self.assertIn(fragment, err)

    def test_usage_errors(self) -> None:
        config = str(self.repo / "components.json")
        cases = {
            "missing config file": ["--config", str(self.repo / "nope.json"), "--root", str(self.repo)],
            "missing root": ["--config", config, "--root", str(self.tmp / "nope")],
            "out outside root": ["--config", config, "--root", str(self.repo), "--out", "../page.md"],
            "no arguments": [],
            "unknown option": ["--config", config, "--root", str(self.repo), "--nope"],
        }
        for label, argv in cases.items():
            with self.subTest(label):
                code, out, err = run(gen, *argv)
                self.assertEqual((code, out), (2, ""))
                self.assertTrue(err.strip())
        self.assertFalse((self.tmp / "page.md").exists())

    def test_config_with_utf8_bom_is_accepted(self) -> None:
        path = self.repo / "components.json"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        self.assertEqual(self.generate("--check")[0], 0)

    def test_source_that_is_not_utf8_is_a_config_error(self) -> None:
        (self.repo / "javascript" / "src" / "demo.js").write_bytes(b"\xff\xfe\x00")
        code, _, err = self.generate("--out", "docs/page.md")
        self.assertEqual(code, 2)
        self.assertIn("as UTF-8", err)


    def test_drive_letter_unc_and_absolute_dirs_and_names_are_rejected(self) -> None:
        for directory in ("C:/x", "C:\\x", "C:x", "//server/share", "\\\\server\\share", "/abs"):
            with self.subTest(dir=directory):
                self.expect_error(lambda d, v=directory: d["languages"][0].update(dir=v),
                                  "must be relative to the repository root")
        for name in ("C:x.py", "C:\\x.py", "\\\\server\\x.py", "/x.py"):
            with self.subTest(name=name):
                self.expect_error(lambda d, v=name: d["components"][0]["files"]["python"].append(v),
                                  "must be relative to the language dir")

    def test_backslash_traversal_is_rejected(self) -> None:
        self.expect_error(lambda d: d["components"][0]["files"]["python"].append("..\\..\\..\\outside.py"),
                          "path leaves the repository")
        self.expect_error(lambda d: d["languages"][0].update(dir="..\\elsewhere"), "path leaves the repository")

    def test_symlinked_source_leading_outside_the_repo_is_rejected(self) -> None:
        secret = self.tmp / "secret.py"
        secret.write_text("TOP SECRET OUTSIDE\n", encoding="utf-8")
        self.symlink(self.repo / "python" / "src" / "leak.py", secret)
        self.expect_error(lambda d: d["components"][0]["files"]["python"].append("leak.py"),
                          "resolves outside the repository")

    def test_out_through_a_symlinked_folder_is_rejected(self) -> None:
        outside = self.tmp / "outside-dir"
        outside.mkdir()
        self.symlink(self.repo / "linked", outside)
        code, out, err = self.generate("--out", "linked/page.md")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("--out must stay inside the root", err)
        self.assertEqual(list(outside.iterdir()), [])

    def test_fence_must_be_a_safe_info_string(self) -> None:
        for bad in ("java\nINJECT", "java\n", "py thon", "c`", "", " ", "a|b", "x\ty", "<b>"):
            with self.subTest(fence=bad):
                self.expect_error(lambda d, v=bad: d["languages"][0].update(fence=v), "fence")
        for good in ("c++", "c#", "objective-c", "text.v2", "py_3"):
            with self.subTest(fence=good):
                data = self.config()
                data["languages"][0]["fence"] = good
                alt = self.write_config(data)
                code, _, err = run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")
                self.assertEqual((code, err), (0, ""))
                self.assertIn(f"```{good}\n", self.read("docs/page.md"))

    def test_single_line_fields_reject_newlines_and_control_characters(self) -> None:
        mutations = [
            lambda d: d.update(title="a\nb"),
            lambda d: d["languages"][0].update(label="a\nb"),
            lambda d: d["languages"][0].update(key="a\nb"),
            lambda d: d["languages"][0].update(dir="a\nb"),
            lambda d: d["components"][0].update(title="a\r\nb"),
            lambda d: d["components"][0].update(role="a\nb"),
            lambda d: d["components"][0].update(role="a\x00b"),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(i=i):
                self.expect_error(mutate, "single line")

    def test_file_names_cannot_break_the_source_comment(self) -> None:
        for name in ("a-->b.py", "a\tb.py", "a\nb.py", "a\x00b.py"):
            with self.subTest(name=name):
                self.expect_error(lambda d, v=name: d["components"][0]["files"]["python"].append(v),
                                  "control characters or '-->'")


class GeneratorWithCheckDocsTests(RepoCase):
    def test_generated_pages_pass_check_docs(self) -> None:
        self.assertEqual(self.generate()[0], 0)
        self.assertEqual(self.check()[:2], (0, "ok\n"))

    def test_round_trip_for_awkward_sources(self) -> None:
        awkward = {
            "python/src/blank_tail.py": "x = 1\n\n\n",
            "python/src/empty.py": "",
            "python/src/only_newline.py": "\n",
            "python/src/no_newline.py": "y = 2",
            "python/src/unicode.py": "# caf\u00e9 \u2192 \u65e5\u672c\n",
            "python/src/tabs.py": "if x:\n\treturn 1  \n",
            "python/src/backticks.py": "'''\n````\n```\n'''\n",
            "python/src/fence_only.py": "```\n",
            "python/src/html.py": "</details>\n<summary>x</summary>\n",
        }
        for rel, text in awkward.items():
            self.write(rel, text)
        data = self.config()
        data["components"][0]["files"]["python"] = [Path(rel).name for rel in awkward]
        alt = self.write_config(data)
        self.assertEqual(run(gen, "--config", str(alt), "--root", str(self.repo), "--out", "docs/page.md")[0], 0)
        self.assertEqual(self.check_only("docs/page.md")[:2], (0, "ok\n"))
        # the same page is stale once any of those files changes
        self.append("python/src/tabs.py", "z\n")
        self.assertEqual(self.check_only("docs/page.md")[0], 1)

    def test_check_docs_catches_hand_edited_generated_page(self) -> None:
        self.generate()
        page = self.repo / "docs" / "05-code-by-component.md"
        page.write_text(page.read_text(encoding="utf-8").replace("print(\"hello\")", "print(\"bye\")"), encoding="utf-8")
        code, lines = self.issues()
        self.assertEqual(code, 1)
        self.assertEqual(len(lines), 1)
        self.assertIn("code block differs from source file -> python/src/demo.py", lines[0])

    def test_example_config_is_valid_generic_and_produces_a_clean_page(self) -> None:
        data = json.loads(EXAMPLE_CONFIG.read_text(encoding="utf-8"))
        self.assertEqual([language["key"] for language in data["languages"]],
                         ["java", "python", "javascript", "typescript"])
        self.assertEqual(len(data["components"]), 5)
        repo = self.tmp / "example-repo"
        languages = {language["key"]: language for language in data["languages"]}
        for component in data["components"]:
            for key, names in component["files"].items():
                for name in names:
                    self.write(f"{languages[key]['dir']}/{name}", f"// {key}: {name}\n", root=repo)
        for key in languages:  # the intro links to each language README
            self.write(f"{key}/README.md", f"# {key}\n", root=repo)
        code, _, err = run(gen, "--config", str(EXAMPLE_CONFIG), "--root", str(repo))
        self.assertEqual((code, err), (0, ""))
        page = (repo / "docs" / "05-code-by-component.md").read_text(encoding="utf-8")
        self.assertEqual(page.count("<details open>"), 5)
        self.assertEqual(page.count("<details>"), 15)
        self.assertEqual(run(gen, "--config", str(EXAMPLE_CONFIG), "--root", str(repo), "--check")[0], 0)
        self.assertEqual(run(check_docs, "--root", str(repo))[:2], (0, "ok\n"))
        raw = EXAMPLE_CONFIG.read_text(encoding="utf-8").lower()
        for private in ("github.com", "@", "io.github", "http"):
            self.assertNotIn(private, raw)


class ScriptEntryPointTests(RepoCase):
    def test_check_docs_runs_as_a_program(self) -> None:
        self.assertEqual(self.program(CHECK_SCRIPT, "--root", str(self.repo)), (0, "ok\n", ""))
        self.append("README.md", "\n[x](nope.md)\n")
        code, out, _ = self.program(CHECK_SCRIPT, "--root", str(self.repo))
        self.assertEqual(code, 1)
        self.assertIn("README.md: line", out)
        self.assertEqual(self.program(CHECK_SCRIPT, "--root", str(self.tmp / "nope"))[0], 2)

    def test_generator_runs_as_a_program(self) -> None:
        config = str(self.repo / "components.json")
        code, _, err = self.program(GEN_SCRIPT, "--config", config, "--root", str(self.repo), "--check")
        self.assertEqual(code, 0, err)
        self.append("python/src/demo.py", "# x\n")
        code, _, err = self.program(GEN_SCRIPT, "--config", config, "--root", str(self.repo), "--check")
        self.assertEqual(code, 1)
        self.assertIn("regenerate", err)
        self.assertEqual(self.program(GEN_SCRIPT, "--config", str(self.tmp / "nope.json"),
                                      "--root", str(self.repo))[0], 2)


if __name__ == "__main__":
    unittest.main()
