"""Tests for skills/document-conversion/scripts/convert_to_markdown.py.

Fixtures are generated in a temp directory. Each test skips cleanly when the
library it needs is not installed.
"""

from __future__ import annotations

import importlib.util
import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "document-conversion" / "scripts" / "convert_to_markdown.py"


def _load():
    spec = importlib.util.spec_from_file_location("convert_to_markdown", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has(*modules: str) -> bool:
    return all(importlib.util.find_spec(m) is not None for m in modules)


conv = _load()


class ConversionTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def convert(self, path: Path, **kwargs) -> tuple[bool, str, str]:
        out = path.with_suffix(".md")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ok = conv.convert_file(path, out, **kwargs)
        text = out.read_text(encoding="utf-8") if out.exists() else ""
        return ok, text, buf.getvalue()


@unittest.skipUnless(_has("docx"), "python-docx not installed")
class TestDocx(ConversionTestCase):
    def _fixture(self) -> Path:
        from docx import Document
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn

        doc = Document()
        doc.add_heading("Title", level=1)
        para = doc.add_paragraph("Kept ")
        # Tracked insertion and deletion inside the same paragraph.
        ins = OxmlElement("w:ins")
        ins.set(qn("w:id"), "1")
        ins.set(qn("w:author"), "t")
        run = OxmlElement("w:r")
        text = OxmlElement("w:t")
        text.text = "inserted"
        run.append(text)
        ins.append(run)
        para._p.append(ins)
        deletion = OxmlElement("w:del")
        deletion.set(qn("w:id"), "2")
        deletion.set(qn("w:author"), "t")
        del_run = OxmlElement("w:r")
        del_text = OxmlElement("w:delText")
        del_text.text = " removed"
        del_run.append(del_text)
        deletion.append(del_run)
        para._p.append(deletion)

        table = doc.add_table(rows=2, cols=2)
        table.cell(0, 0).text = "Name"
        table.cell(0, 1).text = "Value"
        table.cell(1, 0).text = "a|b"
        table.cell(1, 1).text = "42"
        doc.add_paragraph("After table")
        path = self.dir / "sample.docx"
        doc.save(path)
        return path

    def test_tracked_insertions_are_accepted_and_deletions_dropped(self) -> None:
        ok, text, _ = self.convert(self._fixture())
        self.assertTrue(ok)
        self.assertIn("# Title", text)
        self.assertIn("Kept inserted", text)
        self.assertNotIn("removed", text)

    def test_tables_are_kept_as_markdown_in_order(self) -> None:
        ok, text, _ = self.convert(self._fixture())
        self.assertTrue(ok)
        self.assertIn("| Name | Value |", text)
        self.assertIn("| --- | --- |", text)
        self.assertIn("| a\\|b | 42 |", text)
        self.assertLess(text.index("Kept inserted"), text.index("| Name"))
        self.assertLess(text.index("| Name"), text.index("After table"))


@unittest.skipUnless(_has("pandas", "openpyxl", "tabulate"), "pandas/openpyxl/tabulate not installed")
class TestXlsx(ConversionTestCase):
    def _fixture(self) -> Path:
        from openpyxl import Workbook

        wb = Workbook()
        visible = wb.active
        visible.title = "Data"
        visible.append(["col", "n"])
        visible.append(["shown", 1])
        hidden = wb.create_sheet("Secret")
        hidden.append(["col"])
        hidden.append(["internal-only"])
        hidden.sheet_state = "hidden"
        path = self.dir / "book.xlsx"
        wb.save(path)
        return path

    def test_hidden_sheets_are_skipped_by_default_and_reported(self) -> None:
        ok, text, stdout = self.convert(self._fixture())
        self.assertTrue(ok)
        self.assertIn("## Sheet: Data", text)
        self.assertIn("shown", text)
        self.assertNotIn("internal-only", text)
        self.assertIn("Skipped hidden sheets: Secret", text)
        self.assertIn("--include-hidden-sheets", stdout)

    def test_flag_includes_hidden_sheets_and_labels_them(self) -> None:
        ok, text, _ = self.convert(self._fixture(), include_hidden_sheets=True)
        self.assertTrue(ok)
        self.assertIn("## Sheet: Secret (hidden)", text)
        self.assertIn("internal-only", text)

    def test_cli_accepts_the_flag(self) -> None:
        path = self._fixture()
        with redirect_stdout(io.StringIO()):
            code = conv.main([str(path), "--include-hidden-sheets"])
        self.assertEqual(code, 0)
        self.assertIn("internal-only", path.with_suffix(".md").read_text(encoding="utf-8"))


class TestPdfFallback(ConversionTestCase):
    @unittest.skipUnless(_has("reportlab") and shutil.which("pdftotext"),
                         "reportlab or pdftotext not installed")
    def test_falls_back_to_pdftotext_without_pymupdf(self) -> None:
        from reportlab.pdfgen import canvas

        path = self.dir / "two.pdf"
        pdf = canvas.Canvas(str(path))
        pdf.drawString(72, 720, "First page text")
        pdf.showPage()
        pdf.drawString(72, 720, "Second page text")
        pdf.showPage()
        pdf.save()

        with mock.patch.dict(sys.modules, {"fitz": None}):
            ok, text, stdout = self.convert(path)
        self.assertTrue(ok)
        self.assertIn("pdftotext", stdout)
        self.assertIn("<!-- Page 1 -->", text)
        self.assertIn("<!-- Page 2 -->", text)
        self.assertNotIn("<!-- Page 3 -->", text)
        self.assertLess(text.index("First page text"), text.index("<!-- Page 2 -->"))
        self.assertIn("Second page text", text)

    def test_fails_cleanly_without_any_pdf_backend(self) -> None:
        path = self.dir / "none.pdf"
        path.write_bytes(b"%PDF-1.4\n")
        with mock.patch.dict(sys.modules, {"fitz": None}), \
                mock.patch.object(conv.shutil, "which", return_value=None), \
                mock.patch("sys.stderr", new_callable=io.StringIO) as err:
            ok, _, _ = self.convert(path)
        self.assertFalse(ok)
        self.assertIn("pdftotext", err.getvalue())


if __name__ == "__main__":
    unittest.main()
