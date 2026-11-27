from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Dict, List, Optional


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "medium-publishing" / "scripts" / "check_publication.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "check-publication"
PROFILE = FIXTURES / "profile-example.md.txt"
BAD_PROFILE = FIXTURES / "profile-malformed.md.txt"
SPEC = importlib.util.spec_from_file_location("check_publication", SCRIPT)
assert SPEC and SPEC.loader
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
SPEC.loader.exec_module(guard)

ARTICLE_LINK = "https://medium.com/@example/retry-policies-123abc"
REPO_LINK = "https://github.com/example-owner/retry-policies"
POST_ARGS = ["--require-link", ARTICLE_LINK, "--require-link", REPO_LINK, "--forbid", "strategy"]
ARTICLE_ARGS = ["--forbid-title", "strategy"]


def run_main(*argv: str) -> "tuple[int, str, str]":
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = guard.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def fixture(name: str) -> Path:
    return FIXTURES / name


def run_post(name: str, *extra: str) -> "tuple[int, str, str]":
    """A fixture post under the example profile (1300 characters, 5 hashtags, hook 200)."""
    return run_main("post", str(fixture(name)), "--profile", str(PROFILE), *POST_ARGS, *extra)


def run_article(name: str, *extra: str) -> "tuple[int, str, str]":
    """A fixture article under the example profile (1300 words, 1 code block of 15 lines, 2-3 images)."""
    return run_main("article", str(fixture(name)), "--profile", str(PROFILE), *ARTICLE_ARGS, *extra)


def rules(report: "guard.Report") -> "List[str]":
    return [f.rule for f in report.findings]


def post_rules(text: str, **kwargs: object) -> "List[str]":
    kwargs.setdefault("hook_chars", 100000)  # the hook rule has its own tests
    return rules(guard.check_post(text, **kwargs))  # type: ignore[arg-type]


def article_rules(text: str, fmt: str = "markdown", **kwargs: object) -> "List[str]":
    kwargs.setdefault("min_images", 0)  # the image rules have their own tests
    return rules(guard.check_article(text, fmt, **kwargs))  # type: ignore[arg-type]


def md_article(body: str = "Some words here.\n", title: Optional[str] = "A title", action: str = "## Next steps\n\nGo.\n") -> str:
    head = "# %s\n\n" % title if title is not None else ""
    return head + body + "\n" + action


def fenced(lines: int) -> str:
    return "```java\n" + "\n".join("int a%d = %d;" % (i, i) for i in range(lines)) + "\n```\n"


class PostFixtureTests(unittest.TestCase):
    def test_passing_post_prints_the_measured_values(self) -> None:
        code, out, err = run_post("post-pass.txt")
        self.assertEqual((code, err), (0, ""), out)
        self.assertTrue(out.startswith("ok:"), out)
        self.assertEqual(out.count("\n"), 1)
        for measured in ("chars=1042/1300", "hashtags=4/5", "hook=102/200", "links=2/2", "topics=4/4"):
            self.assertIn(measured, out)

    def assert_single_violation(self, name: str, rule: str, *needles: str) -> None:
        code, out, err = run_post(name)
        self.assertEqual((code, err), (1, ""), out)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        self.assertTrue(lines[0].startswith("violation: "), out)
        self.assertIn(": %s: " % rule, lines[0])
        for needle in needles:
            self.assertIn(needle, lines[0])
        self.assertFalse(out.startswith("ok:"), out)

    def test_six_hashtags_fail_only_the_hashtag_limit(self) -> None:
        self.assert_single_violation("post-six-hashtags.txt", "hashtags", "6 hashtags, max 5", "#Backoff")

    def test_long_hook_fails_only_the_hook_limit(self) -> None:
        self.assert_single_violation("post-long-hook.txt", "hook", "217 characters, max 200")

    def test_missing_link_fails_only_the_link_rule(self) -> None:
        self.assert_single_violation("post-missing-link.txt", "link", REPO_LINK)

    def test_unbacked_hashtag_fails_only_the_topic_rule(self) -> None:
        self.assert_single_violation("post-unbacked-hashtag.txt", "topic", "#Kubernetes")

    def test_every_post_fixture_passes_without_the_options_that_target_it(self) -> None:
        self.assertEqual(run_main("post", str(fixture("post-six-hashtags.txt")), "--max-hashtags", "6")[0], 0)
        self.assertEqual(run_main("post", str(fixture("post-long-hook.txt")), "--hook-chars", "217")[0], 0)
        self.assertEqual(run_main("post", str(fixture("post-missing-link.txt")), "--require-link", ARTICLE_LINK)[0], 0)
        self.assertEqual(run_main("post", str(fixture("post-unbacked-hashtag.txt")),
                                  "--alias", "#Kubernetes=container orchestration")[0], 1)
        self.assertEqual(run_main("post", str(fixture("post-unbacked-hashtag.txt")),
                                  "--alias", "kubernetes=retry rule", "--alias", "x=y")[0], 0)

    def test_forbidden_term_in_the_hook_fails_even_when_the_rest_passes(self) -> None:
        code, out, _ = run_main("post", str(fixture("post-pass.txt")), "--forbid", "RETRY POLICY", "--forbid", "kafka")
        self.assertEqual(code, 1)
        self.assertEqual(out.count("violation:"), 1)
        self.assertIn(": forbid: hook contains forbidden term \"RETRY POLICY\"", out)

    def test_forbidden_term_outside_the_hook_is_fine(self) -> None:
        self.assertEqual(run_main("post", str(fixture("post-pass.txt")), "--forbid", "idempotent")[0], 0)

    def test_all_violations_are_listed_together(self) -> None:
        code, out, _ = run_main("post", str(fixture("post-six-hashtags.txt")), "--max-chars", "500",
                                "--hook-chars", "50", "--require-link", "https://example.org/missing")
        self.assertEqual(code, 1)
        self.assertEqual(sorted(line.split(": ")[2] for line in out.splitlines()), ["chars", "hashtags", "hook", "link"])


class PostRuleTests(unittest.TestCase):
    def test_character_limit_is_inclusive(self) -> None:
        self.assertEqual(post_rules("a" * 1300), [])
        self.assertEqual(post_rules("a" * 1301), ["chars"])
        self.assertEqual(post_rules("  \n" + "a" * 1300 + "\n\n  "), [])
        self.assertEqual(post_rules("a" * 11, max_chars=10), ["chars"])

    def test_crlf_counts_as_one_character(self) -> None:
        text = "\r\n".join(["x" * 49] * 20)  # 20 * 49 + 19 line ends
        self.assertEqual(guard.check_post(text).summary.split()[1], "chars=999/1300")

    def test_hashtag_limit_is_inclusive(self) -> None:
        tags = " ".join("#Tag%s" % c for c in "ABCDE")
        text = "tag a, tag b, tag c, tag d, tag e.\n\n" + tags
        self.assertEqual(post_rules(text), [])
        self.assertEqual(post_rules(text + " #TagF"), ["hashtags", "topic"])
        self.assertEqual(post_rules(text, max_hashtags=4), ["hashtags"])

    def test_hashtag_detection(self) -> None:
        find = guard.find_hashtags
        self.assertEqual(find("see https://example.org/page#section and www.example.org/a#b"), [])
        self.assertEqual(find("C# and F# and a#b and &#39; and ##double"), [])
        self.assertEqual(find("issue #1 and # alone and #_x"), [])
        self.assertEqual([n for _, n in find("(#Java) #System_Design,#Go!")], ["Java", "System_Design", "Go"])
        self.assertEqual(find("one\n\ntwo #Tag")[0], (3, "Tag"))
        self.assertEqual([n for _, n in find("#Padr\u00f5es")], ["Padr\u00f5es"])

    def test_hashtag_in_a_url_does_not_count_toward_the_limit(self) -> None:
        text = "Hook java.\n\nRead https://example.org/a#one#two now\n\n#Java"
        self.assertEqual(post_rules(text, max_hashtags=1), [])

    def test_hook_is_the_text_before_the_first_blank_line(self) -> None:
        hook = "h" * 200
        self.assertEqual(post_rules(hook + "\n\nbody", hook_chars=200), [])
        self.assertEqual(post_rules(hook + "h\n\nbody", hook_chars=200), ["hook"])
        self.assertEqual(post_rules("line one\n" + "h" * 195 + "\n\nbody", hook_chars=200), ["hook"])
        self.assertEqual(post_rules("short\n \t\n" + "b" * 400, hook_chars=200), [])
        self.assertEqual(post_rules("\n\n" + hook + "\n\nbody", hook_chars=200), [])
        self.assertEqual(rules(guard.check_post(hook + "\n\nbody")), [])  # the default is 200
        self.assertEqual(rules(guard.check_post(hook + "h\n\nbody")), ["hook"])

    def test_a_post_without_a_blank_line_is_all_hook(self) -> None:
        self.assertEqual(post_rules("w " * 120, hook_chars=200), ["hook"])

    def test_required_links(self) -> None:
        text = "Read https://example.org/a/b. Then https://example.org/c?utm=1, and (https://example.org/d#top)."
        ok = guard.check_post(text, require_links=["https://example.org/a/b", "https://example.org/c/", "https://example.org/d"])
        self.assertEqual(ok.findings, [])
        for wrong in ("https://example.org/a", "https://example.org/a/b/c", "https://example.org/", "http://example.org/a/b"):
            with self.subTest(link=wrong):
                self.assertEqual(rules(guard.check_post(text, require_links=[wrong])), ["link"])

    def test_topic_is_matched_after_splitting_camel_case(self) -> None:
        tags = "\n\n#SystemDesign"
        self.assertEqual(post_rules("A note on System Design." + tags), [])
        self.assertEqual(post_rules("A note on system-design." + tags), [])
        self.assertEqual(post_rules("A note on SYSTEM   DESIGN." + tags), [])
        self.assertEqual(post_rules("A note on systemdesign." + tags), [])
        self.assertEqual(post_rules("A note on design systems." + tags), ["topic"])
        self.assertEqual(post_rules("A note on system designs." + tags), ["topic"])
        self.assertEqual(post_rules("Subsystem design." + tags), ["topic"])

    def test_topic_ignores_the_hashtag_line_inline_hashtags_and_urls(self) -> None:
        self.assertEqual(post_rules("Only the tag.\n\n#Java #Other"), ["topic", "topic"])
        self.assertEqual(post_rules("Built with #Java today.\n\n#Java"), ["topic"])
        self.assertEqual(post_rules("Read https://example.org/java-guide\n\n#Java"), ["topic"])
        self.assertEqual(post_rules("Java 25 is out.\n\n#Java #Java25"), [])
        self.assertEqual(post_rules("Java is out.\n\n#Java #Java25"), ["topic"])

    def test_each_unbacked_tag_is_reported_once(self) -> None:
        report = guard.check_post("Nothing here.\n\n#Alpha #alpha #Beta")
        self.assertEqual([f.rule for f in report.findings], ["topic", "topic"])
        self.assertIn("topics=0/2", report.summary)

    def test_split_camel_case(self) -> None:
        self.assertEqual(guard.split_camel("SystemDesign"), ["system", "design"])
        self.assertEqual(guard.split_camel("LLMOps"), ["llm", "ops"])
        self.assertEqual(guard.split_camel("Java25"), ["java", "25"])
        self.assertEqual(guard.split_camel("OOP"), ["oop"])
        self.assertEqual(guard.split_camel("system_design"), ["system", "design"])
        self.assertEqual(guard.split_camel("DesignPatterns"), ["design", "patterns"])

    def test_alias_backs_a_tag_in_addition_to_camel_case(self) -> None:
        text = "We use object-oriented design.\n\n#OOP"
        self.assertEqual(post_rules(text), ["topic"])
        self.assertEqual(post_rules(text, aliases={"oop": ["Object Oriented"]}), [])
        self.assertEqual(post_rules("We use oop.\n\n#OOP", aliases={"oop": ["object oriented"]}), [])
        self.assertEqual(post_rules(text, aliases={"java": ["object oriented"]}), ["topic"])

    def test_forbid_checks_only_the_hook_and_ignores_case_and_line_breaks(self) -> None:
        text = "The Chain of\nResponsibility trap.\n\nBody about strategy.\n\n#Body"
        self.assertEqual(post_rules(text, forbid=["strategy"]), [])
        self.assertEqual(post_rules(text, forbid=["chain of responsibility"]), ["forbid"])
        self.assertEqual(post_rules(text, forbid=["TRAP", "responsibility"]), ["forbid", "forbid"])


