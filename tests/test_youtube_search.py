from __future__ import annotations

import contextlib
import http.client
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = ROOT / "skills" / "youtube-video-curation"
SCRIPT = SKILL_DIR / "scripts" / "youtube_search.py"
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "youtube-video-curation" / "results.html"
SPEC = importlib.util.spec_from_file_location("youtube_search", SCRIPT)
assert SPEC and SPEC.loader
yt = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = yt
SPEC.loader.exec_module(yt)

ID_A, ID_B, ID_C, ID_D, ID_E = ("AAAAAAAAAAA", "BBBBBBBBBBB", "CCCCCCCCCCC", "DDDDDDDDDDD", "EEEEEEEEEEE")


def fake_response(body, url="https://www.youtube.com/results"):
    """A urlopen() result. read(n) honours its size argument like a real socket does."""
    data = body.encode("utf-8") if isinstance(body, str) else body
    response = mock.MagicMock()
    response.read.side_effect = lambda size=-1: data if size is None or size < 0 else data[:size]
    response.geturl.return_value = url
    response.__enter__.return_value = response
    return response


def page_with(*renderers):
    """A minimal results page whose ytInitialData holds the given videoRenderer dicts."""
    data = {"contents": [{"videoRenderer": r} for r in renderers]}
    return "<script>var ytInitialData = " + json.dumps(data) + ";</script>"


def renderer(video_id="KKKKKKKKKKK", **overrides):
    base = {"videoId": video_id, "title": {"simpleText": "A title"}}
    base.update(overrides)
    return base


def http_error(code):
    return urllib.error.HTTPError("https://example.com/x", code, "status", {}, None)


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = yt.main(list(argv))
    return code, out.getvalue(), err.getvalue()


def item(video_id="XXXXXXXXXXX", **overrides):
    base = {
        "id": video_id,
        "title": "Some Pattern Tutorial",
        "channel": "Channel One",
        "views": 100000,
        "views_text": "100,000 views",
        "published": "1 year ago",
        "length": "10:00",
        "length_seconds": 600,
        "description": "",
        "is_short": False,
        "is_live": False,
        "is_playlist": False,
        "url": "https://www.youtube.com/watch?v=" + video_id,
    }
    base.update(overrides)
    return base


