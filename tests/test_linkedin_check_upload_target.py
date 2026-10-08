from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "linkedin-publishing" / "scripts" / "check_upload_target.py"
REFERENCES = ROOT / "skills" / "linkedin-publishing" / "references"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "linkedin-publishing"
SPEC = importlib.util.spec_from_file_location("check_upload_target", SCRIPT)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)

RECIPE_FIXTURES = ("recipe-proxy-create", "recipe-proxy-check", "recipe-drop", "recipe-proxy-remove")


def run_main(*argv: str) -> "tuple[int, str, str]":
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = guard.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def fixture(name: str) -> Path:
    return FIXTURES / (name + ".js.txt")


def violations(text: str) -> "list[str]":
    return [v.message for v in guard.check_text(text)]


def js_blocks(markdown_path: Path) -> "list[str]":
    text = markdown_path.read_text(encoding="utf-8")
    return [textwrap.dedent(b) for b in re.findall(r"```js\n(.*?)```", text, re.S)]


class OriginalMistakeTests(unittest.TestCase):
    def test_forwarding_to_the_messaging_input_fails(self) -> None:
        code, out, _ = run_main(str(fixture("mistaken-attachment-input")))
        self.assertEqual(code, 1)
        self.assertIn("violation:", out)
        self.assertIn("attachment-input", out)
        self.assertIn("forwards files to 'target'", out)
        self.assertNotIn("ok:", out)

    def test_document_wide_file_input_query_fails(self) -> None:
        code, out, _ = run_main(str(fixture("mistaken-document-wide-file-input")))
        self.assertEqual(code, 1)
        self.assertIn("document-wide file-input query on 'document'", out)
        self.assertIn("forwards files to 'first'", out)

    def test_selector_held_in_a_variable_fails(self) -> None:
        code, out, _ = run_main(str(fixture("mistaken-selector-in-variable")))
        self.assertEqual(code, 1)
        self.assertIn("file-input selector outside a scoped query", out)

    def test_forwarding_to_any_preexisting_input_fails(self) -> None:
        code, out, _ = run_main(str(fixture("forward-to-preexisting-input")))
        self.assertEqual(code, 1)
        self.assertIn("forwards files to 'existing', not to the proxy input 'tmp-upload-proxy'", out)
        self.assertEqual(out.count("violation:"), 1)


class HardeningTests(unittest.TestCase):
    """Other spellings of 'forward the file to some element' must fail like `X.files = ...`."""

    def test_other_spellings_of_files_assignment_fail(self) -> None:
        for name in ("bypass-bracket-files", "bypass-object-assign", "bypass-newline-dot-files",
                     "bypass-descriptor-set", "bypass-decoy-declaration"):
            with self.subTest(name=name):
                code, out, _ = run_main(str(fixture(name)))
                self.assertEqual(code, 1, out)
                self.assertIn("forwards files to 'target'", out)

    def test_every_spelling_is_allowed_on_the_proxy(self) -> None:
        for name in ("proxy-forward-all-spellings", "proxy-declared-over-two-lines"):
            with self.subTest(name=name):
                code, out, _ = run_main(str(fixture(name)))
                self.assertEqual(code, 0, out)

    def test_unrecognised_use_of_quoted_files_fails_closed(self) -> None:
        found = violations("const f = target['files']")
        self.assertEqual(len(found), 1)
        self.assertIn("unrecognised use of the quoted name 'files'", found[0])
        self.assertEqual(len(violations("setIt(target, 'files', dt.files)")), 1)

    def test_reflect_set_and_quoted_object_assign_key(self) -> None:
        self.assertEqual(len(violations("Reflect.set(t, 'files', dt.files)")), 1)
        self.assertEqual(len(violations("Object.assign(t, { 'files': dt.files })")), 1)
        self.assertEqual(len(violations("Object.assign(t, { files })")), 1)
        self.assertEqual(violations("Object.assign(document.getElementById('tmp-upload-proxy'), { files: dt.files })"), [])

    def test_receivers_that_are_call_or_index_expressions(self) -> None:
        self.assertEqual(len(violations("document.querySelector('.x').files = dt.files")), 1)
        self.assertEqual(len(violations("inputs[0]\n  .files = dt.files")), 1)
        self.assertEqual(len(violations("(a || b).files = dt.files")), 1)
        self.assertEqual(violations("const dt = 1\ntarget.files == null"), [])

    def test_declaration_must_assign_the_proxy_to_that_very_name(self) -> None:
        self.assertEqual(len(violations("const t = x, p = 'tmp-upload-proxy'; t.files = f")), 1)
        self.assertEqual(violations("const t = x, p = document.getElementById('tmp-upload-proxy'); p.files = f"), [])
        self.assertEqual(len(violations("let p = other;\nconst note = 'tmp-upload-proxy';\np.files = f")), 1)
        self.assertEqual(violations("let p;\np = document.getElementById('tmp-upload-proxy');\np.files = f"), [])
        self.assertEqual(violations("const p = document\n  .getElementById('tmp-upload-proxy');\np.files = f"), [])