class ArticleFixtureTests(unittest.TestCase):
    def assert_single_violation(self, name: str, rule: str, *needles: str) -> None:
        code, out, err = run_article(name)
        self.assertEqual((code, err), (1, ""), out)
        lines = out.splitlines()
        self.assertEqual(len(lines), 1, out)
        self.assertTrue(lines[0].startswith("violation: "), out)
        self.assertIn(": %s: " % rule, lines[0])
        for needle in needles:
            self.assertIn(needle, lines[0])

    def test_passing_markdown_article_prints_the_measured_values(self) -> None:
        code, out, err = run_article("article-pass.md.txt", "--subtitle", "One policy per route")
        self.assertEqual((code, err), (0, ""), out)
        self.assertEqual(out.count("\n"), 1)
        for measured in ("format=markdown", "title=60/100", "subtitle=20/140", "words=299/1300", "code_blocks=1/1",
                         "longest_code=13/15", "images=2[2-3]", "action_heading=\"Next steps\""):
            self.assertIn(measured, out)

    def test_passing_html_article(self) -> None:
        code, out, err = run_article("article-pass.html.txt")
        self.assertEqual((code, err), (0, ""), out)
        for measured in ("format=html", "title=60/100", "subtitle=-/140", "words=159/1300", "code_blocks=1/1",
                         "longest_code=3/15", "images=2[2-3]"):
            self.assertIn(measured, out)

    def test_pattern_name_in_the_title_fails_only_that_rule(self) -> None:
        self.assert_single_violation("article-pattern-in-title.md.txt", "title-forbidden", "\"strategy\"")

    def test_over_budget_article_fails_only_the_word_limit(self) -> None:
        self.assert_single_violation("article-over-budget.md.txt", "words", "1346 words, max 1300")

    def test_too_many_code_blocks_fail_only_the_block_limit(self) -> None:
        self.assert_single_violation("article-two-code-blocks.md.txt", "code-blocks", "2 code blocks, max 1")

    def test_missing_next_step_heading_fails_only_that_rule(self) -> None:
        self.assert_single_violation("article-no-next-step.md.txt", "action-heading", "/next step/i")

    def test_too_few_images_fail_only_the_minimum(self) -> None:
        self.assert_single_violation("article-too-few-images.md.txt", "images-min", "1 image, min 2")

    def test_too_many_images_fail_only_the_maximum(self) -> None:
        self.assert_single_violation("article-too-many-images.md.txt", "images-max", "4 images, max 3")

    def test_indented_code_block_is_a_code_block_and_not_words(self) -> None:
        self.assert_single_violation("article-indented-code.md.txt", "code-lines", "code block 1 has 20 lines, max 15")
        code, out, _ = run_article("article-indented-code.md.txt", "--max-code-lines", "20")
        self.assertEqual(code, 0, out)
        self.assertIn("code_blocks=1/1 longest_code=20/20", out)
        self.assertIn("words=299/1300", out)

    def test_markdown_link_left_in_html_fails_only_that_rule(self) -> None:
        self.assert_single_violation("article-md-link-in-html.html.txt", "markdown-link", ":22:", "1 leftover")

    def test_fixtures_pass_when_the_matching_limit_is_relaxed(self) -> None:
        self.assertEqual(run_main("article", str(fixture("article-over-budget.md.txt")), "--max-words", "1346")[0], 0)
        self.assertEqual(run_main("article", str(fixture("article-two-code-blocks.md.txt")), "--max-code-blocks", "2")[0], 0)
        self.assertEqual(run_main("article", str(fixture("article-too-few-images.md.txt")), "--min-images", "1")[0], 0)
        self.assertEqual(run_main("article", str(fixture("article-too-many-images.md.txt")), "--max-images", "4")[0], 0)
        self.assertEqual(run_main("article", str(fixture("article-no-next-step.md.txt")),
                                  "--action-heading", "links?$")[0], 0)
        self.assertEqual(run_main("article", str(fixture("article-pattern-in-title.md.txt")),
                                  "--forbid-title", "factory")[0], 0)


