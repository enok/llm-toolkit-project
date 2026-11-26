from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "image-quality-inspection" / "scripts" / "check_carousel.py"
SPEC = importlib.util.spec_from_file_location("check_carousel", SCRIPT)
assert SPEC and SPEC.loader
cc = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = cc
SPEC.loader.exec_module(cc)

BLACK = {"r": 0, "g": 0, "b": 0}
WHITE = {"r": 255, "g": 255, "b": 255}


def rgb(hexcode: str) -> dict:
    h = hexcode.lstrip("#")
    return {"r": int(h[0:2], 16), "g": int(h[2:4], 16), "b": int(h[4:6], 16)}


class ContrastTests(unittest.TestCase):
    def test_black_on_white_is_21(self) -> None:
        self.assertAlmostEqual(21.0, cc.ratio(BLACK, WHITE), places=6)

    def test_ratio_is_symmetric(self) -> None:
        a, b = rgb("#17203F"), rgb("#E8ECF8")
        self.assertAlmostEqual(cc.ratio(a, b), cc.ratio(b, a), places=9)

    def test_same_colour_is_one(self) -> None:
        self.assertAlmostEqual(1.0, cc.ratio(WHITE, WHITE), places=9)

    def test_luminance_bounds(self) -> None:
        self.assertEqual(0.0, cc.lum(BLACK))
        self.assertAlmostEqual(1.0, cc.lum(WHITE), places=6)

    def test_aa_threshold_cases(self) -> None:
        self.assertGreaterEqual(cc.ratio(WHITE, rgb("#17203F")), 4.5)
        self.assertLess(cc.ratio(rgb("#777777"), rgb("#888888")), 4.5)
        # #767676 on white is the classic smallest grey that still passes 4.5
        self.assertGreaterEqual(cc.ratio(rgb("#767676"), WHITE), 4.5)
        self.assertLess(cc.ratio(rgb("#787878"), WHITE), 4.6)


class TypeFloorTests(unittest.TestCase):
    def test_floors_at_1080_width(self) -> None:
        self.assertEqual({"headline": 64, "body": 36, "footer": 24, "diagram": 30}, cc.FLOORS)

    def test_floor_classification(self) -> None:
        below = [(role, fs) for role, floor in cc.FLOORS.items() for fs in (floor - 1, floor)
                 if fs < floor - 0.01]
        self.assertEqual({r for r, _ in below}, set(cc.FLOORS))


class SourceParsingTests(unittest.TestCase):
    SOURCE = (
        "# Deck\n\n"
        "## 1/2 First\nHeadline: Alpha beta\nBody: Gamma delta.\nFooter: 1/2\n\n"
        "## 2/2 Second\nHeadline: Epsilon\nBody: Zeta\nFooter: Disclosure text\n"
    )

    def test_parse_source_sections(self) -> None:
        exp, total = cc.parse_source(self.SOURCE)
        self.assertEqual(2, total)
        self.assertEqual({1, 2}, set(exp))
        self.assertEqual(("Alpha beta", "Gamma delta.", "1/2"), exp[1])
        self.assertEqual(("Epsilon", "Zeta", "Disclosure text"), exp[2])

    def test_missing_fields_are_empty(self) -> None:
        exp, total = cc.parse_source("## 1/1 Only\nHeadline: Solo\n")
        self.assertEqual(1, total)
        self.assertEqual(("Solo", "", ""), exp[1])

    def test_multiset_token_compare(self) -> None:
        import collections
        import unicodedata
        tok = lambda s: unicodedata.normalize("NFKC", s).split()
        want = collections.Counter(tok("a b b") + ["1/2"])
        same_other_order = collections.Counter(tok("b 1/2 a b"))
        missing_one = collections.Counter(tok("a b 1/2"))
        self.assertEqual(want, same_other_order)
        self.assertNotEqual(want, missing_one)
        self.assertEqual({"b": 1}, dict(want - missing_one))


class ArgumentTests(unittest.TestCase):
    def run_main(self, argv: list[str]) -> tuple[int, str]:
        err = io.StringIO()
        with mock.patch.object(sys, "argv", ["check_carousel.py", *argv]), contextlib.redirect_stderr(err):
            code = cc.main()
        return code, err.getvalue()

    def test_missing_inputs_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            missing = str(Path(tmp) / "nope")
            code, err = self.run_main(["--slides", missing, "--pdf", missing, "--source", missing])
        self.assertEqual(2, code)
        self.assertIn("missing input", err)

    def test_required_arguments(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()), mock.patch.object(sys, "argv", ["check_carousel.py"]):
            with self.assertRaises(SystemExit) as ctx:
                cc.main()
        self.assertEqual(2, ctx.exception.code)

    def test_missing_playwright_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            files = []
            for name in ("s.html", "d.pdf", "src.md"):
                path = Path(tmp) / name
                path.write_text("x", encoding="utf-8")
                files.append(str(path))
            with mock.patch.dict(sys.modules, {"playwright": None, "playwright.sync_api": None}):
                code, err = self.run_main(["--slides", files[0], "--pdf", files[1], "--source", files[2]])
        self.assertEqual(2, code)
        self.assertIn("playwright", err)


if __name__ == "__main__":
    unittest.main()