class RecipeSnippetTests(unittest.TestCase):
    def test_recipe_snippets_pass(self) -> None:
        for name in RECIPE_FIXTURES:
            with self.subTest(name=name):
                code, out, err = run_main(str(fixture(name)))
                self.assertEqual((code, err), (0, ""), out)
                self.assertTrue(out.startswith("ok:"))

    def test_recipe_fixtures_are_the_blocks_in_the_recipe(self) -> None:
        blocks = [b.strip() for b in js_blocks(REFERENCES / "image-attach-recipe.md")]
        for name in RECIPE_FIXTURES:
            with self.subTest(name=name):
                self.assertIn(fixture(name).read_text(encoding="utf-8").strip(), blocks)

    def test_every_js_block_in_the_references_passes(self) -> None:
        for reference in ("image-attach-recipe.md", "composer-automation.md"):
            blocks = js_blocks(REFERENCES / reference)
            self.assertTrue(blocks, reference)
            for i, block in enumerate(blocks):
                with self.subTest(reference=reference, block=i):
                    self.assertEqual(violations(block), [])

    def test_forwarding_to_the_proxy_is_allowed(self) -> None:
        self.assertEqual(violations(fixture("forward-to-proxy").read_text(encoding="utf-8")), [])

    def test_query_scoped_to_a_dialog_is_allowed(self) -> None:
        self.assertEqual(violations(fixture("scoped-file-input-query").read_text(encoding="utf-8")), [])


class RuleTests(unittest.TestCase):
    def test_attachment_input_is_reported_with_its_line_number_in_any_case(self) -> None:
        found = guard.check_text("const a = 1;\n// see ATTACHMENT-INPUT-1\n")
        self.assertEqual([v.line for v in found], [2])

    def test_selector_quote_styles_on_document_are_all_reported(self) -> None:
        for selector in ("input[type=file]", 'input[type="file"]', "input[type='file']", "[type=file]", "input[ type = file ]"):
            for wrapper in ("document.querySelector(%s)", "document.querySelectorAll(%s)", "deep(document, %s)",
                            "document.body.querySelector(%s)", "window.document.querySelector(%s)"):
                for quote in ("'", '"', "`"):
                    inner = selector.replace(quote, "\\" + quote) if quote in selector else selector
                    snippet = wrapper % (quote + inner + quote)
                    with self.subTest(snippet=snippet):
                        self.assertEqual(len(violations(snippet)), 1, snippet)

    def test_other_selectors_on_document_are_fine(self) -> None:
        self.assertEqual(violations("document.querySelector('.ql-editor')"), [])
        self.assertEqual(violations("deep(document, 'a')"), [])
        self.assertEqual(violations("input.type = 'file'"), [])

    def test_scoped_receivers_are_allowed_for_file_selectors(self) -> None:
        self.assertEqual(violations("dialog.querySelector('input[type=file]')"), [])
        self.assertEqual(violations("deep(dialogRoot, 'input[type=\"file\"]')"), [])

    def test_files_assignment_to_proxy_forms(self) -> None:
        ok = [
            "document.getElementById('tmp-upload-proxy').files = dt.files",
            "const p = document.getElementById('tmp-upload-proxy'); p.files = dt.files",
            "const p = document.querySelector('#tmp-upload-proxy')\np.files = dt.files",
            "const i = document.createElement('input'); i.id = 'tmp-upload-proxy'; i.files = dt.files",
            "const i = document.createElement('input'); i.setAttribute('id', 'tmp-upload-proxy'); i.files = dt.files",
            "Object.defineProperty(document.getElementById('tmp-upload-proxy'), 'files', { value: dt.files })",
        ]
        for snippet in ok:
            with self.subTest(snippet=snippet):
                self.assertEqual(violations(snippet), [])

    def test_files_assignment_to_other_elements_fails(self) -> None:
        bad = [
            "el.files = dt.files",
            "document.getElementById('image-upload').files = dt.files",
            "const t = composerEditor; t.files = dt.files",
            "Object.defineProperty(input, 'files', { value: dt.files })",
            "const x = document.getElementById('tmp-upload-proxy'); y.files = dt.files",
            "inputs[0].files = dt.files",
        ]
        for snippet in bad:
            with self.subTest(snippet=snippet):
                self.assertEqual(len(violations(snippet)), 1, snippet)

    def test_comparison_and_reads_of_files_are_not_forwarding(self) -> None:
        self.assertEqual(violations("if (el.files == null) {}"), [])
        self.assertEqual(violations("const f = el.files[0]"), [])
        self.assertEqual(violations("const g = (x) => x.files"), [])


class CliTests(unittest.TestCase):
    def test_no_arguments_is_a_usage_error(self) -> None:
        code, _, err = run_main()
        self.assertEqual(code, 2)
        self.assertIn("usage", err.lower())

    def test_help_exits_zero(self) -> None:
        code, out, _ = run_main("--help")
        self.assertEqual(code, 0)
        self.assertIn("SNIPPET_FILE", out)

    def test_missing_file_is_an_io_error(self) -> None:
        code, _, err = run_main(str(FIXTURES / "does-not-exist.js.txt"))
        self.assertEqual(code, 2)
        self.assertIn("error:", err)

    def test_empty_and_undecodable_files_are_io_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.js.txt"
            empty.write_text("  \n", encoding="utf-8")
            self.assertEqual(run_main(str(empty))[0], 2)
            binary = Path(tmp) / "binary.js.txt"
            binary.write_bytes(b"\xff\xfe\x00\x80")
            self.assertEqual(run_main(str(binary))[0], 2)

    def test_worst_status_wins_across_several_files(self) -> None:
        code, out, _ = run_main(str(fixture("recipe-drop")), str(fixture("mistaken-attachment-input")))
        self.assertEqual(code, 1)
        self.assertIn("ok:", out)
        self.assertIn("violation:", out)

    def test_output_is_ascii_even_for_non_ascii_snippets(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "caf\u00e9.js.txt"
            path.write_text("caf\u00e9.files = dt.files // \u2019\n", encoding="utf-8")
            code, out, _ = run_main(str(path))
        self.assertEqual(code, 1)
        out.encode("ascii")


if __name__ == "__main__":
    unittest.main()