class NumberParsingTests(unittest.TestCase):
    def test_parse_views(self) -> None:
        cases = {
            "1,234,567 views": 1234567,
            "1 view": 1,
            "No views": 0,
            "9.8M views": 9800000,
            "12K views": 12000,
            "1.5 million views": 1500000,
            "1,204 watching": 1204,
            "": None,
            "Premieres soon": None,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(yt.parse_views(text), expected)
        self.assertIsNone(yt.parse_views(None))

    def test_parse_length(self) -> None:
        self.assertEqual(yt.parse_length("14:32"), 872)
        self.assertEqual(yt.parse_length("0:45"), 45)
        self.assertEqual(yt.parse_length("1:02:03"), 3723)
        for bad in ("", "LIVE", "12", "1:99", "a:b", "1:2:3:4", None):
            with self.subTest(bad=bad):
                self.assertIsNone(yt.parse_length(bad))

    def test_parse_age_years(self) -> None:
        self.assertAlmostEqual(yt.parse_age_years("3 years ago"), 3.0)
        self.assertAlmostEqual(yt.parse_age_years("1 year ago"), 1.0)
        self.assertAlmostEqual(yt.parse_age_years("6 months ago"), 0.5)
        self.assertAlmostEqual(yt.parse_age_years("Streamed 2 weeks ago"), 14 / 365)
        self.assertAlmostEqual(yt.parse_age_years("4 days ago"), 4 / 365)
        self.assertIsNone(yt.parse_age_years("Just now"))
        self.assertIsNone(yt.parse_age_years(""))

    def test_video_id_validation(self) -> None:
        self.assertTrue(yt.is_valid_video_id("AAAAAAAAAAA"))
        self.assertTrue(yt.is_valid_video_id("a-_0Z9b-_cD"))
        for bad in ("short", "AAAAAAAAAAAA", "AAAAAAAAAA!", "AAAAAAAAAAA\n", "", None, 12345678901):
            with self.subTest(bad=bad):
                self.assertFalse(yt.is_valid_video_id(bad))


class ExtractionTests(unittest.TestCase):
    def test_var_form(self) -> None:
        html = '<script>var ytInitialData = {"a": [1, 2, {"b": "c"}]};</script>'
        self.assertEqual(yt.extract_initial_data(html), {"a": [1, 2, {"b": "c"}]})

    def test_window_form_double_and_single_quotes(self) -> None:
        for marker in ('window["ytInitialData"] = ', "window['ytInitialData']=\n"):
            with self.subTest(marker=marker):
                html = "<script>" + marker + '{"k": 1};</script>'
                self.assertEqual(yt.extract_initial_data(html), {"k": 1})

    def test_braces_and_script_close_sequences_inside_strings(self) -> None:
        payload = {"title": "x }; </script> { y", "n": {"deep": ["}", "{"]}}
        html = "<script>var ytInitialData = " + json.dumps(payload) + ";</script><script>other()</script>"
        self.assertEqual(yt.extract_initial_data(html), payload)

    def test_decoy_marker_is_skipped(self) -> None:
        html = "/* var ytInitialData = nope */ var ytInitialData = {\"ok\": true};"
        self.assertEqual(yt.extract_initial_data(html), {"ok": True})

    def test_missing_marker_and_bad_json_raise(self) -> None:
        with self.assertRaisesRegex(yt.ParseError, "not found"):
            yt.extract_initial_data("<html>consent page</html>")
        with self.assertRaisesRegex(yt.ParseError, "could not be decoded"):
            yt.extract_initial_data("var ytInitialData = {broken")


class FixtureParsingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.videos = yt.parse_search_html(FIXTURE.read_text(encoding="utf-8"))
        cls.by_id = {v["id"]: v for v in cls.videos}

    def test_five_unique_videos_in_page_order(self) -> None:
        self.assertEqual([v["id"] for v in self.videos], [ID_A, ID_B, ID_C, ID_D, ID_E])

    def test_playlist_and_channel_cards_are_ignored(self) -> None:
        self.assertTrue(all(yt.is_valid_video_id(v["id"]) for v in self.videos))

    def test_fields_for_a_normal_video(self) -> None:
        video = self.by_id[ID_A]
        self.assertEqual(video["title"], "Strategy Pattern in Java - Full Code Example")
        self.assertEqual(video["channel"], "Example Code Academy")
        self.assertEqual(video["views"], 1234567)
        self.assertEqual(video["published"], "3 years ago")
        self.assertEqual(video["length"], "14:32")
        self.assertEqual(video["length_seconds"], 872)
        self.assertIn("Java code", video["description"])
        self.assertEqual(video["url"], "https://www.youtube.com/watch?v=" + ID_A)
        self.assertFalse(video["is_short"] or video["is_live"] or video["is_playlist"])

    def test_runs_and_suffix_forms(self) -> None:
        self.assertEqual(self.by_id[ID_E]["views"], 52340)
        self.assertEqual(self.by_id[ID_E]["length_seconds"], 3723)
        self.assertEqual(self.by_id[ID_C]["views"], 9800000)
        self.assertIn("{Beginners}; };", self.by_id[ID_E]["title"])

    def test_short_and_live_flags(self) -> None:
        self.assertTrue(self.by_id[ID_C]["is_short"])
        self.assertTrue(self.by_id[ID_D]["is_live"])
        self.assertEqual(self.by_id[ID_D]["length_seconds"], None)
        self.assertEqual(self.by_id[ID_D]["views"], 1204)


class RankingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.videos = yt.parse_search_html(FIXTURE.read_text(encoding="utf-8"))

    def test_java_order_and_disqualifications(self) -> None:
        ranked, disqualified = yt.rank_results(self.videos, "java")
        self.assertEqual([r["id"] for r in ranked], [ID_A, ID_E, ID_B])
        self.assertEqual([r["rank"] for r in ranked], [1, 2, 3])
        reasons = {d["id"]: d["reasons"] for d in disqualified}
        self.assertEqual(reasons, {ID_C: ["short"], ID_D: ["live"]})
        self.assertEqual(ranked[0]["score"]["language_tier"], 3)
        self.assertEqual(ranked[2]["score"]["language_tier"], 0)
        self.assertFalse(ranked[1]["score"]["length_ok"])

    def test_language_changes_the_order(self) -> None:
        ranked, disqualified = yt.rank_results(self.videos, "python")
        self.assertEqual([r["id"] for r in ranked], [ID_B])
        self.assertEqual(ranked[0]["score"]["language_tier"], 1)
        reasons = {d["id"]: d["reasons"] for d in disqualified}
        self.assertEqual(reasons[ID_A], ["other-code-language:java"])
        self.assertEqual(reasons[ID_E], ["other-code-language:java"])

    def test_ranking_is_deterministic(self) -> None:
        first, _ = yt.rank_results(self.videos, "java")
        second, _ = yt.rank_results(list(reversed(self.videos)), "java")
        self.assertEqual([r["id"] for r in first], [r["id"] for r in second])

    def test_language_tiers(self) -> None:
        patterns = yt.language_patterns("java")
        cases = [
            (item(title="Strategy in Java", description="code walkthrough"), 3),
            (item(title="Java Strategy"), 2),
            (item(title="Strategy", description="we use Java here"), 1),
            (item(title="Strategy", description="we use code here"), 0),
        ]
        for entry, expected in cases:
            with self.subTest(title=entry["title"]):
                self.assertEqual(yt.language_tier(entry, patterns), expected)

    def test_java_does_not_match_javascript(self) -> None:
        patterns = yt.language_patterns("java")
        self.assertEqual(yt.language_tier(item(title="JavaScript Tutorial"), patterns), 0)
        self.assertEqual(yt.language_tier(item(title="Java and JavaScript Tutorial"), patterns), 3)

    def test_language_aliases(self) -> None:
        self.assertEqual(yt.canonical_language("TS"), "typescript")
        self.assertEqual(yt.canonical_language(" py "), "python")
        self.assertEqual(yt.canonical_language("C++"), "cpp")
        self.assertEqual(yt.language_tier(item(title="Node.js code"), yt.language_patterns("javascript")), 3)

    def test_views_relative_to_age_beats_raw_views(self) -> None:
        old_popular = item("OLDOLDOLD01", title="Pattern in Python", views=900000, published="9 years ago")
        newer = item("NEWNEWNEW01", title="Pattern in Python", views=600000, published="1 year ago")
        ranked, _ = yt.rank_results([old_popular, newer], "python")
        self.assertEqual([r["id"] for r in ranked], ["NEWNEWNEW01", "OLDOLDOLD01"])

    def test_language_outranks_views(self) -> None:
        viral = item("VIRALVIRAL1", title="Pattern explained", views=50000000, published="1 year ago")
        on_topic = item("ONTOPIC0001", title="Pattern in Python", views=2000, published="1 year ago")
        ranked, _ = yt.rank_results([viral, on_topic], "python")
        self.assertEqual(ranked[0]["id"], "ONTOPIC0001")

    def test_channel_pool_breaks_ties_and_preferred_channel_wins(self) -> None:
        pool = [
            item("SOLOSOLOSO1", title="Pattern in Python", channel="Solo", views=100000),
            item("TRIOTRIOTR1", title="Pattern in Python", channel="Trio", views=100000),
            item("TRIOTRIOTR2", title="Pattern part 2 in Python", channel="Trio", views=100000),
        ]
        ranked, _ = yt.rank_results(pool, "python")
        self.assertEqual(ranked[-1]["id"], "SOLOSOLOSO1")
        preferred, _ = yt.rank_results(pool, "python", preferred_channels=["solo"])
        self.assertEqual(preferred[0]["id"], "SOLOSOLOSO1")

    def test_length_window_breaks_ties(self) -> None:
        too_long = item("LONGLONGLON", title="Pattern in Python", length_seconds=4000, length="1:06:40")
        in_window = item("INWINDOW001", title="Pattern in Python", length_seconds=900, length="15:00")
        ranked, _ = yt.rank_results([too_long, in_window], "python")
        self.assertEqual([r["id"] for r in ranked], ["INWINDOW001", "LONGLONGLON"])
        self.assertTrue(ranked[0]["score"]["length_ok"])

    def test_window_membership_beats_distance_to_the_target(self) -> None:
        # 100 s is nearer to 10 minutes than 1700 s is, but only 1700 s is inside the 2-30 minute window.
        too_short = item("TOOSHORT001", title="Pattern in Python", length_seconds=100, length="1:40")
        in_window = item("INWINDOW002", title="Pattern in Python", length_seconds=1700, length="28:20")
        ranked, _ = yt.rank_results([too_short, in_window], "python")
        self.assertEqual([r["id"] for r in ranked], ["INWINDOW002", "TOOSHORT001"])
        self.assertEqual([r["score"]["length_ok"] for r in ranked], [True, False])
        edges = [item("EDGEEDGEED%d" % i, title="Pattern in Python", channel="C%d" % i, length_seconds=sec)
                 for i, sec in enumerate((119, 120, 1800, 1801))]
        ranked, _ = yt.rank_results(edges, "python")
        self.assertEqual({r["length_seconds"]: r["score"]["length_ok"] for r in ranked},
                         {119: False, 120: True, 1800: True, 1801: False})

    def test_shorts_boundary_is_sixty_seconds_inclusive(self) -> None:
        for seconds, expected_short in ((59, True), (60, True), (61, False)):
            with self.subTest(seconds=seconds):
                ranked, disqualified = yt.rank_results([item("BOUNDARYVID", length_seconds=seconds)], "python")
                self.assertEqual(bool(disqualified), expected_short)

    def test_recorded_stream_loses_a_tie(self) -> None:
        # The stream's ID sorts first, so only the stream tie-breaker can put the edited upload ahead.
        stream = item("AAASTREAM01", title="Pattern in Python", published="Streamed 1 year ago")
        edited = item("ZZZEDITED01", title="Pattern in Python", published="1 year ago")
        ranked, _ = yt.rank_results([stream, edited], "python")
        self.assertEqual(ranked[0]["id"], "ZZZEDITED01")
        self.assertTrue(ranked[1]["score"]["was_stream"])

    def test_disqualifiers(self) -> None:
        cases = {
            "short-flag": (item("SHORTSHORT1", is_short=True), "short"),
            "short-length": (item("SHORTSHORT2", length_seconds=45, length="0:45"), "short"),
            "short-hashtag": (item("SHORTSHORT3", title="Pattern #shorts"), "short"),
            "live": (item("LIVELIVELIV", is_live=True), "live"),
            "watching": (item("WATCHWATCH1", views_text="12 watching"), "live"),
            "playlist-flag": (item("PLAYPLAYPL1", is_playlist=True), "playlist"),
            "playlist-url": (item("PLAYPLAYPL2", url="https://www.youtube.com/playlist?list=PLabc"), "playlist"),
            "playlist-id": (item("PLexampleexampleexampleexample00000"), "invalid-id"),
            "bad-id": (item("short"), "invalid-id"),
            "cyrillic": (item("NONENGLISH1", title="Паттерн стратегия Python"), "non-english"),
            "marker": (item("NONENGLISH2", title="Padrão Strategy em Python (Português)"), "non-english"),
            "other-lang": (item("OTHERLANG01", title="Pattern in Rust"), "other-code-language:rust"),
        }
        for name, (entry, reason) in cases.items():
            with self.subTest(case=name):
                ranked, disqualified = yt.rank_results([entry], "python")
                self.assertEqual(ranked, [])
                self.assertIn(reason, disqualified[0]["reasons"])

    def test_allow_non_english_flag(self) -> None:
        entry = item("NONENGLISH3", title="Паттерн стратегия Python")
        ranked, _ = yt.rank_results([entry], "python", allow_non_english=True)
        self.assertEqual(len(ranked), 1)

    def test_mentioning_requested_language_is_not_a_conflict(self) -> None:
        entry = item("BOTHLANG001", title="Pattern in Java and Python")
        ranked, _ = yt.rank_results([entry], "python")
        self.assertEqual(len(ranked), 1)

    def test_duplicates_collapse_and_old_format_is_accepted(self) -> None:
        legacy = {"id": "LEGACYLEGA1", "title": "Pattern in Python", "channel": "Old", "views": "1,000 views",
                  "published": "2 years ago", "length": "10:00"}
        ranked, _ = yt.rank_results([legacy, dict(legacy)], "python")
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["views"], 1000)
        self.assertEqual(ranked[0]["length_seconds"], 600)

    def test_non_object_entries_raise(self) -> None:
        with self.assertRaises(yt.ParseError):
            yt.rank_results(["not an object"], "python")