class MarkdownRuleTests(unittest.TestCase):
    def test_word_budget_is_inclusive_and_skips_code_images_and_title(self) -> None:
        body = " ".join(["word"] * 40) + "\n\n" + fenced(10) + "\n![alt text here](https://example.org/a.png)\n"
        self.assertEqual(article_rules(md_article(body, action="## Next step\n"), max_words=42), [])
        self.assertEqual(article_rules(md_article(body, action="## Next step\n"), max_words=41), ["words"])
        report = guard.check_article(md_article(body, title="Many words in the title"), "markdown", min_images=0)
        self.assertIn("words=43/1500", report.summary)

    def test_word_counting_details(self) -> None:
        parsed = guard.parse_markdown(
            "# Title words\n\n## Heading two\n\n- bullet one\n1. numbered two\n> quote three\n"
            "[link text](https://example.org/very/long/url) and ![img](x.png) end\n"
            "<!-- hidden words\nacross lines -->\n---\n| a | b |\n[ref]: https://example.org\n<br>\n"
        )
        self.assertEqual(parsed.title, "Title words")
        self.assertEqual(parsed.words, 2 + 2 + 2 + 2 + 4 + 2)

    def test_code_block_limits(self) -> None:
        self.assertEqual(article_rules(md_article(fenced(15))), [])
        self.assertEqual(article_rules(md_article(fenced(16))), ["code-lines"])
        self.assertEqual(article_rules(md_article(fenced(16)), max_code_lines=16), [])
        self.assertEqual(article_rules(md_article(fenced(2) + "\ntext\n\n" + fenced(2))), ["code-blocks"])
        self.assertEqual(article_rules(md_article(fenced(2) + "\n" + fenced(20) + "\n" + fenced(3))),
                         ["code-blocks", "code-lines"])
        self.assertEqual(article_rules(md_article("text only")), [])
        self.assertEqual(article_rules(md_article(fenced(2)), max_code_blocks=0), ["code-blocks"])

    def test_blank_lines_inside_a_code_block_count_but_edge_blank_lines_do_not(self) -> None:
        inner = "\n".join(["a"] * 7 + [""] + ["b"] * 7)
        self.assertEqual(article_rules(md_article("```\n" + inner + "\n```\n")), [])
        self.assertEqual(article_rules(md_article("```\n" + inner + "\nc\n```\n")), ["code-lines"])
        self.assertEqual(article_rules(md_article("```\n\n\n" + inner + "\n\n```\n")), [])

    def test_fence_forms(self) -> None:
        tilde = "~~~\n" + "\n".join("x" for _ in range(16)) + "\n~~~\n"
        self.assertEqual(article_rules(md_article(tilde)), ["code-lines"])
        nested = "````\n" + "```\ninner\n```\n" + "\n".join("x" for _ in range(13)) + "\n````\n"
        self.assertEqual(article_rules(md_article(nested)), ["code-lines"])
        self.assertEqual(article_rules(md_article("```\n# not a heading\n~~~\nstill code\n```\n")), [])

    def test_headings_inside_code_blocks_are_not_the_title_or_a_section(self) -> None:
        text = "```\n# fake title\n## Next step\n```\n\n# Real title\n"
        report = guard.check_article(text, "markdown", min_images=0)
        self.assertEqual(rules(report), ["action-heading"])
        self.assertIn("title=10/100", guard.check_article(text + "\n## Next step\n", "markdown", min_images=0).summary)

    def test_unclosed_fence_is_reported_with_its_line(self) -> None:
        report = guard.check_article(md_article("intro\n\n```java\nint a;\n"), "markdown", min_images=0)
        self.assertIn("fence", rules(report))
        self.assertEqual([f.line for f in report.findings if f.rule == "fence"], [5])

    def test_title_rules(self) -> None:
        self.assertEqual(article_rules(md_article(title="t" * 100)), [])
        self.assertEqual(article_rules(md_article(title="t" * 101)), ["title-length"])
        self.assertEqual(article_rules(md_article(title=None)), ["title"])
        self.assertEqual(article_rules(md_article(title=None), title="Passed in"), [])
        self.assertEqual(article_rules(md_article(title="t" * 101), title="Short"), [])
        self.assertEqual(article_rules(md_article(title="Short"), title="t" * 101), ["title-length"])
        self.assertEqual(article_rules(md_article(title="The OBSERVER way"), forbid_title=["observer"]), ["title-forbidden"])
        self.assertEqual(article_rules(md_article(title="The Observer way"), forbid_title=["observer", "way"]),
                         ["title-forbidden", "title-forbidden"])
        self.assertEqual(article_rules(md_article(title="Clean")), [])

    def test_the_first_h1_is_the_title_and_later_h1_headings_are_sections(self) -> None:
        text = "# First\n\nbody\n\n# Next step\n"
        self.assertEqual(article_rules(text), [])
        self.assertEqual(article_rules("# Next step\n\nbody\n"), ["action-heading"])
        self.assertEqual(article_rules("#hashtag-not-heading\n\n## Next step\n"), ["title"])

    def test_forbidden_term_in_the_body_is_allowed(self) -> None:
        self.assertEqual(article_rules(md_article("The Observer pattern in the body."), forbid_title=["observer"]), [])

    def test_subtitle_rules(self) -> None:
        self.assertEqual(article_rules(md_article(), subtitle="s" * 140), [])
        self.assertEqual(article_rules(md_article(), subtitle="s" * 141), ["subtitle-length"])
        self.assertEqual(article_rules(md_article(), subtitle="Why Observer wins", forbid_title=["observer"]),
                         ["subtitle-forbidden"])
        self.assertEqual(article_rules(md_article(title="Observer"), subtitle="Observer " + "s" * 140,
                                       forbid_title=["observer"]),
                         ["title-forbidden", "subtitle-length", "subtitle-forbidden"])
        self.assertEqual(article_rules(md_article()), [])

    def test_action_heading_regex(self) -> None:
        for heading in ("## Next step", "### NEXT STEPS", "## Your next step: run it", "## 5. Next steps"):
            with self.subTest(heading=heading):
                self.assertEqual(article_rules(md_article(action=heading + "\n")), [])
        for heading in ("## Next", "## Step next", "Next steps in a paragraph"):
            with self.subTest(heading=heading):
                self.assertEqual(article_rules(md_article(action=heading + "\n")), ["action-heading"])
        self.assertEqual(article_rules(md_article(action="## Call to action\n"), action_heading="^call to action$"), [])
        self.assertEqual(article_rules(md_article(action="## Next steps\n"), action_heading="^call to action$"),
                         ["action-heading"])

    def test_markdown_links_are_normal_in_markdown(self) -> None:
        self.assertEqual(article_rules(md_article("See [the repo](https://example.org/r).")), [])

    def test_unicode_is_reported_as_ascii(self) -> None:
        report = guard.check_article("# Padr\u00e3o \u00e9\n\nbody\n", "markdown", forbid_title=["\u00e3o"], min_images=0)
        self.assertEqual(rules(report), ["title-forbidden", "action-heading"])
        for finding in report.findings:
            finding.message.encode("ascii")


