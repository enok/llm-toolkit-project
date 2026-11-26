from __future__ import annotations

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
import zipfile
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "job-search-pipeline" / "scripts" / "render_cv.py"


def load():
    spec = importlib.util.spec_from_file_location("render_cv", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


RC = load()
HAS_DOCX = RC.have_docx()
SOFFICE = RC.find_soffice()
PDFTOTEXT = shutil.which("pdftotext")

CV = """﻿# Alex Example
alex@example.com | +1 555 0100 | Springfield | linkedin.com/in/alex-example

## Summary
Backend engineer with **8 years** building payment APIs. <!-- src: master § summary -->

## Skills
**Languages:** Java, Python, SQL
**Platforms:** Kubernetes, AWS, PostgreSQL <!-- kw: kubernetes; aws -->

## Experience
### Senior Engineer — Example Corp
*Remote | 2021-03 – Present*
- Cut p95 latency 40% as measured by APM dashboards by adding a read cache. <!-- kw: java; redis --> <!-- src: master § exp1 -->
- Led **5 engineers** through a zero-downtime database migration
  that finished a week early.
  - Wrote the runbook <!-- kw: runbooks -->
<!-- multi-line comment
     kw: hidden; words
     src: nowhere -->
### Engineer — Sample Labs
*Springfield | 2018-01 – 2021-02*
- Built the invoicing service used by 12 teams.

## Education
- BSc Computer Science — Example University

## Languages
- English (fluent)
"""


def run_cli(*argv: str):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = RC.main(list(argv))
    text = out.getvalue()
    return code, (json.loads(text) if text.strip() else None), err.getvalue()


def docx_xml(path: str, part: str = "word/document.xml") -> str:
    with zipfile.ZipFile(path) as z:
        return z.read(part).decode("utf-8")


class ParserTests(unittest.TestCase):
    def test_strip_comments_handles_inline_multiline_and_unterminated(self) -> None:
        text, warnings = RC.strip_comments("a <!-- x --> b\n<!-- y\nz -->\nc")
        self.assertEqual(text, "a  b\n\n\nc")
        self.assertEqual(warnings, [])
        text, warnings = RC.strip_comments("keep <!-- never closed\nnext")
        self.assertEqual(text, "keep \nnext")
        self.assertEqual(len(warnings), 1)

    def test_blocks_kinds_and_continuation(self) -> None:
        text, _ = RC.strip_comments(CV.lstrip("﻿"))
        blocks = RC.parse_cv(text)
        kinds = [b.kind for b in blocks]
        self.assertEqual(kinds[:3], ["name", "contact", "section"])
        self.assertEqual([b.text for b in blocks if b.kind == "entry"],
                         ["Senior Engineer — Example Corp", "Engineer — Sample Labs"])
        led = next(b for b in blocks if b.text.startswith("Led "))
        self.assertTrue(led.text.endswith("finished a week early."))
        nested = next(b for b in blocks if b.text.startswith("Wrote the runbook"))
        self.assertEqual((nested.kind, nested.level), ("bullet", 2))
        skills = [b.text for b in blocks if b.text.startswith("**Languages") or b.text.startswith("**Platforms")]
        self.assertEqual(len(skills), 2)  # label lines stay separate paragraphs

    def test_inline_bold_italic_and_links(self) -> None:
        self.assertEqual(RC.parse_inline("a **b** c"), [("a ", False, False), ("b", True, False), (" c", False, False)])
        self.assertEqual(RC.parse_inline("*Remote | 2020-01 – 2021-02*"), [("Remote | 2020-01 – 2021-02", False, True)])
        self.assertEqual(RC.parse_inline("C* and snake_case*"), [("C* and snake_case*", False, False)])
        self.assertEqual(RC.parse_inline("[site](https://example.com/x)"), [("site (https://example.com/x)", False, False)])
        self.assertEqual(RC.parse_inline("[https://e.com](https://e.com)"), [("https://e.com", False, False)])

    def test_fill_detection(self) -> None:
        self.assertEqual(RC.find_fill("ok\n- shipped [FILL: metric]\n[fill]")[0][0], 2)
        self.assertEqual(len(RC.find_fill("ok\n- shipped [FILL: metric]\n[fill]")), 2)
        self.assertEqual(RC.find_fill("[Filler] text"), [])


class MissingDependencyTests(unittest.TestCase):
    def test_missing_python_docx_prints_hint_and_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            src = Path(tmp) / "cv.md"
            src.write_text(CV, encoding="utf-8")
            with mock.patch.dict(sys.modules, {"docx": None}):
                code, payload, err = run_cli("--in", str(src), "--out-dir", tmp)
            self.assertEqual(code, 2)
            self.assertIsNone(payload)
            self.assertIn("pip install python-docx", err)
            self.assertFalse((Path(tmp) / "cv.docx").exists())


class SofficeLookupTests(unittest.TestCase):
    def test_windows_program_files_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "LibreOffice" / "program" / "soffice.exe"
            exe.parent.mkdir(parents=True)
            exe.write_text("", encoding="utf-8")
            env = {"ProgramFiles": tmp, "ProgramW6432": "", "ProgramFiles(x86)": ""}
            with mock.patch.object(RC.shutil, "which", return_value=None), \
                    mock.patch.object(RC.sys, "platform", "win32"), \
                    mock.patch.dict(os.environ, env):
                self.assertEqual(RC.find_soffice(), str(exe))

    def test_returns_none_when_absent(self) -> None:
        with mock.patch.object(RC.shutil, "which", return_value=None), \
                mock.patch.object(RC.sys, "platform", "linux"):
            self.assertIsNone(RC.find_soffice())


@unittest.skipIf(not HAS_DOCX, "python-docx not installed")
class RenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        self.src = self.dir / "cv.md"
        self.src.write_text(CV, encoding="utf-8")
        self.out = self.dir / "out"

    def render(self, *extra: str, text: str | None = None):
        if text is not None:
            self.src.write_text(text, encoding="utf-8")
        return run_cli("--in", str(self.src), "--out-dir", str(self.out), *extra)

    def paragraphs(self, path: str):
        import docx

        return [(p.style.name, p.text) for p in docx.Document(path).paragraphs]

    def test_headings_and_bullets_land_in_docx(self) -> None:
        code, payload, err = self.render()
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(payload["warnings"], [])
        self.assertIsNone(payload["pdf"])
        self.assertEqual(Path(payload["docx"]), (self.out / "cv.docx").resolve())
        paras = self.paragraphs(payload["docx"])
        self.assertEqual(paras[0], ("Title", "Alex Example"))
        self.assertEqual(paras[1][0], "CV Contact")
        self.assertIn("alex@example.com | +1 555 0100", paras[1][1])
        h1 = [t for s, t in paras if s == "Heading 1"]
        self.assertEqual(h1, ["Summary", "Skills", "Experience", "Education", "Languages"])
        h2 = [t for s, t in paras if s == "Heading 2"]
        self.assertEqual(h2, ["Senior Engineer — Example Corp", "Engineer — Sample Labs"])
        bullets = [t for s, t in paras if s == "List Bullet"]
        self.assertEqual(bullets[0], "Cut p95 latency 40% as measured by APM dashboards by adding a read cache.")
        self.assertEqual(bullets[1], "Led 5 engineers through a zero-downtime database migration that finished a week early.")
        self.assertIn("Built the invoicing service used by 12 teams.", bullets)
        self.assertIn(("List Bullet 2", "Wrote the runbook"), paras)
        self.assertIn(("CV Meta", "Remote | 2021-03 – Present"), paras)

    def test_inline_bold_is_a_bold_run(self) -> None:
        import docx

        _, payload, _ = self.render()
        doc = docx.Document(payload["docx"])
        bold = [r.text for p in doc.paragraphs for r in p.runs if r.bold]
        self.assertIn("8 years", bold)
        self.assertIn("5 engineers", bold)
        self.assertIn("Languages:", bold)
        italic = [r.text for p in doc.paragraphs for r in p.runs if r.italic]
        self.assertIn("Remote | 2021-03 – Present", italic)
        self.assertNotIn("**", "\n".join(p.text for p in doc.paragraphs))

    def test_comments_are_stripped_everywhere(self) -> None:
        _, payload, _ = self.render()
        xml = docx_xml(payload["docx"])
        for needle in ("<!--", "-->", "kw:", "src:", "hidden", "nowhere", "redis", "runbooks"):
            self.assertNotIn(needle, xml)
        with zipfile.ZipFile(payload["docx"]) as z:
            for name in z.namelist():
                if name.endswith(".xml"):
                    self.assertNotIn(b"<!--", z.read(name))

    def test_bom_is_ignored_and_ats_safe_structure(self) -> None:
        import docx

        _, payload, _ = self.render()
        with zipfile.ZipFile(payload["docx"]) as z:
            self.assertFalse([n for n in z.namelist() if n.startswith("word/media/")])
            xml = z.read("word/document.xml").decode("utf-8")
        for tag in ("<w:tbl>", "<w:tbl ", "<w:drawing", "<w:pict", "txbxContent", "<w:object", "<mc:AlternateContent"):
            self.assertNotIn(tag, xml)
        self.assertIsNone(re.search(r'<w:cols[^>]*w:num="([2-9]|\d\d)"', xml))
        doc = docx.Document(payload["docx"])
        self.assertEqual(len(doc.tables), 0)
        self.assertEqual(len(doc.inline_shapes), 0)
        self.assertEqual(doc.paragraphs[0].text, "Alex Example")  # BOM did not leak into the name
        normal = doc.styles["Normal"]
        self.assertEqual(normal.font.name, "Calibri")
        self.assertEqual(normal.font.size.pt, 10.5)
        for name in ("Title", "Heading 1", "Heading 2", "List Bullet"):
            self.assertEqual(doc.styles[name].font.name, "Calibri")
        section = doc.sections[0]
        self.assertGreaterEqual(section.left_margin.inches, 0.5)
        self.assertLessEqual(section.left_margin.inches, 1.0)

    def test_font_size_and_paper_options(self) -> None:
        import docx

        code, payload, _ = self.render("--font", "Arial", "--size", "11", "--paper", "a4", "--basename", "alex.docx")
        self.assertEqual(code, 0)
        self.assertTrue(payload["docx"].endswith("alex.docx"))
        doc = docx.Document(payload["docx"])
        self.assertEqual(doc.styles["Normal"].font.name, "Arial")
        self.assertEqual(doc.styles["Normal"].font.size.pt, 11)
        self.assertAlmostEqual(doc.sections[0].page_width.mm, 210, places=0)

    def test_fill_is_refused_without_allow_fill(self) -> None:
        text = CV.replace("zero-downtime", "zero-downtime [FILL: confirm metric]")
        code, payload, err = self.render(text=text)
        self.assertEqual(code, 2)
        self.assertIsNone(payload)
        self.assertIn("[FILL]", err)
        self.assertIn("line 15", err)
        self.assertFalse((self.out / "cv.docx").exists())

    def test_fill_is_accepted_with_allow_fill_and_reported(self) -> None:
        text = CV.replace("12 teams", "[FILL: how many teams] teams")
        code, payload, _ = self.render("--allow-fill", text=text)
        self.assertEqual(code, 0)
        self.assertTrue(any("[FILL]" in w for w in payload["warnings"]))
        self.assertIn("[FILL: how many teams] teams", "\n".join(t for _, t in self.paragraphs(payload["docx"])))

    def test_fill_inside_a_comment_does_not_block(self) -> None:
        code, payload, _ = self.render(text=CV.replace("<!-- kw: kubernetes; aws -->", "<!-- [FILL: later] -->"))
        self.assertEqual(code, 0)
        self.assertNotIn("FILL", docx_xml(payload["docx"]))

    def test_footer_has_real_field_codes_right_aligned(self) -> None:
        import docx

        code, payload, _ = self.render("--footer", "{page} of {total}")
        self.assertEqual(code, 0)
        with zipfile.ZipFile(payload["docx"]) as z:
            footers = [n for n in z.namelist() if re.fullmatch(r"word/footer\d*\.xml", n)]
            self.assertEqual(len(footers), 1)
            xml = z.read(footers[0]).decode("utf-8")
        self.assertRegex(xml, r"<w:instrText[^>]*>\s*PAGE\s*</w:instrText>")
        self.assertRegex(xml, r"<w:instrText[^>]*>\s*NUMPAGES\s*</w:instrText>")
        self.assertEqual(xml.count('w:fldCharType="begin"'), 2)
        self.assertEqual(xml.count('w:fldCharType="separate"'), 2)
        self.assertEqual(xml.count('w:fldCharType="end"'), 2)
        self.assertIn('<w:jc w:val="right"/>', xml)
        self.assertLess(xml.index("PAGE"), xml.index(" of "))
        self.assertLess(xml.index(" of "), xml.index("NUMPAGES"))
        self.assertEqual(payload["warnings"], [])
        footer = docx.Document(payload["docx"]).sections[0].footer
        self.assertFalse(footer.is_linked_to_previous)

    def test_no_footer_part_without_the_option(self) -> None:
        _, payload, _ = self.render()
        with zipfile.ZipFile(payload["docx"]) as z:
            self.assertFalse([n for n in z.namelist() if n.startswith("word/footer")])

    def test_unknown_footer_placeholder_warns(self) -> None:
        code, payload, _ = self.render("--footer", "Page {pagee}")
        self.assertEqual(code, 0)
        self.assertTrue(any("{pagee}" in w for w in payload["warnings"]))

    def test_missing_input_and_bad_basename_exit_2(self) -> None:
        code, _, err = run_cli("--in", str(self.dir / "nope.md"), "--out-dir", str(self.out))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        code, _, err = self.render("--basename", "../escape")
        self.assertEqual(code, 2)
        self.assertIn("--basename", err)

    def test_pdf_without_soffice_warns_and_exits_0(self) -> None:
        with mock.patch.object(RC, "find_soffice", return_value=None):
            code, payload, _ = self.render("--pdf")
        self.assertEqual(code, 0)
        self.assertIsNone(payload["pdf"])
        self.assertTrue(any("soffice" in w and "PDF skipped" in w for w in payload["warnings"]))
        self.assertTrue(Path(payload["docx"]).is_file())

    def test_failed_conversion_warns_and_exits_0(self) -> None:
        failed = subprocess.CompletedProcess(args=[], returncode=1, stdout="", stderr="boom")
        with mock.patch.object(RC, "find_soffice", return_value="soffice"), \
                mock.patch.object(RC.subprocess, "run", return_value=failed):
            code, payload, _ = self.render("--pdf")
        self.assertEqual(code, 0)
        self.assertIsNone(payload["pdf"])
        self.assertTrue(any("conversion failed" in w and "boom" in w for w in payload["warnings"]))


@unittest.skipIf(not HAS_DOCX, "python-docx not installed")
@unittest.skipIf(SOFFICE is None, "soffice (LibreOffice) not installed")
class PdfTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        src = Path(cls.tmp.name) / "long.md"
        bullets = "\n".join(f"- Delivered feature number {i} for the example platform with measurable impact." for i in range(1, 90))
        src.write_text(CV.replace("- Built the invoicing service used by 12 teams.", bullets), encoding="utf-8")
        cls.code, cls.payload, cls.err = run_cli(
            "--in", str(src), "--out-dir", str(Path(cls.tmp.name) / "out"), "--pdf", "--footer", "{page} of {total}")

    def test_pdf_is_created(self) -> None:
        self.assertEqual(self.code, 0, self.err)
        self.assertIsNotNone(self.payload["pdf"], self.payload["warnings"])
        pdf = Path(self.payload["pdf"])
        self.assertEqual(pdf.name, "long.pdf")
        self.assertEqual(pdf.read_bytes()[:5], b"%PDF-")

    @unittest.skipIf(PDFTOTEXT is None, "pdftotext not installed")
    def test_pdf_footer_shows_page_of_total_on_every_page(self) -> None:
        text = subprocess.run([PDFTOTEXT, "-layout", self.payload["pdf"], "-"], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", check=True).stdout
        pages = [p for p in text.split("\f") if p.strip()]
        self.assertGreaterEqual(len(pages), 2)
        for number, page in enumerate(pages, 1):
            self.assertRegex(page, rf"\b{number} of {len(pages)}\b")
        self.assertNotIn("<!--", text)
        self.assertNotIn("kw:", text)


if __name__ == "__main__":
    unittest.main()
