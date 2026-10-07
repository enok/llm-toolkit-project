from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "medium-publishing" / "scripts" / "medium_paste_html.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "medium-publishing"
SPEC = importlib.util.spec_from_file_location("medium_paste_html", SCRIPT)
assert SPEC and SPEC.loader
paste = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = paste
SPEC.loader.exec_module(paste)

SHA40 = "0123456789abcdef0123456789abcdef01234567"
RAW = "https://raw.githubusercontent.com/example-owner/example-repo"


def run_main(*argv: str) -> "tuple[int, str, str]":
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = paste.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def built(text: str) -> str:
    return paste.build_html(text)[0]


def codes(text: str, prefixes: "tuple[str, ...]" = ()) -> "list[str]":
    return [issue.code for issue in paste.check_html(text, prefixes)]


class BuildLanguageTests(unittest.TestCase):
    def test_label_sets_explicit_language(self) -> None:
        out = built("<p><strong>src/Duck.java</strong></p>\n<pre>x</pre>")
        self.assertIn('<pre data-code-block-mode="2" data-code-block-lang="java">x</pre>', out)

    def test_extension_map(self) -> None:
        expected = {
            "a.java": "java",
            "a.py": "python",
            "a.js": "javascript",
            "a.ts": "typescript",
            "a.kt": "kotlin",
            "a.go": "go",
            "a.rs": "rust",
            "a.cs": "csharp",
            "a.rb": "ruby",
            "a.sh": "bash",
            "a.sql": "sql",
            "a.json": "json",
            "a.yaml": "yaml",
            "a.yml": "yaml",
            "a.xml": "xml",
            "a.html": "html",
            "a.css": "css",
            "A.JAVA": "java",
        }
        for label, lang in expected.items():
            with self.subTest(label=label):
                out = built("<p><strong>%s</strong></p><pre>x</pre>" % label)
                self.assertIn('data-code-block-mode="2" data-code-block-lang="%s"' % lang, out)

    def test_label_with_trailing_colon_and_br(self) -> None:
        self.assertIn('lang="python"', built("<p><strong>a.py:</strong></p><pre>x</pre>"))
        self.assertIn('lang="python"', built("<strong>a.py</strong><br>\n<pre>x</pre>"))

    def test_class_on_pre_and_on_code(self) -> None:
        self.assertIn('lang="python"', built('<pre class="highlight language-python">x</pre>'))
        self.assertIn('lang="typescript"', built('<pre><code class="language-ts">x</code></pre>'))
        self.assertIn('lang="bash"', built('<pre class="lang-shell">x</pre>'))

    def test_class_wins_over_label(self) -> None:
        out = built('<p><strong>a.java</strong></p><pre class="language-python">x</pre>')
        self.assertIn('lang="python"', out)
        self.assertNotIn('lang="java"', out)

    def test_pre_class_wins_over_code_class(self) -> None:
        out = built('<pre class="language-python"><code class="language-java">x</code></pre>')
        self.assertEqual(out, '<pre data-code-block-mode="2" data-code-block-lang="python">x</pre>')

    def test_language_aliases(self) -> None:
        expected = {"python3": "python", "node": "javascript", "nodejs": "javascript", "golang": "go",
                    "c#": "csharp", "shell": "bash", "zsh": "bash", "PY": "python", "yml": "yaml"}
        for name, lang in expected.items():
            with self.subTest(name=name):
                self.assertIn('lang="%s"' % lang, built('<pre class="language-%s">x</pre>' % name))

    def test_parse_attrs_unescapes_and_handles_quote_styles(self) -> None:
        attrs = paste.parse_attrs("""src="a&amp;b" ALT='x y' data-n=3 hidden""")
        self.assertEqual(attrs, {"src": "a&b", "alt": "x y", "data-n": "3", "hidden": ""})

    def test_unknown_class_falls_back_to_label_then_plain(self) -> None:
        with_label = built('<p><strong>a.go</strong></p><pre class="language-text">x</pre>')
        self.assertIn('lang="go"', with_label)
        self.assertEqual(built('<pre class="language-text">x</pre>'), '<pre data-code-block-mode="0">x</pre>')

    def test_unknown_or_missing_language_is_plain_mode_zero(self) -> None:
        plain = '<pre data-code-block-mode="0">x</pre>'
        self.assertEqual(built("<p><strong>notes.txt</strong></p><pre>x</pre>"), "<p><strong>notes.txt</strong></p>" + plain)
        self.assertEqual(built("<pre>x</pre>"), plain)
        self.assertEqual(built("<p><strong>Makefile</strong></p><pre>x</pre>"), "<p><strong>Makefile</strong></p>" + plain)

    def test_label_does_not_leak_to_next_block(self) -> None:
        out = built("<p><strong>a.java</strong></p><pre>1</pre><pre>2</pre>")
        self.assertIn('lang="java">1</pre>', out)
        self.assertIn('<pre data-code-block-mode="0">2</pre>', out)

    def test_label_must_be_adjacent(self) -> None:
        out = built("<p><strong>a.java</strong></p><p>text between</p><pre>x</pre>")
        self.assertIn('<pre data-code-block-mode="0">x</pre>', out)

    def test_existing_attrs_are_replaced_and_rebuild_is_stable(self) -> None:
        once = built('<p><strong>a.py</strong></p><pre class="x" id="y">a\n\nb</pre>')
        self.assertNotIn('class="x"', once)
        self.assertEqual(built(once), once)
        keep = '<pre data-code-block-mode="2" data-code-block-lang="rust">x</pre>'
        self.assertEqual(built(keep), keep)

    def test_code_wrapper_is_unwrapped_only_when_sole_element(self) -> None:
        self.assertEqual(built("<pre><code>a &lt; b</code></pre>"), '<pre data-code-block-mode="0">a &lt; b</pre>')
        multi = "<pre><code>a</code> and <code>b</code></pre>"
        self.assertIn("<code>a</code> and <code>b</code>", built(multi))

    def test_languages_returned_per_block(self) -> None:
        _, langs = paste.build_html("<p><strong>a.py</strong></p><pre>1</pre><pre>2</pre>")
        self.assertEqual(langs, ["python", None])