class MarkdownCodeBlockTests(unittest.TestCase):
    """Fenced and indented code in lists, as CommonMark reads them."""

    def parse(self, text: str) -> "guard.Parsed":
        return guard.parse_markdown(text)

    def blocks(self, text: str) -> "List[int]":
        return [b.lines for b in self.parse(text).code_blocks]

    def test_thirty_indented_lines_are_one_code_block_and_no_words(self) -> None:
        code = "\n".join("    int a%d = %d;" % (i, i) for i in range(30))
        text = "# Title\n\nIntro words here.\n\n" + code + "\n\n## Next steps\n"
        parsed = self.parse(text)
        self.assertEqual([(b.line, b.lines) for b in parsed.code_blocks], [(5, 30)])
        self.assertEqual(parsed.words, 3 + 2)
        self.assertEqual(article_rules(text), ["code-lines"])

    def test_indented_block_after_a_paragraph_line_is_a_continuation(self) -> None:
        text = "# T\n\nExample follows:\n    not code\n    still not code\n"
        parsed = self.parse(text)
        self.assertEqual(parsed.code_blocks, [])
        self.assertEqual(parsed.words, 2 + 2 + 3)

    def test_indented_block_after_heading_blank_line_or_at_the_start(self) -> None:
        self.assertEqual(self.blocks("# T\n\n## Section\n    a\n    b\n"), [2])
        self.assertEqual(self.blocks("    a\n    b\n\ntext\n"), [2])
        self.assertEqual(self.blocks("text\n\n    a\n\ntext\n\n    b\n"), [1, 1])

    def test_indented_block_ends_at_a_dedented_line_and_keeps_inner_blank_lines(self) -> None:
        text = "text\n\n    a\n\n\n    b\n\n  dedented words\n"
        parsed = self.parse(text)
        self.assertEqual([b.lines for b in parsed.code_blocks], [4])
        self.assertEqual(parsed.words, 1 + 2)
        self.assertEqual(self.blocks("text\n\n    a\n    b\n\n\n\nmore\n"), [2])

    def test_deeper_indent_inside_an_indented_block_stays_code(self) -> None:
        self.assertEqual(self.blocks("text\n\n    a\n        b\n      c\n"), [3])

    def test_tab_indent_is_four_columns(self) -> None:
        self.assertEqual(self.blocks("text\n\n\ta\n\tb\n"), [2])
        self.assertEqual(self.blocks("text\n\n  \ta\n"), [1])

    def test_headings_and_fences_inside_indented_code_are_text(self) -> None:
        text = "text\n\n    # fake title\n    ```\n    ## Next step\n\nend words\n"
        parsed = self.parse(text)
        self.assertIsNone(parsed.title)
        self.assertEqual(parsed.headings, [])
        self.assertEqual([b.lines for b in parsed.code_blocks], [3])
        self.assertEqual(parsed.unclosed_fences, [])

    def test_fence_nested_in_list_items_at_any_depth(self) -> None:
        for indent in (2, 3, 4, 6, 7, 8, 12):
            pad = " " * indent
            text = "1. Step one\n\n%s```java\n%sint a;\n%sint b;\n%s```\n\nOutside words.\n" % (pad, pad, pad, pad)
            with self.subTest(indent=indent):
                parsed = self.parse(text)
                self.assertEqual([b.lines for b in parsed.code_blocks], [2], text)
                self.assertEqual(parsed.unclosed_fences, [])
                self.assertEqual(parsed.words, 2 + 2)

    def test_fence_in_nested_list_and_directly_after_the_item_line(self) -> None:
        text = "- outer\n  - inner\n      ```\n      x\n      ```\n  - sibling words\n\nAfter list.\n"
        parsed = self.parse(text)
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.words, 1 + 1 + 2 + 2)

    def test_tilde_fence_in_a_list_item_and_a_closing_fence_at_another_indent(self) -> None:
        text = "- item\n\n      ~~~\n      x\n    ~~~\n\nafter\n"
        parsed = self.parse(text)
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.unclosed_fences, [])

    def test_two_fences_in_two_list_items_are_two_blocks(self) -> None:
        text = "1. one\n\n   ```\n   a\n   ```\n\n2. two\n\n   ```\n   b\n   ```\n"
        self.assertEqual(self.blocks(text), [1, 1])
        self.assertEqual(article_rules(md_article(text)), ["code-blocks"])

    def test_unclosed_fence_in_a_list_item_is_reported(self) -> None:
        parsed = self.parse("- item\n\n      ```\n      x\n")
        self.assertEqual(parsed.unclosed_fences, [3])
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])

    def test_top_level_fence_indented_past_three_is_indented_code_not_a_fence(self) -> None:
        parsed = self.parse("text\n\n    ```\n    x\n    ```\n")
        self.assertEqual([b.lines for b in parsed.code_blocks], [3])
        self.assertEqual(parsed.unclosed_fences, [])

    def test_indented_text_in_a_list_item_is_not_code(self) -> None:
        for text, words in (
            ("- item\n\n  second paragraph words\n", 4),
            ("- item\n\n    four spaces is only two past the item content\n", 10),
            ("-   wide marker\n\n    aligned with the content\n", 6),
            ("1. item\n\n   three\n\n    four\n", 3),
            ("- item\n    lazy continuation\n", 3),
            ("- item\n\n    - nested bullet\n", 3),
        ):
            with self.subTest(text=text):
                parsed = self.parse(text)
                self.assertEqual(parsed.code_blocks, [], text)
                self.assertEqual(parsed.words, words, text)

    def test_indented_code_inside_a_list_item_needs_four_columns_past_the_content(self) -> None:
        self.assertEqual(self.blocks("- item\n\n      code\n      more\n"), [2])
        self.assertEqual(self.blocks("1. item\n\n       code\n"), [1])
        self.assertEqual(self.blocks("-   wide\n\n        code\n"), [1])
        text = "- item\n\n      code\n\n  paragraph words\n\n- next item\n"
        parsed = self.parse(text)
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.words, 1 + 2 + 1 + 1)

    def test_text_after_a_list_returns_to_the_margin(self) -> None:
        text = "- item\n\nParagraph words.\n\n    code after the list\n"
        parsed = self.parse(text)
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.words, 1 + 2)

    def test_numbers_do_not_open_list_items_inside_a_paragraph(self) -> None:
        text = "The year was\n1986. It rained.\n\n    code\n"
        parsed = self.parse(text)
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.words, 3 + 3)

    def test_thematic_breaks_setext_underlines_and_quotes_are_not_code(self) -> None:
        parsed = self.parse("Title words\n===========\n\n> quote words\n\n---\n\nplain words\n")
        self.assertEqual(parsed.code_blocks, [])
        self.assertEqual(parsed.words, 2 + 2 + 2)

    def test_a_comment_line_is_an_html_block_and_ends_a_paragraph(self) -> None:
        self.assertEqual(self.blocks("text\n<!-- note -->\n    code after the comment\n"), [1])
        self.assertEqual(self.blocks("text\n\n<!-- note -->\n    code\n"), [1])
        self.assertEqual(self.blocks("text <!-- note -->\n    still the same paragraph\n"), [])
        self.assertEqual(self.blocks("text\n<!-- multi\nline -->\n    code\n"), [1])
        parsed = self.parse("- item\n<!-- note -->\n    code after the list\n")
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.words, 1)

    def test_a_thematic_break_or_setext_underline_ends_a_paragraph(self) -> None:
        for text in ("# H\n---\n    code\n", "text\n---\n    code\n", "text\n***\n    code\n", "text\n* * *\n    code\n",
                     "text\n===\n    code\n", "text\n-\n    code\n", "text\n--\n    code\n", "- item\n  ---\n      code\n"):
            with self.subTest(text=text):
                self.assertEqual(self.blocks(text), [1], text)
        for text in ("text\n---x\n    lazy\n", "text\n+++\n    lazy\n", "text\n== =\n    lazy\n"):
            with self.subTest(text=text):
                self.assertEqual(self.blocks(text), [], text)

    def test_an_empty_list_item_holds_no_paragraph(self) -> None:
        parsed = self.parse("-\n      six spaces\n")
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.words, 0)
        self.assertEqual(self.blocks("1.\n        eight spaces\n"), [1])
        self.assertEqual(self.blocks("- \n      six spaces\n"), [1])
        self.assertEqual(self.blocks("text\n-\n      six spaces\n"), [1])  # the dash underlines "text"

    def test_a_list_item_outside_the_container_is_not_an_interruption(self) -> None:
        self.assertEqual(self.blocks("* item two\n2. second\n\n      six spaces\n"), [])
        self.assertEqual(self.blocks("2. second\n-\n    indented four\n  two spaces\n"), [])
        self.assertEqual(self.blocks("- item\n2. second\n\n          ten spaces\n"), [1])

    def test_a_lazy_continuation_line_keeps_the_list_item_open(self) -> None:
        self.assertEqual(self.blocks("   1. deep num\n    - deep bullet\n\n        indented eight\n"), [])

    def test_a_block_quote_ends_a_list(self) -> None:
        parsed = self.parse("- item one\n> quote words\n\n    indented four\n")
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.words, 2 + 2)

    def test_entities_are_decoded_before_counting(self) -> None:
        self.assertEqual(self.parse("x &amp; y &nbsp; z &lt;b&gt;\n").words, 4)

    def test_the_toolkit_article_shape_still_reads_the_same(self) -> None:
        text = (FIXTURES / "article-pass.md.txt").read_text(encoding="utf-8")
        parsed = self.parse(text)
        self.assertEqual([b.lines for b in parsed.code_blocks], [13])
        self.assertEqual(parsed.words, 299)
        self.assertEqual(parsed.images, 2)


class ImageRuleTests(unittest.TestCase):
    def images(self, text: str, fmt: str = "markdown") -> int:
        return (guard.parse_html(text) if fmt == "html" else guard.parse_markdown(text)).images

    def test_markdown_image_forms(self) -> None:
        self.assertEqual(self.images("![a](x.png)"), 1)
        self.assertEqual(self.images("![](x.png) and ![b](y.png \"title\") side by side"), 2)
        self.assertEqual(self.images("![a][ref]\n\n[ref]: x.png"), 1)
        self.assertEqual(self.images("[![badge](b.svg)](https://example.org)"), 1)
        self.assertEqual(self.images('<img src="x.png" alt="a"> and <IMG src="y.png">'), 2)
        self.assertEqual(self.images("# ![in heading](x.png)\n\ntext"), 1)
        self.assertEqual(self.images("- ![in list](x.png)\n- ![in list](y.png)"), 2)

    def test_not_images(self) -> None:
        self.assertEqual(self.images("[link](https://example.org/x.png) and ![unclosed](x.png"), 0)
        self.assertEqual(self.images("```\n![a](x.png)\n```\n"), 0)
        self.assertEqual(self.images("text\n\n    ![a](x.png)\n"), 0)
        self.assertEqual(self.images("<!-- ![a](x.png) -->\ntext"), 0)
        self.assertEqual(self.images("<!--\n![a](x.png)\n-->\ntext"), 0)
        self.assertEqual(self.images("an <imgx> tag and a bang! [not](x.png)"), 0)

    def test_image_lines_add_no_words(self) -> None:
        text = "word one\n\n![alt words here](x.png)\n\n<img src=\"y.png\" alt=\"more words\">\n"
        self.assertEqual(guard.parse_markdown(text).words, 2)

    def test_html_images(self) -> None:
        self.assertEqual(self.images('<p><img src="a.png"></p><figure><img src="b.png"/></figure>', "html"), 2)
        self.assertEqual(self.images('<pre>&lt;img src="a.png"&gt;</pre><pre><img src="x"></pre>', "html"), 0)
        self.assertEqual(self.images("<p>![a](x.png)</p>", "html"), 0)
        self.assertEqual(self.images("<p>no images</p>", "html"), 0)

    def test_bounds_are_inclusive(self) -> None:
        one, two, three, four = (md_article("\n\n".join("![a](%d.png)" % i for i in range(n))) for n in (1, 2, 3, 4))
        self.assertEqual(rules(guard.check_article(one, "markdown")), ["images-min"])
        self.assertEqual(rules(guard.check_article(two, "markdown")), [])
        self.assertEqual(rules(guard.check_article(three, "markdown")), [])
        self.assertEqual(rules(guard.check_article(four, "markdown")), ["images-max"])
        self.assertEqual(rules(guard.check_article(four, "markdown", max_images=4)), [])
        self.assertEqual(rules(guard.check_article(one, "markdown", min_images=1)), [])
        self.assertEqual(rules(guard.check_article(md_article(), "markdown", min_images=0, max_images=0)), [])
        self.assertEqual(rules(guard.check_article(one, "markdown", min_images=0, max_images=0)), ["images-max"])

    def test_messages_and_summary(self) -> None:
        none = guard.check_article(md_article(), "markdown")
        self.assertEqual(rules(none), ["images-min"])
        self.assertEqual(none.findings[0].message, "0 images, min 2 (short by 2)")
        three = guard.check_article(md_article("![a](1.png)\n\n![b](2.png)\n\n![c](3.png)"), "markdown",
                                    min_images=1, max_images=5)
        self.assertEqual(three.findings, [])
        self.assertIn("images=3[1-5]", three.summary)

    def test_html_bounds(self) -> None:
        html = "<h1>T</h1><p>x</p>%s<h2>Next steps</h2>"
        self.assertEqual(rules(guard.check_article(html % '<img src="a">', "html")), ["images-min"])
        self.assertEqual(rules(guard.check_article(html % ('<img src="a">' * 2), "html")), [])
        self.assertEqual(rules(guard.check_article(html % ('<img src="a">' * 4), "html")), ["images-max"])