class VerifyTests(unittest.TestCase):
    def test_success_prints_title_and_author_and_builds_oembed_url(self) -> None:
        payload = json.dumps({"title": "Invented Title", "author_name": "Invented Channel"})
        with mock.patch("urllib.request.urlopen", return_value=fake_response(payload)) as urlopen:
            code, out, _ = run_cli("verify", ID_A)
        self.assertEqual(code, 0)
        self.assertIn("OK    " + ID_A, out)
        self.assertIn("Invented Title | Invented Channel", out)
        request = urlopen.call_args[0][0]
        self.assertTrue(request.full_url.startswith("https://www.youtube.com/oembed?format=json&url="))
        self.assertIn("watch%3Fv%3D" + ID_A, request.full_url)
        self.assertIn("verified_at:", out)

    def test_http_404_is_a_failed_check(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=http_error(404)):
            code, out, _ = run_cli("verify", ID_A)
        self.assertEqual(code, 1)
        self.assertIn("FAIL  " + ID_A, out)
        self.assertIn("HTTP 404", out)

    def test_http_401_means_embedding_disabled(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=http_error(401)):
            code, out, _ = run_cli("verify", ID_A)
        self.assertEqual(code, 1)
        self.assertIn("embedding disabled", out)

    def test_blocked_network_is_exit_2_not_a_verdict(self) -> None:
        for error in (urllib.error.URLError("tunnel refused"), http_error(403), TimeoutError("timed out")):
            with self.subTest(error=type(error).__name__):
                with mock.patch("urllib.request.urlopen", side_effect=error):
                    code, out, err = run_cli("verify", ID_A)
                self.assertEqual(code, 2)
                self.assertIn("FAIL  " + ID_A, out)
                self.assertIn("run this command on the user's machine", err)

    def test_malformed_payload_fails(self) -> None:
        for body in ("<html>not json</html>", json.dumps({"title": "only title"}), "[]"):
            with self.subTest(body=body[:20]):
                with mock.patch("urllib.request.urlopen", return_value=fake_response(body)):
                    code, out, _ = run_cli("verify", ID_A)
                self.assertEqual(code, 1)
                self.assertIn("unexpected oEmbed payload", out)

    def test_invalid_id_never_reaches_the_network(self) -> None:
        with mock.patch("urllib.request.urlopen") as urlopen:
            code, out, _ = run_cli("verify", "not-an-id", "../etc/passwd", "AAAAAAAAAAA\n")
        urlopen.assert_not_called()
        self.assertEqual(code, 1)
        self.assertEqual(out.count("invalid id format"), 3)

    def test_mixed_ids_report_each_and_exit_1(self) -> None:
        good = json.dumps({"title": "T", "author_name": "A"})
        with mock.patch("urllib.request.urlopen", side_effect=[fake_response(good), http_error(404)]) as urlopen:
            code, out, _ = run_cli("verify", ID_A, ID_B, "bad")
        self.assertEqual(urlopen.call_count, 2)
        self.assertEqual(code, 1)
        self.assertIn("OK    " + ID_A, out)
        self.assertIn("FAIL  " + ID_B, out)
        self.assertIn("FAIL  bad", out)

    def test_json_output(self) -> None:
        good = json.dumps({"title": "T", "author_name": "A"})
        with mock.patch("urllib.request.urlopen", return_value=fake_response(good)):
            code, out, _ = run_cli("verify", ID_A, "--json")
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertRegex(payload["verified_at"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertEqual(payload["results"][0]["title"], "T")


class SearchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.html = FIXTURE.read_bytes()

    def test_search_requests_results_page_with_browser_headers(self) -> None:
        with mock.patch("urllib.request.urlopen", return_value=fake_response(self.html)) as urlopen:
            code, out, _ = run_cli("search", "strategy pattern java", "--limit", "2", "--timeout", "7")
        self.assertEqual(code, 0)
        request = urlopen.call_args[0][0]
        self.assertIn("https://www.youtube.com/results?", request.full_url)
        self.assertIn("search_query=strategy%20pattern%20java", request.full_url)
        self.assertIn("Mozilla/5.0", request.get_header("User-agent"))
        self.assertEqual(urlopen.call_args[1]["timeout"], 7.0)
        self.assertEqual(len(out.strip().splitlines()), 2)
        self.assertIn(ID_A, out)

    def test_search_json_envelope_records_pull_date(self) -> None:
        with mock.patch("urllib.request.urlopen", return_value=fake_response(self.html)):
            with mock.patch.object(yt, "utc_now_iso", return_value="2026-01-02T03:04:05Z"):
                code, out, _ = run_cli("search", "q", "--json")
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(payload["query"], "q")
        self.assertEqual(payload["pulled_at"], "2026-01-02T03:04:05Z")
        self.assertEqual(len(payload["results"]), 5)

    def test_search_out_file_is_utf8_and_feeds_rank(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "java.json"
            with mock.patch("urllib.request.urlopen", return_value=fake_response(self.html)):
                code, _out, _ = run_cli("search", "q", "--out", str(target))
            self.assertEqual(code, 0)
            self.assertFalse(target.read_bytes().startswith(b"\xef\xbb\xbf"))
            code, out, _ = run_cli("rank", str(target), "--language", "java", "--top", "1")
            self.assertEqual(code, 0)
            self.assertIn("1. " + ID_A, out)
            self.assertNotIn(ID_E, out.split("Disqualified")[0])

    def test_blocked_network_is_exit_2_with_hint(self) -> None:
        with mock.patch("urllib.request.urlopen", side_effect=urllib.error.URLError("blocked")):
            code, _out, err = run_cli("search", "q")
        self.assertEqual(code, 2)
        self.assertIn("user's machine", err)

    def test_page_without_data_is_exit_2(self) -> None:
        with mock.patch("urllib.request.urlopen", return_value=fake_response("<html>consent</html>")):
            code, _out, err = run_cli("search", "q")
        self.assertEqual(code, 2)
        self.assertIn("ytInitialData not found", err)

    def test_zero_videos_is_a_failed_check(self) -> None:
        empty = '<script>var ytInitialData = {"contents": {}};</script>'
        with mock.patch("urllib.request.urlopen", return_value=fake_response(empty)):
            code, _out, err = run_cli("search", "q")
        self.assertEqual(code, 1)
        self.assertIn("no videos found", err)

    def test_size_cap_reads_at_most_cap_plus_one_and_rejects_oversize(self) -> None:
        with mock.patch.object(yt, "MAX_BYTES", 50):
            body = fake_response(b"x" * 51)
            with mock.patch("urllib.request.urlopen", return_value=body):
                code, _out, err = run_cli("search", "q")
            self.assertEqual(code, 2)
            self.assertIn("larger than 50 bytes", err)
            body.read.assert_called_once_with(51)  # an unbounded read() would be a regression
            body.close.assert_called()

    def test_size_cap_allows_exactly_the_cap(self) -> None:
        with mock.patch.object(yt, "MAX_BYTES", 50):
            with mock.patch("urllib.request.urlopen", return_value=fake_response(b"y" * 50)):
                self.assertEqual(yt.http_get("https://www.youtube.com/x", 5), "y" * 50)


class CliTests(unittest.TestCase):
    def test_usage_errors_exit_2(self) -> None:
        for argv in ([], ["bogus"], ["search"], ["verify"], ["rank", "x.json"], ["search", "q", "--limit", "0"]):
            with self.subTest(argv=argv):
                code, _out, _err = run_cli(*argv)
                self.assertEqual(code, 2)

    def test_help_exits_0(self) -> None:
        code, out, _ = run_cli("--help")
        self.assertEqual(code, 0)
        self.assertIn("verify", out)

    def test_parse_text_and_json(self) -> None:
        code, out, _ = run_cli("parse", str(FIXTURE))
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()), 5)
        code, out, _ = run_cli("parse", str(FIXTURE), "--json", "--limit", "3")
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual([r["id"] for r in payload["results"]], [ID_A, ID_B, ID_C])
        self.assertEqual(payload["source"], "results.html")

    def test_parse_errors_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.html"
            code, _out, err = run_cli("parse", str(missing))
            self.assertEqual(code, 2)
            self.assertIn("error:", err)
            blank = Path(tmp) / "blank.html"
            blank.write_text("<html></html>", encoding="utf-8")
            code, _out, err = run_cli("parse", str(blank))
            self.assertEqual(code, 2)
            self.assertIn("ytInitialData not found", err)

    def test_rank_text_output_lists_disqualified_and_next_step(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parsed = Path(tmp) / "parsed.json"
            code, _out, _ = run_cli("parse", str(FIXTURE), "--out", str(parsed))
            self.assertEqual(code, 0)
            code, out, _ = run_cli("rank", str(parsed), "--language", "java")
            self.assertEqual(code, 0)
            self.assertIn("Ranked for language=java", out)
            self.assertIn("Disqualified (2): " + ID_C + " short; " + ID_D + " live", out)
            self.assertIn("verify <id>", out)
            order = [out.index(i) for i in (ID_A, ID_E, ID_B)]
            self.assertEqual(order, sorted(order))

    def test_rank_json_and_top(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            parsed = Path(tmp) / "parsed.json"
            run_cli("parse", str(FIXTURE), "--out", str(parsed))
            code, out, _ = run_cli("rank", str(parsed), "--language", "JAVA", "--top", "2", "--json")
            payload = json.loads(out)
            self.assertEqual(code, 0)
            self.assertEqual(payload["language"], "java")
            self.assertEqual([r["id"] for r in payload["ranked"]], [ID_A, ID_E])
            self.assertEqual(len(payload["disqualified"]), 2)

    def test_rank_accepts_bare_list_query_map_and_utf16_files(self) -> None:
        videos = yt.parse_search_html(FIXTURE.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            bare = Path(tmp) / "bare.json"
            bare.write_text(json.dumps(videos), encoding="utf-8")
            mapped = Path(tmp) / "mapped.json"
            mapped.write_text(json.dumps({"query one": videos[:2], "query two": videos[2:]}), encoding="utf-8")
            utf16 = Path(tmp) / "utf16.json"
            utf16.write_text(json.dumps(videos), encoding="utf-16")
            for path in (bare, mapped, utf16):
                with self.subTest(path=path.name):
                    code, out, _ = run_cli("rank", str(path), "--language", "java", "--json")
                    self.assertEqual(code, 0)
                    self.assertEqual([r["id"] for r in json.loads(out)["ranked"]], [ID_A, ID_E, ID_B])

    def test_rank_bad_input_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("not json", encoding="utf-8")
            code, _out, err = run_cli("rank", str(bad), "--language", "java")
            self.assertEqual(code, 2)
            self.assertIn("not valid JSON", err)
            shape = Path(tmp) / "shape.json"
            shape.write_text('{"results": "nope"}', encoding="utf-8")
            code, _out, err = run_cli("rank", str(shape), "--language", "java")
            self.assertEqual(code, 2)
            self.assertIn("unexpected JSON shape", err)
            code, _out, _err = run_cli("rank", str(Path(tmp) / "missing.json"), "--language", "java")
            self.assertEqual(code, 2)

    def test_rank_with_no_qualified_candidates_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            only_short = Path(tmp) / "short.json"
            only_short.write_text(json.dumps([item("SHORTSHORT1", is_short=True)]), encoding="utf-8")
            code, _out, err = run_cli("rank", str(only_short), "--language", "java")
            self.assertEqual(code, 1)
            self.assertIn("no qualified candidates", err)


class TransportErrorTests(unittest.TestCase):
    """Any transport failure is a network error (exit 2), never a traceback or exit 1."""

    def test_truncated_body_is_exit_2_for_search_and_verify(self) -> None:
        for command in (("search", "q"), ("verify", ID_A)):
            with self.subTest(command=command[0]):
                response = fake_response(b"ignored")
                response.read.side_effect = http.client.IncompleteRead(b"x")
                with mock.patch("urllib.request.urlopen", return_value=response):
                    code, out, err = run_cli(*command)
                self.assertEqual(code, 2)
                self.assertIn("IncompleteRead", out + err)
                response.close.assert_called()

    def test_http_client_errors_raised_by_urlopen_are_exit_2(self) -> None:
        errors = (http.client.BadStatusLine("junk"), http.client.LineTooLong("status line"),
                  http.client.RemoteDisconnected("closed"), ConnectionResetError("reset"))
        for error in errors:
            for command in (("search", "q"), ("verify", ID_A)):
                with self.subTest(error=type(error).__name__, command=command[0]):
                    with mock.patch("urllib.request.urlopen", side_effect=error):
                        code, _out, err = run_cli(*command)
                    self.assertEqual(code, 2)
                    self.assertIn("error:", err)

    def test_verify_marks_truncated_response_as_network_error(self) -> None:
        response = fake_response(b"ignored")
        response.read.side_effect = http.client.IncompleteRead(b"x")
        with mock.patch("urllib.request.urlopen", return_value=response):
            result = yt.verify_id(ID_A, 5)
        self.assertTrue(result["network_error"])
        self.assertFalse(result["ok"])

    def test_http_error_is_closed_but_still_raised(self) -> None:
        error = http_error(404)
        with mock.patch.object(error, "close") as close:
            with mock.patch("urllib.request.urlopen", side_effect=error):
                with self.assertRaises(urllib.error.HTTPError):
                    yt.http_get("https://www.youtube.com/x", 5)
        close.assert_called_once_with()

    def test_main_turns_an_unexpected_oserror_into_exit_2(self) -> None:
        with mock.patch.object(yt, "cmd_parse", side_effect=OSError("disk exploded")):
            code, _out, err = run_cli("parse", str(FIXTURE))
        self.assertEqual(code, 2)
        self.assertIn("error: disk exploded", err)

    def test_unwritable_out_path_is_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "missing-dir" / "out.json"
            code, _out, err = run_cli("parse", str(FIXTURE), "--out", str(target))
        self.assertEqual(code, 2)
        self.assertIn("error:", err)


class RedirectAndCookieTests(unittest.TestCase):
    def test_consent_cookie_and_locale_are_sent_on_the_first_request_only(self) -> None:
        with mock.patch("urllib.request.urlopen", return_value=fake_response(FIXTURE.read_bytes())) as urlopen:
            run_cli("search", "q")
        request = urlopen.call_args[0][0]
        self.assertIn("hl=en&gl=US", request.full_url)
        self.assertIn("CONSENT=", request.get_header("Cookie"))
        self.assertIn("SOCS=", request.get_header("Cookie"))
        self.assertEqual(request.get_header("Accept-language"), "en-US,en;q=0.9")
        self.assertIn("Cookie", request.unredirected_hdrs)
        self.assertNotIn("Cookie", request.headers)

    def test_cookie_is_dropped_by_urllib_on_redirect(self) -> None:
        request = yt.build_request("https://www.youtube.com/results?search_query=x")
        for target in ("https://other.example.com/x", "https://consent.youtube.com/x"):
            with self.subTest(target=target):
                redirected = urllib.request.HTTPRedirectHandler().redirect_request(
                    request, None, 302, "Found", {}, target)
                self.assertIsNotNone(redirected)
                self.assertIsNone(redirected.get_header("Cookie"))
                self.assertEqual(redirected.get_header("User-agent"), request.get_header("User-agent"))

    def test_allowed_url_check(self) -> None:
        allowed = ("https://www.youtube.com/results", "https://youtube.com/x", "https://consent.youtube.com/x",
                   "https://consent.google.com/m?x=1", "https://WWW.YOUTUBE.COM/watch")
        denied = ("http://www.youtube.com/results", "https://youtube.com.evil.example.com/x",
                  "https://evil-youtube.com/x", "https://www.youtube.com@evil.example.com/x",
                  "https://example.com/youtube.com", "ftp://www.youtube.com/x", "", "not a url", "https://")
        for url in allowed:
            with self.subTest(url=url):
                self.assertTrue(yt.is_allowed_url(url))
        for url in denied:
            with self.subTest(url=url):
                self.assertFalse(yt.is_allowed_url(url))

    def test_response_from_another_host_is_rejected(self) -> None:
        for command in (("search", "q"), ("verify", ID_A)):
            with self.subTest(command=command[0]):
                response = fake_response(FIXTURE.read_bytes(), url="https://evil.example.com/results")
                with mock.patch("urllib.request.urlopen", return_value=response):
                    code, out, err = run_cli(*command)
                self.assertEqual(code, 2)
                self.assertIn("unexpected host", out + err)
                self.assertNotIn(ID_A + "  Strategy", out)
                response.close.assert_called()


class DashIdTests(unittest.TestCase):
    """About 1 in 64 real video IDs starts with '-', which argparse reads as an option."""

    DASH_ID = "-aBcDeFgHiJ"

    def verify_ok(self, *argv):
        good = json.dumps({"title": "T", "author_name": "A"})
        with mock.patch("urllib.request.urlopen", side_effect=lambda *a, **k: fake_response(good)) as urlopen:
            code, out, err = run_cli(*argv)
        requested = [call[0][0].full_url for call in urlopen.call_args_list]
        return code, out, err, requested

    def test_leading_dash_id_is_accepted_as_is(self) -> None:
        code, out, _err, requested = self.verify_ok("verify", self.DASH_ID)
        self.assertEqual(code, 0)
        self.assertIn("OK    " + self.DASH_ID, out)
        self.assertIn("watch%3Fv%3D" + self.DASH_ID, requested[0])

    def test_order_is_preserved_with_flags_and_mixed_ids(self) -> None:
        code, out, _err, requested = self.verify_ok("verify", ID_A, self.DASH_ID, ID_B, "--json", "--timeout", "9")
        self.assertEqual(code, 0)
        ids = [r["id"] for r in json.loads(out)["results"]]
        self.assertEqual(ids, [ID_A, self.DASH_ID, ID_B])
        self.assertEqual(len(requested), 3)

    def test_separator_form_also_works(self) -> None:
        code, out, _err, _requested = self.verify_ok("verify", "--json", "--", self.DASH_ID, ID_A)
        self.assertEqual(code, 0)
        self.assertEqual([r["id"] for r in json.loads(out)["results"]], [self.DASH_ID, ID_A])

    def test_marker_rewriting_is_scoped(self) -> None:
        mark = yt.DASH_ID_MARK
        self.assertEqual(yt.protect_dash_ids(["verify", self.DASH_ID]), ["verify", mark + self.DASH_ID])
        self.assertEqual(yt.protect_dash_ids(["verify", "--", self.DASH_ID]), ["verify", "--", self.DASH_ID])
        self.assertEqual(yt.protect_dash_ids(["verify", "--timeout", "-1234567890"]),
                         ["verify", "--timeout", "-1234567890"])
        self.assertEqual(yt.protect_dash_ids(["verify", "--json", "--timeout", "5"]),
                         ["verify", "--json", "--timeout", "5"])
        self.assertEqual(yt.protect_dash_ids(["search", self.DASH_ID]), ["search", self.DASH_ID])
        self.assertEqual(yt.protect_dash_ids([]), [])

    def test_other_dash_arguments_stay_usage_errors(self) -> None:
        for argv in (("verify", "-x"), ("verify", "--nope", ID_A), ("verify", "-aBcDeFgHiJkL")):
            with self.subTest(argv=argv):
                with mock.patch("urllib.request.urlopen") as urlopen:
                    code, _out, _err = run_cli(*argv)
                self.assertEqual(code, 2)
                urlopen.assert_not_called()

    def test_verify_help_documents_the_rule(self) -> None:
        _code, out, _err = run_cli("verify", "--help")
        self.assertIn("starts with", out)
        self.assertIn("--", out)


class TimeoutValidationTests(unittest.TestCase):
    def test_non_positive_or_non_finite_timeout_is_a_usage_error(self) -> None:
        for value in ("0", "-1", "nan", "inf", "abc"):
            for command in (("search", "q"), ("verify", ID_A)):
                with self.subTest(value=value, command=command[0]):
                    with mock.patch("urllib.request.urlopen") as urlopen:
                        code, _out, _err = run_cli(*command, "--timeout", value)
                    self.assertEqual(code, 2)
                    urlopen.assert_not_called()


class OutFileTests(unittest.TestCase):
    def test_out_is_written_as_utf8_bytes_with_lf_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "r.json"
            # Path.write_text(newline=...) does not exist before Python 3.10; this fails loudly if used.
            with mock.patch.object(Path, "write_text", side_effect=AssertionError("write_text used")):
                code, _out, _err = run_cli("parse", str(FIXTURE), "--out", str(target))
            raw = target.read_bytes()
        self.assertEqual(code, 0)
        self.assertTrue(raw.endswith(b"\n"))
        self.assertNotIn(b"\r", raw)
        self.assertEqual(len(json.loads(raw.decode("utf-8"))["results"]), 5)

    def test_non_ascii_titles_are_written_unescaped(self) -> None:
        html = page_with(renderer(title={"simpleText": "Muster — Strategie"}))
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "p.html"
            source.write_text(html, encoding="utf-8")
            target = Path(tmp) / "r.json"
            code, _out, _err = run_cli("parse", str(source), "--out", str(target))
            raw = target.read_bytes()
        self.assertEqual(code, 0)
        self.assertIn("Muster — Strategie".encode("utf-8"), raw)

    def test_empty_result_never_overwrites_an_existing_out_file(self) -> None:
        empty = '<script>var ytInitialData = {"contents": {}};</script>'
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "curated.json"
            target.write_text("KEEP ME", encoding="utf-8")
            blank = Path(tmp) / "blank.html"
            blank.write_text(empty, encoding="utf-8")
            with mock.patch("urllib.request.urlopen", return_value=fake_response(empty)):
                search = run_cli("search", "q", "--out", str(target))
            parse = run_cli("parse", str(blank), "--out", str(target))
            parse_json = run_cli("parse", str(blank), "--out", str(target), "--json")
            self.assertEqual(target.read_text(encoding="utf-8"), "KEEP ME")
        for code, out, err in (search, parse, parse_json):
            self.assertEqual(code, 1)
            self.assertNotIn("wrote", out)
            self.assertIn("left untouched", err)

    def test_empty_result_does_not_create_the_out_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            blank = Path(tmp) / "blank.html"
            blank.write_text('<script>var ytInitialData = {};</script>', encoding="utf-8")
            target = Path(tmp) / "new.json"
            code, _out, _err = run_cli("parse", str(blank), "--out", str(target))
            self.assertEqual(code, 1)
            self.assertFalse(target.exists())


class MalformedMarkupTests(unittest.TestCase):
    CRASHERS = {
        "badges": {"badges": 5},
        "thumbnailOverlays": {"thumbnailOverlays": 5},
        "title runs": {"title": {"runs": [{"text": 5}]}},
        "owner runs": {"ownerText": {"runs": [{"text": 5}]}},
        "command metadata": {"navigationEndpoint": {"commandMetadata": 5}},
        "snippets": {"detailedMetadataSnippets": 5},
    }

    def test_one_malformed_renderer_is_skipped_not_fatal(self) -> None:
        for name, override in self.CRASHERS.items():
            with self.subTest(field=name):
                html = page_with(renderer("BADBADBADBA", **override), renderer("GOODGOODGOO"))
                self.assertEqual([v["id"] for v in yt.parse_search_html(html)], ["GOODGOODGOO"])

    def test_all_renderers_malformed_is_a_parse_error_and_exit_2(self) -> None:
        for name, override in self.CRASHERS.items():
            with self.subTest(field=name):
                html = page_with(renderer("BADBADBADBA", **override), renderer("BADBADBADBB", **override))
                with self.assertRaisesRegex(yt.ParseError, "unexpected field types"):
                    yt.parse_search_html(html)
                with mock.patch("urllib.request.urlopen", return_value=fake_response(html)):
                    code, _out, err = run_cli("search", "q")
                self.assertEqual(code, 2)
                self.assertIn("markup change", err)

    def test_renderer_without_a_video_id_is_ignored(self) -> None:
        self.assertIsNone(yt.video_from_renderer({"title": {"simpleText": "x"}}))
        self.assertIsNone(yt.video_from_renderer({"videoId": 12345}))
        self.assertEqual(yt.parse_search_html(page_with({"title": {"simpleText": "x"}})), [])

    def test_absurdly_nested_json_is_a_parse_error_not_a_traceback(self) -> None:
        deep = "[" * 100000
        with self.assertRaises(yt.ParseError):
            yt.extract_initial_data("var ytInitialData = " + deep)
        with tempfile.TemporaryDirectory() as tmp:
            nested = Path(tmp) / "nested.json"
            nested.write_text(deep, encoding="utf-8")
            code, _out, err = run_cli("rank", str(nested), "--language", "java")
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)


class RendererFlagTests(unittest.TestCase):
    """Flags derived from raw videoRenderer fields, not from fixture-level behaviour."""

    def parse(self, **overrides):
        return yt.video_from_renderer(renderer(**overrides))

    def test_plain_renderer_has_no_flags(self) -> None:
        video = self.parse(lengthText={"simpleText": "10:00"}, viewCountText={"simpleText": "5 views"})
        self.assertFalse(video["is_short"] or video["is_live"] or video["is_playlist"])

    def test_live_signals(self) -> None:
        cases = {
            "upcoming event": {"upcomingEventData": {"startTime": "1"}},
            "live badge style": {"badges": [{"metadataBadgeRenderer": {"style": "BADGE_STYLE_TYPE_LIVE_NOW"}}]},
            "live badge label": {"badges": [{"metadataBadgeRenderer": {"label": " live "}}]},
            "live overlay": {"thumbnailOverlays": [{"thumbnailOverlayTimeStatusRenderer": {"style": "LIVE"}}]},
            "watching count": {"viewCountText": {"runs": [{"text": "7"}, {"text": " watching"}]}},
        }
        for name, override in cases.items():
            with self.subTest(signal=name):
                self.assertTrue(self.parse(**override)["is_live"])
        other_badge = {"badges": [{"metadataBadgeRenderer": {"style": "BADGE_STYLE_TYPE_SIMPLE", "label": "New"}}]}
        self.assertFalse(self.parse(**other_badge)["is_live"])

    def test_playlist_signals(self) -> None:
        by_id = {"navigationEndpoint": {"watchEndpoint": {"videoId": "KKKKKKKKKKK", "playlistId": "PLx"}}}
        by_url = {"navigationEndpoint": {"commandMetadata": {"webCommandMetadata": {"url": "/playlist?list=PLx"}}}}
        self.assertTrue(self.parse(**by_id)["is_playlist"])
        self.assertTrue(self.parse(**by_url)["is_playlist"])

    def test_short_signals(self) -> None:
        by_url = {"navigationEndpoint": {"commandMetadata": {"webCommandMetadata": {"url": "/shorts/KKKKKKKKKKK"}}}}
        self.assertTrue(self.parse(**by_url)["is_short"])
        self.assertTrue(self.parse(lengthText={"simpleText": "0:59"})["is_short"])
        self.assertTrue(self.parse(lengthText={"simpleText": "1:00"})["is_short"])
        self.assertFalse(self.parse(lengthText={"simpleText": "1:01"})["is_short"])

    def test_length_falls_back_to_the_overlay_text(self) -> None:
        overlay = {"thumbnailOverlays": [{"thumbnailOverlayTimeStatusRenderer": {
            "text": {"simpleText": " 7:07 "}, "style": "DEFAULT"}}]}
        video = self.parse(**overlay)
        self.assertEqual((video["length"], video["length_seconds"]), ("7:07", 427))
        live_overlay = {"thumbnailOverlays": [{"thumbnailOverlayTimeStatusRenderer": {
            "text": {"runs": [{"text": "LIVE"}]}, "style": "LIVE"}}]}
        self.assertEqual(self.parse(**live_overlay)["length"], "")

    def test_text_fallbacks(self) -> None:
        self.assertEqual(self.parse(longBylineText={"runs": [{"text": "Long"}]})["channel"], "Long")
        self.assertEqual(self.parse(shortBylineText={"runs": [{"text": "Short"}]})["channel"], "Short")
        owner = self.parse(ownerText={"runs": [{"text": "Owner"}]}, longBylineText={"runs": [{"text": "Long"}]})
        self.assertEqual(owner["channel"], "Owner")
        self.assertEqual(self.parse(descriptionSnippet={"runs": [{"text": "Snippet"}]})["description"], "Snippet")
        self.assertEqual(self.parse()["url"], "https://www.youtube.com/watch?v=KKKKKKKKKKK")


class NumericRobustnessTests(unittest.TestCase):
    def test_odd_view_counts_never_abort_ranking(self) -> None:
        raw = (
            '[{"id":"NEGATIVEVID","title":"Python Code","views":-1},'
            '{"id":"NOTANUMBERV","title":"Python Code","views":NaN},'
            '{"id":"INFINITYVID","title":"Python Code","views":Infinity},'
            '{"id":"OVERFLOWVID","title":"Python Code","views":1e999},'
            '{"id":"HUGEINTVIDE","title":"Python Code","views":1' + "0" * 400 + '},'
            '{"id":"NANLENGTHVD","title":"Python Code","views":5,"length":"10:00","length_seconds":NaN},'
            '{"id":"NEGLENGTHVD","title":"Python Code","views":5,"length":"10:00","length_seconds":-5}]'
        )
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "odd.json"
            path.write_text(raw, encoding="utf-8")
            code, out, err = run_cli("rank", str(path), "--language", "python", "--top", "10", "--json")
        self.assertEqual(code, 0, err)
        ranked = {r["id"]: r for r in json.loads(out)["ranked"]}
        self.assertEqual(len(ranked), 7)
        for video_id in ("NEGATIVEVID", "NOTANUMBERV", "INFINITYVID", "OVERFLOWVID"):
            self.assertIsNone(ranked[video_id]["views"])
            self.assertEqual(ranked[video_id]["score"]["views_per_year"], 0)
        self.assertEqual(ranked["HUGEINTVIDE"]["views"], yt.MAX_VIEWS)
        for video_id in ("NANLENGTHVD", "NEGLENGTHVD"):
            self.assertEqual(ranked[video_id]["length_seconds"], 600)

    def test_normalize_item_numeric_edges(self) -> None:
        def views(value):
            return yt.normalize_item({"id": "XXXXXXXXXXX", "views": value})["views"]
        self.assertEqual(views(0), 0)
        self.assertEqual(views(12.9), 12)
        self.assertIsNone(views(-1))
        self.assertIsNone(views(float("nan")))
        self.assertIsNone(views(float("inf")))
        self.assertIsNone(views(True))
        self.assertEqual(views("2.5M views"), 2500000)
        fallback = yt.normalize_item({"id": "XXXXXXXXXXX", "views": float("nan"), "views_text": "1,500 views"})
        self.assertEqual(fallback["views"], 1500)

    def test_parse_views_rejects_non_finite_scaling(self) -> None:
        self.assertIsNone(yt.parse_views("9" * 400 + " views"))
        self.assertEqual(yt.parse_views("1" + "0" * 20 + " views"), 10 ** 20)


class RubricPinTests(unittest.TestCase):
    """The script and references/ranking-rubric.md must describe the same ranking."""

    RUBRIC = (SKILL_DIR / "references" / "ranking-rubric.md").read_text(encoding="utf-8")
    SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")

    def test_constants(self) -> None:
        self.assertEqual(
            (yt.LENGTH_MIN_SECONDS, yt.LENGTH_MAX_SECONDS, yt.LENGTH_TARGET_SECONDS, yt.SHORT_MAX_SECONDS),
            (120, 1800, 600, 60),
        )
        self.assertEqual((yt.MIN_AGE_YEARS, yt.UNKNOWN_AGE_YEARS), (0.25, 1.0))
        self.assertEqual((yt.CHANNEL_POOL_CAP, yt.PREFERRED_CHANNEL_SCORE), (3, 10))

    def test_bucket_formula_points_quoted_in_the_rubric(self) -> None:
        self.assertEqual([yt.views_bucket(v) for v in (0, 99, 100000 - 2, 250000, 316000, 400000, 600000, 10 ** 6 - 2)],
                         [0, 4, 9, 10, 10, 11, 11, 11])
        self.assertEqual(yt.views_bucket(10 ** 6), 12)
        self.assertEqual(yt.views_bucket(400000), yt.views_bucket(600000))
        self.assertEqual(yt.views_bucket(250000), yt.views_bucket(400000) - 1)
        self.assertIn("400k and 600k per year tie", self.RUBRIC.replace("\n", " ").replace("  ", " "))
        self.assertIn("250k falls one", self.RUBRIC.replace("\n", " ").replace("  ", " "))
        self.assertIn("floor(2 * log10(views_per_year + 1))", self.RUBRIC)

    def test_rubric_text_matches_the_constants_and_reason_codes(self) -> None:
        flat = " ".join(self.RUBRIC.split())
        for fragment in ("120 to 1800 seconds", "max(age_years, 0.25)", "unknown age counts as 1", "closest to 10 minutes",
                         "capped at 3", "scores 10", "<= 60 s"):
            self.assertIn(fragment, flat)
        for reason in ("`short`", "`live`", "`playlist`", "`invalid-id`", "`non-english`", "`other-code-language:<name>`"):
            self.assertIn(reason, self.RUBRIC)

    def test_every_flag_in_the_skill_table_exists_in_the_cli(self) -> None:
        rows = re.findall(r"^\| `(search|parse|rank|verify) ([^`]*)` \|", self.SKILL, re.M)
        self.assertEqual(sorted(command for command, _ in rows), ["parse", "rank", "search", "verify"])
        for command, usage in rows:
            _code, help_text, _err = run_cli(command, "--help")
            for flag in re.findall(r"--[a-z][a-z-]*", usage):
                with self.subTest(command=command, flag=flag):
                    self.assertIn(flag, help_text)

    def test_skill_documents_the_overrides_and_exit_codes(self) -> None:
        for fragment in ("--allow-non-english", "--timeout", "--prefer-channel", "python3", "`--`"):
            self.assertIn(fragment, self.SKILL)


class SortTieBreakerTests(unittest.TestCase):
    def ids(self, *items):
        ranked, _ = yt.rank_results(list(items), "python")
        return [r["id"] for r in ranked]

    def test_length_closer_to_ten_minutes_wins_before_views(self) -> None:
        near = item("NEARNEARNE1", title="Pattern in Python", channel="A", views=100000, length_seconds=500)
        far = item("FARFARFARF1", title="Pattern in Python", channel="B", views=120000, length_seconds=900)
        self.assertEqual(self.ids(far, near), ["NEARNEARNE1", "FARFARFARF1"])

    def test_more_views_win_within_a_bucket(self) -> None:
        # The high-view ID sorts last, so only the views tie-breaker can put it first.
        low = item("AAALOWVIEWS", title="Pattern in Python", channel="A", views=100000)
        high = item("ZZZHIGHVIEW", title="Pattern in Python", channel="B", views=120000)
        self.assertEqual(yt.views_bucket(100000), yt.views_bucket(120000))
        self.assertEqual(self.ids(low, high), ["ZZZHIGHVIEW", "AAALOWVIEWS"])

    def test_video_id_is_the_final_tie_breaker(self) -> None:
        first = item("AAAAAAAAAA1", title="Pattern in Python", channel="A")
        second = item("BBBBBBBBBB1", title="Pattern in Python", channel="B")
        self.assertEqual(self.ids(second, first), ["AAAAAAAAAA1", "BBBBBBBBBB1"])
        self.assertEqual(self.ids(first, second), ["AAAAAAAAAA1", "BBBBBBBBBB1"])

    def test_rank_json_with_no_qualified_candidate_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            only_live = Path(tmp) / "live.json"
            only_live.write_text(json.dumps([item("LIVELIVELIV", is_live=True)]), encoding="utf-8")
            code, out, _err = run_cli("rank", str(only_live), "--language", "java", "--json")
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertEqual(payload["ranked"], [])
        self.assertEqual(payload["disqualified"][0]["reasons"], ["live"])


if __name__ == "__main__":
    unittest.main()