class BuildBodyTests(unittest.TestCase):
    def test_blank_lines_get_single_space(self) -> None:
        out = built("<pre>a\n\nb\n\n\nc</pre>")
        self.assertIn(">a\n \nb\n \n \nc</pre>", out)

    def test_leading_and_trailing_newline_are_not_padded(self) -> None:
        out = built("<pre>\nfoo\n</pre>")
        self.assertIn(">\nfoo\n</pre>", out)
        out = built("<pre>foo\n\n</pre>")
        self.assertIn(">foo\n \n</pre>", out)

    def test_indented_whitespace_only_lines_are_kept(self) -> None:
        out = built("<pre>a\n    \nb</pre>")
        self.assertIn(">a\n    \nb</pre>", out)

    def test_blank_lines_outside_pre_are_untouched(self) -> None:
        text = "<p>one</p>\n\n\n<p>two</p>\n"
        self.assertEqual(built(text), text)

    def test_non_ascii_is_entity_encoded_everywhere(self) -> None:
        out = built("<p>It’s café \U0001F600</p><pre>✓ ok</pre><img alt=\"é\" src=\"https://example.com/a.png\">")
        self.assertEqual(out, out.encode("ascii").decode("ascii"))
        for entity in ("&#8217;", "&#233;", "&#128512;", "&#10003;"):
            self.assertIn(entity, out)

    def test_everything_else_is_preserved(self) -> None:
        text = (
            '<h1>T &amp; U</h1>\n<p>a <em>b</em> <a href="https://example.com/x?a=1&amp;b=2">c</a></p>\n'
            '<figure><img src="%s/%s/a.png"></figure>\n<pre>a &lt; b &amp;&amp; c</pre>\n<!-- note -->\n' % (RAW, SHA40)
        )
        expected = text.replace("<pre>", '<pre data-code-block-mode="0">')
        self.assertEqual(built(text), expected)

    def test_multiple_and_uppercase_pre(self) -> None:
        out = built("<PRE>a</PRE><pre>b</pre>")
        self.assertEqual(out.count("<pre "), 2)

    def test_prefixed_tag_names_are_not_pre(self) -> None:
        for text in ("<preview>x</preview>", "<pre-wrap>keep\n\nthis</pre-wrap>"):
            with self.subTest(text=text):
                self.assertEqual(built(text), text)
        out = built("<pre-wrap>keep</pre-wrap><pre>x</pre>")
        self.assertEqual(out, '<pre-wrap>keep</pre-wrap><pre data-code-block-mode="0">x</pre>')

    def test_pre_with_attributes_and_newline_in_tag_is_matched(self) -> None:
        self.assertEqual(built('<pre\nclass="a">x</pre>'), '<pre data-code-block-mode="0">x</pre>')