class HtmlRuleTests(unittest.TestCase):
    def html(self, body: str = "<p>Some words here.</p>", title: str = "<h1>A title</h1>",
             action: str = "<h2>Next steps</h2><p>Go.</p>") -> str:
        return "%s\n%s\n%s\n" % (title, body, action)

    def test_title_words_code_and_figures(self) -> None:
        text = self.html(
            body='<p>One two <strong>three</strong>four</p><pre><code>a b c\nd e f</code></pre>'
                 '<figure><img src="x.png" alt="a b c"><figcaption>cap tion</figcaption></figure><p>five six</p>'
                 '<img src="y.png" alt="more words">'
        )
        report = guard.check_article(text, "html")
        self.assertEqual(report.findings, [])  # two images: one in a figure, one bare
        # "One two threefour", "five six" and the "Next steps" / "Go." section: 3 + 2 + 3
        self.assertIn("words=8/1500", report.summary)
        self.assertIn("title=7/100", report.summary)

    def test_inline_markup_does_not_split_words_but_blocks_do(self) -> None:
        parsed = guard.parse_html("<h1>T</h1><p>abc<em>def</em></p><p>ghi</p><ul><li>jkl</li><li>mno</li></ul>")
        self.assertEqual(parsed.words, 4)

    def test_script_style_and_entities(self) -> None:
        parsed = guard.parse_html("<h1>T</h1><style>p { x: y }</style><script>var a = 1;</script><p>a &amp; b &lt; c</p>")
        self.assertEqual(parsed.words, 3)

    def test_code_blocks_and_lines(self) -> None:
        pre = "<pre>%s</pre>" % "\n".join("int a%d;" % i for i in range(15))
        self.assertEqual(article_rules(self.html(pre), "html"), [])
        pre16 = "<pre><code>%s</code></pre>" % "\n".join("int a%d;" % i for i in range(16))
        self.assertEqual(article_rules(self.html(pre16), "html"), ["code-lines"])
        self.assertEqual(article_rules(self.html("<pre>a</pre><p>x</p><pre>b</pre>"), "html"), ["code-blocks"])
        self.assertEqual(article_rules(self.html("<p>Inline <code>x()</code> is not a block.</p>"), "html"), [])
        self.assertEqual(article_rules(self.html("<pre>\na\n\nb\n</pre>"), "html"), [])
        self.assertEqual(article_rules(self.html("<pre>a<br>b<br/>c</pre>"), "html", max_code_lines=2), ["code-lines"])

    def test_unclosed_pre_still_counts_as_a_code_block(self) -> None:
        text = self.html("<pre>%s" % "\n".join("int a%d;" % i for i in range(16)))
        # an unclosed <pre> swallows the rest of the file, the next-step section included
        self.assertEqual(article_rules(text, "html"), ["code-lines", "action-heading"])

    def test_title_forbidden_and_missing(self) -> None:
        self.assertEqual(article_rules(self.html(title="<h1>The <em>Observer</em> way</h1>"), "html",
                                       forbid_title=["observer"]), ["title-forbidden"])
        self.assertEqual(article_rules(self.html(title=""), "html"), ["title"])
        self.assertEqual(article_rules(self.html(title="<h1>%s</h1>" % ("t" * 101)), "html"), ["title-length"])
        self.assertEqual(article_rules(self.html(title="<h1>&amp;&amp;</h1>"), "html"), [])

    def test_action_heading_in_any_heading_level(self) -> None:
        self.assertEqual(article_rules(self.html(action="<h3>What is next step?</h3>"), "html"), [])
        self.assertEqual(article_rules(self.html(action="<p>Next steps</p>"), "html"), ["action-heading"])
        self.assertEqual(article_rules(self.html(title="<h1>Next steps</h1>", action=""), "html"), ["action-heading"])

    def test_leftover_markdown_links_in_html(self) -> None:
        report = guard.check_article(self.html("<p>a</p>\n<p>[x](https://e.org) and [y](http://e.org)</p>"), "html", min_images=0)
        self.assertEqual(rules(report), ["markdown-link"])
        self.assertEqual(report.findings[0].line, 3)
        self.assertIn("2 leftover", report.findings[0].message)
        self.assertEqual(article_rules(self.html('<p><a href="https://e.org">x</a> ](not a link)</p>'), "html"), [])

    def test_format_detection(self) -> None:
        detect = guard.detect_format
        self.assertEqual(detect("a.html", "x"), "html")
        self.assertEqual(detect("a.HTM", "x"), "html")
        self.assertEqual(detect("a.html.txt", "x"), "html")
        self.assertEqual(detect("a.md", "<p>x</p>"), "markdown")
        self.assertEqual(detect("a.md.txt", "<p>x</p>"), "markdown")
        self.assertEqual(detect("a.markdown", "x"), "markdown")
        self.assertEqual(detect("draft", "<h1>T</h1>"), "html")
        self.assertEqual(detect("draft.txt", "# T\n\nplain text"), "markdown")
        self.assertEqual(detect("draft", "# T\n\na < b and c > d"), "markdown")


class CliTests(unittest.TestCase):
    def test_no_arguments_and_unknown_subcommand_are_usage_errors(self) -> None:
        code, _, err = run_main()
        self.assertEqual(code, 2)
        self.assertIn("usage", err.lower())
        self.assertEqual(run_main("poster", "x.txt")[0], 2)
        self.assertEqual(run_main("post")[0], 2)
        self.assertEqual(run_main("article")[0], 2)

    def test_help_exits_zero(self) -> None:
        for argv in (("--help",), ("post", "--help"), ("article", "--help")):
            with self.subTest(argv=argv):
                code, out, _ = run_main(*argv)
                self.assertEqual(code, 0)
                self.assertIn("usage:", out)
        self.assertIn("--require-link", run_main("post", "--help")[1])
        self.assertIn("--action-heading", run_main("article", "--help")[1])
        self.assertIn("--min-images", run_main("article", "--help")[1])
        self.assertIn("--max-images", run_main("article", "--help")[1])

    def test_missing_file_is_an_io_error(self) -> None:
        for command in ("post", "article"):
            code, out, err = run_main(command, str(FIXTURES / "does-not-exist.txt"))
            self.assertEqual((code, out), (2, ""))
            self.assertIn("error:", err)

    def test_empty_and_undecodable_files_are_io_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "empty.txt"
            empty.write_text("  \n", encoding="utf-8")
            binary = Path(tmp) / "binary.txt"
            binary.write_bytes(b"\xff\xfe\x00\x80")
            for command in ("post", "article"):
                self.assertEqual(run_main(command, str(empty))[0], 2)
                self.assertEqual(run_main(command, str(binary))[0], 2)
            self.assertEqual(run_main("post", tmp)[0], 2)

    def test_bad_options_are_usage_errors(self) -> None:
        post = str(fixture("post-pass.txt"))
        article = str(fixture("article-pass.md.txt"))
        bad = [
            ("post", post, "--max-chars", "many"),
            ("post", post, "--max-chars", "-1"),
            ("post", post, "--alias", "Java"),
            ("post", post, "--alias", "=java"),
            ("post", post, "--alias", "Java="),
            ("post", post, "--forbid", ""),
            ("post", post, "--require-link", " "),
            ("post", post, "--nope"),
            ("article", article, "--action-heading", "("),
            ("article", article, "--forbid-title", ""),
            ("article", article, "--max-words", "1.5"),
            ("article", article, "--min-images", "-1"),
            ("article", article, "--max-images", "many"),
            ("article", article, "--min-images", "4", "--max-images", "3"),
            ("article", article, "--title", ""),
        ]
        for argv in bad:
            with self.subTest(argv=argv):
                code, out, err = run_main(*argv)
                self.assertEqual((code, out), (2, ""))
                self.assertIn("usage", err.lower())

    def test_options_override_the_defaults(self) -> None:
        post = str(fixture("post-pass.txt"))
        self.assertEqual(run_main("post", post, "--max-chars", "1041")[0], 1)
        self.assertEqual(run_main("post", post, "--max-chars", "1042")[0], 0)
        self.assertEqual(run_main("post", post, "--max-hashtags", "3")[0], 1)
        self.assertEqual(run_main("post", post, "--hook-chars", "101")[0], 1)
        article = str(fixture("article-pass.md.txt"))
        self.assertEqual(run_main("article", article, "--max-words", "298")[0], 1)
        self.assertEqual(run_main("article", article, "--max-code-lines", "12")[0], 1)
        self.assertEqual(run_main("article", article, "--max-code-blocks", "0")[0], 1)
        self.assertEqual(run_main("article", article, "--min-images", "3", "--max-images", "3")[0], 1)
        self.assertEqual(run_main("article", article, "--min-images", "0", "--max-images", "1")[0], 1)
        self.assertEqual(run_main("article", article, "--min-images", "1", "--max-images", "2")[0], 0)
        self.assertEqual(run_main("article", article, "--title", "T" * 101)[0], 1)

    def test_summary_is_printed_with_the_file_name(self) -> None:
        code, out, _ = run_main("article", str(fixture("article-pass.md.txt")))
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("ok: %s: article " % fixture("article-pass.md.txt")), out)

    def test_output_is_ascii_even_for_non_ascii_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            post = Path(tmp) / "caf\u00e9.txt"
            post.write_text("Caf\u00e9 \u2019\n\n#Caf\u00e9 #Nada", encoding="utf-8")
            code, out, _ = run_main("post", str(post), "--forbid", "caf\u00e9", "--require-link", "https://e.org/\u00e9")
            self.assertEqual(code, 1)
            self.assertIn("forbid", out)
            out.encode("ascii")
            article = Path(tmp) / "art\u00edculo.md"
            article.write_text("# Padr\u00e3o\n\ncorpo\n", encoding="utf-8")
            code, out, _ = run_main("article", str(article), "--forbid-title", "padr\u00e3o")
            self.assertEqual(code, 1)
            out.encode("ascii")

    def test_utf8_bom_and_crlf_are_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            post = Path(tmp) / "bom.txt"
            post.write_bytes(b"\xef\xbb\xbfJava hook.\r\n\r\nBody.\r\n\r\n#Java")
            code, out, _ = run_main("post", str(post))
            self.assertEqual(code, 0, out)
            self.assertIn("hook=10/200", out)