class CheckTests(unittest.TestCase):
    def test_clean_document_has_no_issues(self) -> None:
        text = (
            '<h1>T</h1><p>text</p><figure><img src="%s/%s/a.png"></figure>'
            '<pre data-code-block-mode="2" data-code-block-lang="java">x</pre><pre data-code-block-mode="0">y</pre>'
        ) % (RAW, SHA40)
        self.assertEqual(paste.check_html(text), [])

    def test_markdown_leftover_outside_pre_only(self) -> None:
        self.assertEqual(codes("<p>[a](https://example.com)</p>"), ["markdown-leftover"])
        self.assertEqual(codes('<pre data-code-block-mode="0">[a](https://example.com)</pre>'), [])

    def test_table_outside_pre_only(self) -> None:
        self.assertEqual(codes("<table><tr><td>x</td></tr></table>"), ["table"])
        self.assertEqual(codes('<pre data-code-block-mode="0">&lt;table&gt;</pre>'), [])

    def test_inline_code_outside_pre_only(self) -> None:
        self.assertEqual(codes("<p>use <code>x</code></p>"), ["inline-code"])
        self.assertEqual(codes('<pre data-code-block-mode="0"><code>x</code></pre>'), [])

    def test_pre_attribute_problems(self) -> None:
        self.assertEqual(codes("<pre>x</pre>"), ["pre-attrs"])
        self.assertEqual(codes('<pre data-code-block-mode="2">x</pre>'), ["pre-attrs"])
        self.assertEqual(codes('<pre data-code-block-mode="2" data-code-block-lang="">x</pre>'), ["pre-attrs"])
        self.assertEqual(codes('<pre data-code-block-mode="1">x</pre>'), ["pre-attrs"])
        self.assertEqual(codes('<pre data-code-block-mode="0">x</pre>'), [])

    def test_raw_image_must_be_pinned_to_sha(self) -> None:
        def img(ref: str) -> str:
            return '<img src="%s/%s/docs/a.png">' % (RAW, ref)

        for ok in ("abcdef1", "ABCDEF1234", SHA40):
            with self.subTest(ok=ok):
                self.assertEqual(codes(img(ok)), [])
        for bad in ("main", "v1.0", "abcdef", SHA40 + "0", "refs/heads/main"):
            with self.subTest(bad=bad):
                self.assertEqual(codes(img(bad)), ["image-unpinned"])

    def test_non_raw_hosts_skip_the_sha_check(self) -> None:
        self.assertEqual(codes('<img src="https://example.com/main/a.png">'), [])

    def test_raw_url_decoded_before_check(self) -> None:
        self.assertEqual(codes('<img src="%s/%s/a.png?x=1&amp;y=2">' % (RAW, SHA40)), [])

    def test_repo_raw_prefix_restricts_images(self) -> None:
        inside = '<img src="%s/%s/a.png">' % (RAW, SHA40)
        outside = '<img src="https://example.com/b.png">'
        for prefix in (RAW + "/", RAW):
            with self.subTest(prefix=prefix):
                self.assertEqual(codes(inside, (prefix,)), [])
                self.assertEqual(codes(outside, (prefix,)), ["image-prefix"])
        self.assertEqual(codes(outside), [])
        self.assertEqual(codes('<img src="%s/main/a.png">' % RAW, (RAW,)), ["image-unpinned"])

    def test_non_ascii_left_is_reported_per_line(self) -> None:
        issues = paste.check_html("<p>ok</p>\n<p>café ’</p>\n<p>fine</p>\n<p>ü</p>")
        self.assertEqual([(i.line, i.code) for i in issues], [(2, "non-ascii"), (4, "non-ascii")])
        self.assertIn("2 non-ASCII", issues[0].message)
        self.assertIn("U+00E9", issues[0].message)

    def test_non_ascii_issue_count_is_capped(self) -> None:
        text = "\n".join("é" for _ in range(30))
        issues = paste.check_html(text)
        self.assertEqual(len(issues), paste.MAX_NON_ASCII_ISSUES + 1)
        self.assertIn("more lines", issues[-1].message)

    def test_line_numbers_survive_multiline_pre(self) -> None:
        text = '<pre data-code-block-mode="0">a\nb\nc</pre>\n<p>[x](https://example.com)</p>'
        self.assertEqual([(i.line, i.code) for i in paste.check_html(text)], [(4, "markdown-leftover")])

    def test_empty_interior_line_in_pre_is_flagged(self) -> None:
        issues = paste.check_html('<p>x</p>\n<pre data-code-block-mode="0">a\nb\n\n\nc</pre>')
        self.assertEqual([(i.line, i.code) for i in issues], [(4, "pre-blank-line")])
        self.assertIn("2 empty line(s)", issues[0].message)

    def test_space_indent_and_edge_newlines_are_not_blank_lines(self) -> None:
        for body in ("a\n \nb", "a\n    \nb", "\nfoo\n", "foo\n \n"):
            with self.subTest(body=body):
                self.assertEqual(codes('<pre data-code-block-mode="0">%s</pre>' % body), [])

    def test_check_accepts_what_build_produces_for_blank_lines(self) -> None:
        self.assertEqual(codes(built("<pre>a\n\n\nb\n</pre>")), [])

    def test_non_ascii_inside_pre_is_flagged(self) -> None:
        self.assertEqual(codes('<pre data-code-block-mode="0">caf\u00e9</pre>'), ["non-ascii"])

    def test_img_inside_pre_is_not_an_image(self) -> None:
        text = '<pre data-code-block-mode="0"><img src="%s/main/a.png"></pre>' % RAW
        self.assertEqual(codes(text), [])

    def test_prefix_without_slash_does_not_accept_sibling_repo(self) -> None:
        sibling = '<img src="%s-other/%s/a.png">' % (RAW, SHA40)
        self.assertEqual(codes(sibling, (RAW,)), ["image-prefix"])

    def test_raw_host_check_ignores_hostname_case(self) -> None:
        self.assertEqual(codes('<img src="https://RAW.GitHubUserContent.com/o/r/main/a.png">'), ["image-unpinned"])

    def test_issues_are_sorted_by_line_then_code(self) -> None:
        text = "<p>[a](https://example.com)</p>\n<table></table>\n<pre>x</pre>\n<p>[b](https://example.com) <code>c</code></p>"
        got = [(i.line, i.code) for i in paste.check_html(text)]
        self.assertEqual(
            got,
            [(1, "markdown-leftover"), (2, "table"), (3, "pre-attrs"), (4, "inline-code"), (4, "markdown-leftover")],
        )

    def test_pre_like_tag_names_are_not_pre_blocks_in_check(self) -> None:
        self.assertEqual(codes("<pre-wrap>a\n\nb</pre-wrap>"), [])

    def test_all_issue_kinds_together(self) -> None:
        bad = (FIXTURES / "check-bad.html.txt").read_text(encoding="utf-8")
        found = {issue.code for issue in paste.check_html(bad, (RAW + "/",))}
        self.assertEqual(
            found,
            {
                "markdown-leftover",
                "table",
                "inline-code",
                "pre-attrs",
                "pre-blank-line",
                "image-unpinned",
                "image-prefix",
                "non-ascii",
            },
        )

    def test_build_output_passes_check(self) -> None:
        source = (FIXTURES / "article-input.html.txt").read_text(encoding="utf-8")
        self.assertEqual(paste.check_html(built(source), (RAW + "/",)), [])


class CliTests(unittest.TestCase):
    def test_build_matches_golden_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "article.paste.html"
            code, stdout, _ = run_main("build", str(FIXTURES / "article-input.html.txt"), "-o", str(out))
            self.assertEqual(code, 0)
            self.assertIn("6 pre blocks", stdout)
            self.assertIn("java=1", stdout)
            self.assertEqual(out.read_bytes(), (FIXTURES / "article-expected.html.txt").read_bytes())

    def test_build_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first, second = Path(tmp) / "one.html", Path(tmp) / "two.html"
            self.assertEqual(run_main("build", str(FIXTURES / "article-input.html.txt"), "-o", str(first))[0], 0)
            self.assertEqual(run_main("build", str(first), "-o", str(second))[0], 0)
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_build_handles_crlf_and_bom_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src, out = Path(tmp) / "in.html", Path(tmp) / "out.html"
            src.write_bytes(b"\xef\xbb\xbf<p><strong>a.py</strong></p>\r\n<pre>a\r\n\r\nb</pre>\r\n")
            self.assertEqual(run_main("build", str(src), "-o", str(out))[0], 0)
            data = out.read_bytes()
            self.assertNotIn(b"\r", data)
            self.assertIn(b">a\n \nb</pre>", data)
            self.assertTrue(data.startswith(b"<p>"))

    def test_build_refuses_to_overwrite_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "in.html"
            src.write_text("<pre>x</pre>", encoding="utf-8")
            code, _, err = run_main("build", str(src), "-o", str(src))
            self.assertEqual(code, 2)
            self.assertIn("differ", err)
            self.assertEqual(src.read_text(encoding="utf-8"), "<pre>x</pre>")

    def test_check_exit_codes(self) -> None:
        code, stdout, _ = run_main("check", str(FIXTURES / "article-expected.html.txt"))
        self.assertEqual((code, stdout.startswith("OK:")), (0, True))
        code, stdout, _ = run_main("check", str(FIXTURES / "check-bad.html.txt"))
        self.assertEqual(code, 1)
        for name in ("markdown-leftover", "table", "inline-code", "pre-attrs", "pre-blank-line", "image-unpinned", "non-ascii"):
            self.assertIn(": %s:" % name, stdout)
        self.assertNotIn("image-prefix", stdout)
        self.assertIn("issue(s) in", stdout)

    def test_check_repo_raw_prefix_flag(self) -> None:
        code, stdout, _ = run_main("check", str(FIXTURES / "check-bad.html.txt"), "--repo-raw-prefix", RAW + "/")
        self.assertEqual(code, 1)
        self.assertIn("image-prefix", stdout)
        code, _, _ = run_main("check", str(FIXTURES / "article-expected.html.txt"), "--repo-raw-prefix", RAW + "/")
        self.assertEqual(code, 0)
        code, stdout, _ = run_main("check", str(FIXTURES / "article-expected.html.txt"), "--repo-raw-prefix", "https://example.com/")
        self.assertEqual(code, 1)
        self.assertIn("image-prefix", stdout)

    def test_io_and_usage_errors_exit_two(self) -> None:
        missing = str(FIXTURES / "does-not-exist.html")
        self.assertEqual(run_main("check", missing)[0], 2)
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(run_main("build", missing, "-o", str(Path(tmp) / "o.html"))[0], 2)
            bad = Path(tmp) / "bad.html"
            bad.write_bytes(b"<p>\xff\xfe</p>")
            code, _, err = run_main("check", str(bad))
            self.assertEqual(code, 2)
            self.assertIn("error:", err)
            self.assertEqual(run_main("build", str(FIXTURES / "article-input.html.txt"), "-o", str(Path(tmp) / "no-dir" / "o.html"))[0], 2)
        self.assertEqual(run_main()[0], 2)
        self.assertEqual(run_main("build", str(FIXTURES / "article-input.html.txt"))[0], 2)
        self.assertEqual(run_main("bogus")[0], 2)

    def test_help_exits_zero(self) -> None:
        self.assertEqual(run_main("--help")[0], 0)
        self.assertEqual(run_main("check", "--help")[0], 0)

    def test_check_survives_strict_ascii_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "arrow.html"
            src.write_text("<p>arrow \u2192 [x](https://example.com/\u00e9)</p>\n", encoding="utf-8")
            raw = io.BytesIO()
            stream = io.TextIOWrapper(raw, encoding="ascii", errors="strict", write_through=True)
            with contextlib.redirect_stdout(stream):
                code = paste.main(["check", str(src)])
            self.assertEqual(code, 1)
            out = raw.getvalue().decode("ascii")
            self.assertIn("markdown-leftover", out)
            self.assertIn("\\u2192", out)
            self.assertIn("issue(s) in", out)

    def test_check_survives_cp1252_and_ascii_consoles_in_a_process(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "arrow.html"
            src.write_text("<p>arrow \u2192 [x](https://example.com/y)</p>\n", encoding="utf-8")
            missing = Path(tmp) / "caf\u00e9-missing.html"
            for encoding in ("cp1252", "ascii"):
                env = dict(os.environ, PYTHONIOENCODING=encoding)
                env.pop("PYTHONUTF8", None)
                with self.subTest(encoding=encoding):
                    bad = subprocess.run(
                        [sys.executable, str(SCRIPT), "check", str(src)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                    )
                    self.assertEqual(bad.returncode, 1, bad.stderr)
                    self.assertIn(b"markdown-leftover", bad.stdout)
                    self.assertIn(b"\\u2192", bad.stdout)
                    self.assertEqual(bad.stderr, b"")
                    gone = subprocess.run(
                        [sys.executable, str(SCRIPT), "check", str(missing)],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                    )
                    self.assertEqual(gone.returncode, 2, gone.stderr)
                    self.assertIn(b"error:", gone.stderr)
                    self.assertNotIn(b"Traceback", gone.stderr)

    def test_script_runs_as_a_process(self) -> None:
        good = subprocess.run(
            [sys.executable, str(SCRIPT), "check", str(FIXTURES / "article-expected.html.txt")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(good.returncode, 0, good.stderr)
        bad = subprocess.run(
            [sys.executable, str(SCRIPT), "check", str(FIXTURES / "check-bad.html.txt")],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(bad.returncode, 1, bad.stderr)


if __name__ == "__main__":
    unittest.main()