class DefaultsTests(unittest.TestCase):
    """What applies when neither a flag nor a profile sets a limit."""

    def test_documented_defaults(self) -> None:
        self.assertEqual(guard.DEFAULTS, {
            "post": {"max_chars": 1300, "max_hashtags": 5, "hook_chars": 200},
            "article": {"max_words": 1500, "max_code_blocks": 1, "max_code_lines": 15, "min_images": 2, "max_images": 3},
        })
        self.assertEqual((guard.TITLE_MAX_CHARS, guard.SUBTITLE_MAX_CHARS), (100, 140))

    def test_cli_applies_the_defaults_and_prints_them(self) -> None:
        code, out, _ = run_main("post", str(fixture("post-pass.txt")))
        self.assertEqual(code, 0, out)
        for measured in ("chars=1042/1300", "hashtags=4/5", "hook=102/200"):
            self.assertIn(measured, out)
        code, out, _ = run_main("article", str(fixture("article-pass.md.txt")))
        self.assertEqual(code, 0, out)
        for measured in ("words=299/1500", "code_blocks=1/1", "longest_code=13/15", "images=2[2-3]"):
            self.assertIn(measured, out)

    def test_default_word_limit_is_1500_and_inclusive(self) -> None:
        def words(n: int) -> "List[str]":
            # the "Next steps" section of md_article adds 3 words ("Next", "steps", "Go.")
            return article_rules(md_article(" ".join(["word"] * (n - 3))), min_images=0)
        self.assertEqual(words(1500), [])
        self.assertEqual(words(1501), ["words"])

    def test_default_hook_limit_is_200_and_inclusive(self) -> None:
        self.assertEqual(rules(guard.check_post("h" * 200 + "\n\nbody")), [])
        self.assertEqual(rules(guard.check_post("h" * 201 + "\n\nbody")), ["hook"])

    def test_the_over_budget_fixture_sits_between_the_profile_limit_and_the_default(self) -> None:
        name = "article-over-budget.md.txt"
        self.assertEqual(run_main("article", str(fixture(name)))[0], 0)  # 1346 words, default 1500
        self.assertEqual(run_main("article", str(fixture(name)), "--max-words", "1300")[0], 1)
        self.assertEqual(run_main("article", str(fixture(name)), "--profile", str(PROFILE))[0], 1)  # profile 1300


class FirstJsonBlockTests(unittest.TestCase):
    def block(self, text: str) -> "Optional[tuple]":
        return guard.first_json_block(text)

    def test_the_first_json_block_with_its_line(self) -> None:
        self.assertEqual(self.block('# P\n\n```json\n{"a": 1}\n```\n'), (3, '{"a": 1}'))
        self.assertEqual(self.block('```json\n{"a": 1}\n```\n```json\n{"b": 2}\n```\n'), (1, '{"a": 1}'))
        self.assertEqual(self.block('```json\n{\n  "a": 1\n}\n```'), (1, '{\n  "a": 1\n}'))

    def test_fence_forms(self) -> None:
        for text in ('~~~json\n{}\n~~~', '```JSON\n{}\n```', '```json title="x"\n{}\n```', '````json\n{}\n````',
                     '   ```json\n{}\n   ```', '```json\r\n{}\r\n```\r\n', '```json\n{}\n`````'):
            with self.subTest(text=text):
                found = self.block(text)
                self.assertIsNotNone(found)
                self.assertEqual(found[1].strip(), "{}")

    def test_blocks_that_are_not_json_are_skipped_whole(self) -> None:
        self.assertEqual(self.block('```text\n{"x": 1}\n```\n\n```json\n{"a": 1}\n```\n'), (5, '{"a": 1}'))
        self.assertEqual(self.block('```\n{}\n```\n~~~json\n{"a": 1}\n~~~\n'), (4, '{"a": 1}'))
        self.assertIsNone(self.block('````text\n```json\n{}\n```\n````\n'))
        self.assertIsNone(self.block('```jsonc\n{}\n```\n'))
        self.assertIsNone(self.block('```\n{}\n```\n'))
        self.assertIsNone(self.block('plain text with `json` and { } only\n'))
        self.assertIsNone(self.block('```text\nnever closed\n```json\n{}\n'))

    def test_a_shorter_or_different_closing_fence_does_not_close(self) -> None:
        self.assertEqual(self.block('````json\n{}\n```\n{"a": 1}\n````\n'), (1, '{}\n```\n{"a": 1}'))
        self.assertEqual(self.block('```json\n{}\n~~~\n```\n'), (1, '{}\n~~~'))
        self.assertEqual(self.block('```json {"inline"}\n{}\n```\n'), (1, '{}'))

    def test_a_json_block_that_is_never_closed_is_an_input_error(self) -> None:
        with self.assertRaises(guard.InputError) as caught:
            self.block('intro\n```json\n{}\n')
        self.assertIn("line 2", str(caught.exception))
        self.assertIn("never closed", str(caught.exception))

    def test_an_info_string_with_a_backtick_does_not_open_a_fence(self) -> None:
        self.assertIsNone(self.block('```json`x`\n{}\n```\n'))


class ProfileTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)

    def profile(self, settings: object = None, text: Optional[str] = None, name: str = "profile.md") -> str:
        body = text if text is not None else "# Profile\n\nProse.\n\n```json\n%s\n```\n" % json.dumps(settings, indent=2)
        path = self.tmp / name
        path.write_bytes(body.encode("utf-8"))
        return str(path)

    def post(self, *extra: str, name: str = "post-pass.txt") -> "tuple[int, str, str]":
        return run_main("post", str(fixture(name)), *extra)

    def article(self, *extra: str, name: str = "article-pass.md.txt") -> "tuple[int, str, str]":
        return run_main("article", str(fixture(name)), *extra)

    def failed_rules(self, out: str) -> "List[str]":
        return sorted(line.split(": ")[2] for line in out.splitlines() if line.startswith("violation: "))

    # -- values are applied

    def test_the_example_fixture_holds_the_documented_settings(self) -> None:
        text = PROFILE.read_text(encoding="utf-8")
        self.assertEqual(guard.parse_profile(text, "post"), {"max_chars": 1300, "max_hashtags": 5, "hook_chars": 200})
        self.assertEqual(guard.parse_profile(text, "article"), {
            "max_words": 1300, "max_code_blocks": 1, "max_code_lines": 15, "min_images": 2, "max_images": 3})

    def test_post_limits_come_from_the_profile(self) -> None:
        strict = self.profile({"post": {"max_chars": 500, "max_hashtags": 3, "hook_chars": 100}})
        code, out, err = self.post("--profile", strict)
        self.assertEqual((code, err), (1, ""), out)
        self.assertEqual(self.failed_rules(out), ["chars", "hashtags", "hook"])
        self.assertIn("1042 characters, max 500", out)
        self.assertIn("4 hashtags, max 3", out)
        self.assertIn("hook is 102 characters, max 100", out)

    def test_post_fixtures_pass_under_a_relaxed_profile(self) -> None:
        relaxed = self.profile({"post": {"max_hashtags": 6, "hook_chars": 217}})
        self.assertEqual(self.post("--profile", relaxed, name="post-six-hashtags.txt")[0], 0)
        self.assertEqual(self.post("--profile", relaxed, name="post-long-hook.txt")[0], 0)
        code, out, _ = self.post("--profile", relaxed)
        self.assertEqual(code, 0, out)
        self.assertIn("hashtags=4/6", out)
        self.assertIn("hook=102/217", out)

    def test_article_limits_come_from_the_profile(self) -> None:
        strict = self.profile({"article": {"max_words": 100, "max_code_blocks": 0, "max_code_lines": 5,
                                           "min_images": 3, "max_images": 3}})
        code, out, err = self.article("--profile", strict)
        self.assertEqual((code, err), (1, ""), out)
        self.assertEqual(self.failed_rules(out), ["code-blocks", "code-lines", "images-min", "words"])
        self.assertIn("299 words, max 100", out)
        self.assertIn("code block 1 has 13 lines, max 5", out)
        self.assertIn("2 images, min 3", out)

    def test_article_fixtures_pass_under_a_relaxed_profile(self) -> None:
        relaxed = self.profile({"article": {"max_words": 1500, "max_code_blocks": 2, "min_images": 1, "max_images": 4}})
        for name in ("article-over-budget.md.txt", "article-two-code-blocks.md.txt", "article-too-few-images.md.txt",
                     "article-too-many-images.md.txt"):
            with self.subTest(name=name):
                code, out, _ = self.article("--profile", relaxed, name=name)
                self.assertEqual(code, 0, out)
        out = self.article("--profile", relaxed)[1]
        self.assertIn("words=299/1500", out)
        self.assertIn("code_blocks=1/2", out)
        self.assertIn("images=2[1-4]", out)

    def test_limits_of_zero_are_valid(self) -> None:
        zero = self.profile({"article": {"max_code_blocks": 0, "min_images": 0, "max_images": 0}})
        code, out, _ = self.article("--profile", zero, name="article-pass.html.txt")
        self.assertEqual(code, 1)
        self.assertEqual(self.failed_rules(out), ["code-blocks", "images-max"])

    # -- flags override the profile, the profile overrides the defaults

    def test_a_flag_overrides_the_profile_in_both_directions(self) -> None:
        tight = self.profile({"post": {"max_chars": 100}})
        self.assertEqual(self.post("--profile", tight)[0], 1)
        self.assertEqual(self.post("--profile", tight, "--max-chars", "5000")[0], 0)
        self.assertEqual(self.post("--profile", self.profile({"post": {"max_chars": 5000}}), "--max-chars", "100")[0], 1)
        wide = self.profile({"article": {"max_words": 100}})
        self.assertEqual(self.article("--profile", wide)[0], 1)
        self.assertEqual(self.article("--profile", wide, "--max-words", "299")[0], 0)
        self.assertEqual(self.article("--profile", wide, "--max-words", "298")[0], 1)

    def test_a_flag_equal_to_the_default_still_overrides_the_profile(self) -> None:
        wide = self.profile({"article": {"max_words": 100}, "post": {"hook_chars": 10}})
        self.assertEqual(self.article("--profile", wide, "--max-words", "1500")[0], 0)
        self.assertEqual(self.post("--profile", wide, "--hook-chars", "200")[0], 0)

    def test_a_flag_replaces_only_its_own_key(self) -> None:
        tight = self.profile({"post": {"max_chars": 100, "max_hashtags": 1}})
        code, out, _ = self.post("--profile", tight, "--max-chars", "5000")
        self.assertEqual(self.failed_rules(out), ["hashtags"])
        both = self.profile({"article": {"min_images": 3, "max_words": 100}})
        code, out, _ = self.article("--profile", both, "--min-images", "2")
        self.assertEqual(self.failed_rules(out), ["words"])

    def test_keys_the_profile_leaves_out_use_the_defaults(self) -> None:
        only_tags = self.profile({"post": {"max_hashtags": 10}})
        code, out, _ = self.post("--profile", only_tags, name="post-long-hook.txt")
        self.assertEqual(self.failed_rules(out), ["hook"])  # the default 200 still applies
        self.assertIn("max 200", out)
        for settings in ({}, {"post": {}}, {"article": {}}, {"post": None}):
            with self.subTest(settings=settings):
                code, out, _ = self.post("--profile", self.profile(settings))
                self.assertEqual(code, 0, out)
                self.assertIn("chars=1042/1300 hashtags=4/5 hook=102/200", out)
        code, out, _ = self.article("--profile", self.profile({"post": {"max_chars": 1}}), name="article-over-budget.md.txt")
        self.assertEqual(code, 0, out)  # another section sets nothing for the article: default 1500 words

    def test_unknown_keys_and_sections_are_ignored(self) -> None:
        text = self.profile({"extra": [1, 2], "forbid_title_terms_from": "pattern name", "linkedin": {"max_chars": 1},
                             "post": {"max_chars": 5000, "colour": "red", "max_chars_soft": -1, "Max_Chars": "x"},
                             "article": {"max_words": 1500, "words": "many"}})
        code, out, err = self.post("--profile", text)
        self.assertEqual((code, err), (0, ""), out)
        self.assertIn("chars=1042/5000", out)
        self.assertEqual(self.article("--profile", text)[0], 0)

    def test_only_the_section_of_the_subcommand_is_read(self) -> None:
        bad_article = self.profile({"post": {"max_chars": 5000}, "article": {"max_words": "many"}})
        self.assertEqual(self.post("--profile", bad_article)[0], 0)
        self.assertEqual(self.article("--profile", bad_article)[0], 2)
        bad_post = self.profile({"post": "oops", "article": {"max_words": 1500}})
        self.assertEqual(self.post("--profile", bad_post)[0], 2)
        self.assertEqual(self.article("--profile", bad_post)[0], 0)

    def test_the_first_json_block_wins_and_other_blocks_are_skipped(self) -> None:
        code, out, _ = self.post("--profile", str(PROFILE))
        self.assertEqual(code, 0, out)
        self.assertIn("chars=1042/1300", out)  # not the later block's max_chars of 1
        text = "````text\n```json\n{\"post\": {\"max_chars\": 1}}\n```\n````\n\n```json\n{\"post\": {\"max_chars\": 5000}}\n```\n"
        self.assertIn("chars=1042/5000", self.post("--profile", self.profile(text=text))[1])

    def test_bom_crlf_and_a_profile_without_a_trailing_newline(self) -> None:
        text = "\ufeff# P\r\n\r\n```json\r\n{\"post\": {\"max_chars\": 4000}}\r\n```"
        code, out, _ = self.post("--profile", self.profile(text=text))
        self.assertEqual(code, 0, out)
        self.assertIn("chars=1042/4000", out)

    # -- errors are exit 2 with a message that names the profile

    def assert_profile_error(self, path: str, *needles: str, command: str = "post") -> None:
        extra = (path,)
        code, out, err = (self.post("--profile", *extra) if command == "post" else self.article("--profile", *extra))
        self.assertEqual((code, out), (2, ""), err)
        self.assertTrue(err.startswith("error: "), err)
        self.assertEqual(err.count("\n"), 1, err)
        for needle in needles:
            self.assertIn(needle, err)

    def test_malformed_json_is_exit_2_with_the_line(self) -> None:
        trailing = self.profile(text='# P\n\n```json\n{\n  "post": {"max_chars": 1,}\n}\n```\n')
        self.assert_profile_error(trailing, "profile ", trailing, "malformed json", "line 5")
        self.assert_profile_error(trailing, "malformed json", "line 5", command="article")
        self.assert_profile_error(str(BAD_PROFILE), "malformed json", "line 7")
        for broken in ("not json", "", "{", '{"post": {"max_chars": 1}} trailing', "{'post': {}}", '{"post": {"max_chars": 01}}'):
            with self.subTest(broken=broken):
                self.assert_profile_error(self.profile(text="```json\n%s\n```\n" % broken), "malformed json")

    def test_no_json_block_is_exit_2(self) -> None:
        for text in ("# Profile\n\nProse only.\n", "```text\n{}\n```\n", "```\n{}\n```\n", "`json` {}\n"):
            with self.subTest(text=text):
                self.assert_profile_error(self.profile(text=text), "no fenced json block")

    def test_unclosed_json_block_is_exit_2(self) -> None:
        self.assert_profile_error(self.profile(text="# P\n```json\n{}\n"), "never closed", "line 2")

    def test_json_that_is_not_an_object_is_exit_2(self) -> None:
        for body in ("[]", "[1]", "5", '"post"', "null", "true"):
            with self.subTest(body=body):
                self.assert_profile_error(self.profile(text="```json\n%s\n```\n" % body), "must be an object")

    def test_a_section_that_is_not_an_object_is_exit_2(self) -> None:
        for value in ("[]", "5", '"x"', "true", "[1]"):
            with self.subTest(value=value):
                self.assert_profile_error(self.profile(text='```json\n{"post": %s}\n```\n' % value), '"post" must be an object')
                self.assert_profile_error(self.profile(text='```json\n{"article": %s}\n```\n' % value),
                                          '"article" must be an object', command="article")

    def test_wrong_values_are_exit_2_and_name_the_key(self) -> None:
        for value in ('"1300"', "1.5", "1300.0", "-1", "true", "false", "null", "[]", "{}", "1e3"):
            with self.subTest(value=value):
                path = self.profile(text='```json\n{"post": {"max_chars": %s}}\n```\n' % value)
                self.assert_profile_error(path, '"post.max_chars" must be a whole number of 0 or more')
        for key in guard.DEFAULTS["article"]:
            with self.subTest(key=key):
                path = self.profile(text='```json\n{"article": {"%s": "x"}}\n```\n' % key)
                self.assert_profile_error(path, '"article.%s"' % key, command="article")

    def test_unusable_profile_files_are_exit_2(self) -> None:
        blank = self.tmp / "blank.md"
        blank.write_text(" \n\n", encoding="utf-8")
        utf16 = self.tmp / "utf16.md"
        utf16.write_bytes("```json\n{}\n```\n".encode("utf-16"))
        self.assert_profile_error(str(self.tmp / "missing.md"), "cannot read profile")
        self.assert_profile_error(str(self.tmp), "cannot read profile")
        self.assert_profile_error(str(blank), "empty profile")
        self.assert_profile_error(str(utf16), "not valid UTF-8")
        code, out, err = self.post("--profile", "")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("usage", err.lower())
        code, out, err = self.post("--profile")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("usage", err.lower())

    def test_a_profile_error_wins_over_nothing_else_is_printed(self) -> None:
        code, out, err = run_main("article", str(fixture("article-over-budget.md.txt")), "--profile", str(BAD_PROFILE))
        self.assertEqual((code, out), (2, ""))  # no verdict from defaults is printed
        self.assertIn("malformed json", err)

    def test_image_bounds_from_the_profile_and_flags_must_agree(self) -> None:
        crossed = self.profile({"article": {"min_images": 3, "max_images": 2}})
        code, out, err = self.article("--profile", crossed)
        self.assertEqual((code, out), (2, ""))
        self.assertIn("minimum images (3) is larger than maximum images (2)", err)
        self.assertIn("usage", err.lower())
        self.assertEqual(self.article("--profile", crossed, "--max-images", "3")[0], 1)  # 2 images, min 3
        self.assertEqual(self.article("--profile", crossed, "--min-images", "2")[0], 0)
        self.assertEqual(self.article("--profile", self.profile({"article": {"min_images": 5}}))[0], 2)  # default max 3
        self.assertEqual(self.article("--profile", self.profile({"article": {"max_images": 1}}))[0], 2)  # default min 2

    def test_error_output_stays_ascii_for_a_non_ascii_profile_path(self) -> None:
        path = self.profile(text="```json\n{oops}\n```\n", name="perfil-\u00e9.md")
        code, out, err = self.post("--profile", path)
        self.assertEqual((code, out), (2, ""))
        err.encode("ascii")
        self.assertIn("\\xe9", err)

    def test_help_documents_the_profile_for_both_subcommands(self) -> None:
        for command, key in (("post", "post.max_chars"), ("article", "article.max_words")):
            with self.subTest(command=command):
                code, out, _ = run_main(command, "--help")
                self.assertEqual(code, 0)
                self.assertIn("--profile PATH", out)
                self.assertIn("profile key " + key, " ".join(out.split()))
                self.assertNotIn("1300 words", out)


class InlineCodeTests(unittest.TestCase):
    def parse(self, text: str) -> "guard.Parsed":
        return guard.parse_markdown(text)

    def test_inline_code_counts_as_words_and_keeps_its_angle_brackets(self) -> None:
        self.assertEqual(self.parse("Use `Map<String, List<Integer>>` here").words, 4)
        self.assertEqual(self.parse("Use ``a ` b`` and `<img src=x>` ok").words, 7)
        self.assertEqual(self.parse("See [`List<String>`](https://example.org/a) now").words, 3)

    def test_inline_code_is_not_an_image(self) -> None:
        text = "Write `<img src=x>` and `![a](b.png)` as code, then ![real](r.png)"
        self.assertEqual(self.parse(text).images, 1)

    def test_an_unmatched_backtick_is_plain_text(self) -> None:
        self.assertEqual(self.parse("A `unclosed tick and more").words, 5)
        self.assertEqual(self.parse("A ![alt](a.png) and `unclosed").images, 1)

    def test_a_fence_line_is_not_an_inline_code_span(self) -> None:
        parsed = self.parse("text\n\n```java\nint a;\n```\n\nmore `x` words\n")
        self.assertEqual([b.lines for b in parsed.code_blocks], [1])
        self.assertEqual(parsed.words, 1 + 3)


class MiscRuleTests(unittest.TestCase):
    def test_hashtag_edge_cases_through_the_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            post = Path(tmp) / "post.txt"
            post.write_text(
                "Java 25 and C# differ. It&#39;s fine, say &#x27;ok&#x27;.\n\n"
                "See https://example.org/a#frag#two and www.example.org/b#c and (https://example.org/#Java).\n\n"
                "Issue #12 and # alone and ##double.\n\n#Java\n", encoding="utf-8")
            code, out, err = run_main("post", str(post))
            self.assertEqual((code, err), (0, ""), out)
            self.assertIn("hashtags=1/5", out)
            self.assertIn("topics=1/1", out)

    def test_required_link_with_parentheses_and_trailing_punctuation(self) -> None:
        wiki = "https://en.wikipedia.org/wiki/Foo_(bar)"
        self.assertEqual(guard.check_post("Read " + wiki + ".\n", require_links=[wiki]).findings, [])
        self.assertEqual(guard.check_post("Read (" + wiki + ")\n", require_links=[wiki]).findings, [])
        self.assertEqual(guard.check_post("Read https://example.org/a.\n", require_links=["https://example.org/a."]).findings, [])
        self.assertEqual(rules(guard.check_post("Read https://example.org/ab.\n", require_links=["https://example.org/a"])), ["link"])

    def test_windows_style_paths(self) -> None:
        self.assertEqual(guard.detect_format("G:\\opt\\code\\study\\medium-v2.md", "x"), "markdown")
        self.assertEqual(guard.detect_format("C:\\drafts\\Article.HTML", "x"), "html")
        self.assertEqual(guard.detect_format("C:\\drafts\\article.html.txt", "x"), "html")
        out = io.StringIO()
        guard.write_report("G:\\opt\\post.txt", guard.Report([guard.Finding("chars", "too long"), guard.Finding("fence", "open", 7)], ""), out)
        self.assertEqual(out.getvalue().splitlines(), ["violation: G:\\opt\\post.txt: chars: too long",
                                                       "violation: G:\\opt\\post.txt:7: fence: open"])

    def test_exit_codes(self) -> None:
        self.assertEqual(run_main("post", str(fixture("post-pass.txt")))[0], 0)
        self.assertEqual(run_main("post", str(fixture("post-six-hashtags.txt")))[0], 1)
        self.assertEqual(run_main("article", str(fixture("article-pass.md.txt")))[0], 0)
        self.assertEqual(run_main("article", str(fixture("article-too-many-images.md.txt")))[0], 1)
        self.assertEqual(run_main("post", str(fixture("does-not-exist.txt")))[0], 2)
        self.assertEqual(run_main("article", "--nope")[0], 2)
        self.assertEqual(run_main("--help")[0], 0)

    def test_findings_never_print_a_summary_and_a_pass_never_prints_a_violation(self) -> None:
        for name in sorted(p.name for p in FIXTURES.glob("post-*.txt")):
            code, out, _ = run_post(name)
            self.assertEqual(out.startswith("ok: "), code == 0, name)
            self.assertEqual("violation: " in out, code == 1, name)
        for name in sorted(p.name for p in FIXTURES.glob("article-*.txt")):
            code, out, _ = run_article(name)
            self.assertEqual(out.startswith("ok: "), code == 0, name)
            self.assertEqual("violation: " in out, code == 1, name)

    def test_every_fixture_has_the_expected_verdict(self) -> None:
        expected = {
            "post-pass.txt": [], "post-six-hashtags.txt": ["hashtags"], "post-long-hook.txt": ["hook"],
            "post-missing-link.txt": ["link"], "post-unbacked-hashtag.txt": ["topic"],
            "article-pass.md.txt": [], "article-pass.html.txt": [], "article-over-budget.md.txt": ["words"],
            "article-two-code-blocks.md.txt": ["code-blocks"], "article-indented-code.md.txt": ["code-lines"],
            "article-no-next-step.md.txt": ["action-heading"], "article-pattern-in-title.md.txt": ["title-forbidden"],
            "article-too-few-images.md.txt": ["images-min"], "article-too-many-images.md.txt": ["images-max"],
            "article-md-link-in-html.html.txt": ["markdown-link"],
        }
        on_disk = sorted(p.name for p in FIXTURES.iterdir() if not p.name.startswith("profile-"))
        self.assertEqual(on_disk, sorted(expected), "a fixture has no expected verdict, or a verdict has no fixture")
        for name, want in expected.items():
            with self.subTest(name=name):
                code, out, err = run_post(name) if name.startswith("post-") else run_article(name)
                got = sorted(line.split(": ")[2] for line in out.splitlines() if line.startswith("violation: "))
                self.assertEqual((got, err), (want, ""), out)
                self.assertEqual(code, 1 if want else 0)


class SourceGuardTests(unittest.TestCase):
    """The script must run on a bare Python 3.9 on any platform."""

    def setUp(self) -> None:
        self.source = SCRIPT.read_text(encoding="utf-8")

    def test_the_syntax_is_python_39(self) -> None:
        ast.parse(self.source, filename=str(SCRIPT), feature_version=(3, 9))

    def test_only_the_standard_library_is_imported(self) -> None:
        allowed = {"__future__", "argparse", "json", "re", "sys", "html", "pathlib", "typing"}
        imported = set()
        for node in ast.walk(ast.parse(self.source)):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertLessEqual(imported, allowed)

    def test_the_source_is_ascii(self) -> None:
        self.source.encode("ascii")

    def test_the_script_runs_as_a_program_with_the_documented_exit_codes(self) -> None:
        def run(*argv: str, env: "Optional[Dict[str, str]]" = None) -> "subprocess.CompletedProcess[str]":
            return subprocess.run([sys.executable, "-I", str(SCRIPT), *argv], capture_output=True, text=True,
                                  encoding="ascii", env=env, timeout=60)
        ok = run("post", str(fixture("post-pass.txt")), "--profile", str(PROFILE))
        self.assertEqual((ok.returncode, ok.stderr), (0, ""))
        self.assertTrue(ok.stdout.startswith("ok: "))
        bad = run("post", str(fixture("post-six-hashtags.txt")))
        self.assertEqual((bad.returncode, bad.stderr), (1, ""))
        self.assertTrue(bad.stdout.startswith("violation: "))
        usage = run("post", str(fixture("post-pass.txt")), "--profile", str(BAD_PROFILE))
        self.assertEqual((usage.returncode, usage.stdout), (2, ""))
        self.assertIn("error:", usage.stderr)
        self.assertEqual(run("--help").returncode, 0)

    def test_a_legacy_console_encoding_cannot_break_the_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            name = Path(tmp) / "post-\u4e2d.txt"
            try:
                name.write_text("Hook \u4e2d.\n\n#Java\n", encoding="utf-8")
            except (OSError, UnicodeError):
                self.skipTest("the file system cannot hold this name")
            env = dict(os.environ, PYTHONIOENCODING="cp1252:strict")
            done = subprocess.run([sys.executable, "-I", str(SCRIPT), "post", str(name), "--forbid", "\u4e2d"],
                                  capture_output=True, env=env, timeout=60)
            self.assertEqual(done.returncode, 1, done.stderr)
            self.assertEqual(done.stderr, b"")
            done.stdout.decode("ascii")
            self.assertIn(b"forbid", done.stdout)


if __name__ == "__main__":
    unittest.main()
