#!/usr/bin/env python3
"""Render the "CV markdown format" to an ATS-safe DOCX and, optionally, a PDF.

    render_cv.py --in cv.md --out-dir DIR [--basename NAME] [--pdf]
                 [--footer "{page} of {total}"] [--allow-fill]
                 [--font Calibri|Arial] [--size 10.5|11] [--paper letter|a4]

CV markdown format (one line = one paragraph; a line indented, or directly
following a bullet/paragraph without a blank line and not starting with a
bold label, continues the previous one):

    # Full Name
    contact | items | separated | by pipes
    ## Summary / Skills / Experience / Education / Certifications / Languages
    **Group:** a, b, c                       (skills line)
    ### Title - Company                      (entry heading)
    *Location | YYYY-MM - YYYY-MM*           (italic meta line)
    - bullet  <!-- kw: java; spring --> <!-- src: master.md section -->

Every HTML comment (also multi-line) is stripped. `**bold**` is supported
inline; `[text](url)` is flattened to plain text. A `[FILL: ...]` marker means
a fact the owner must supply: rendering is refused (exit 2) while one remains
in the rendered text, unless --allow-fill is given (then it is kept visibly and
reported as a warning).

Layout: single column; no tables, text boxes, images or header content;
Calibri/Arial 10.5-11 pt body; headings are real Heading 1/2/3 paragraph
styles. --footer takes a template with {page} and {total} that is written
right-aligned into the footer using real PAGE / NUMPAGES field codes.

--pdf converts the DOCX with `soffice --headless --convert-to pdf`. soffice is
looked up on PATH, then in the usual Windows (Program Files\\LibreOffice) and
macOS install locations. When it is missing or the conversion fails, a warning
is added, no PDF is produced and the exit code stays 0.

Prints one JSON object: {"docx": path, "pdf": path|null, "warnings": [...]}.
Exit codes: 0 ok, 2 usage/input error (missing python-docx, unreadable input,
[FILL left), 4 output not writable (for example the DOCX is open in Word).
Runs on Windows, macOS and Linux with Python 3.9+ and python-docx.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

EXIT_OK, EXIT_USAGE, EXIT_WRITE = 0, 2, 4

INSTALL_HINT = "python-docx is required: python -m pip install python-docx"

COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
FILL_RE = re.compile(r"\[\s*FILL(?![A-Za-z])", re.I)
CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f￾￿]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^(\s*)([-*+•])\s+(.*\S)\s*$")
RULE_RE = re.compile(r"^\s*([-*_])(?:\s*\1){2,}\s*$")
LABEL_RE = re.compile(r"^\*\*[^*]+\*\*")
META_RE = re.compile(r"^\*[^*\s][^*]*\*$")
INLINE_RE = re.compile(
    r"\*\*(?P<b>.+?)\*\*"
    r"|(?<![\w*])\*(?P<i>[^\s*](?:[^*]*[^\s*])?)\*(?![\w*])"
    r"|\[(?P<lt>[^\]]+)\]\((?P<lu>[^)\s]+)\)"
)
FOOTER_TOKEN_RE = re.compile(r"(\{[A-Za-z_]+\})")
FOOTER_FIELDS = {"{page}": "PAGE", "{total}": "NUMPAGES"}


# ---------------------------------------------------------------- parsing

def strip_comments(text: str) -> tuple[str, list[str]]:
    """Remove every HTML comment, keeping line numbers stable."""
    warnings: list[str] = []
    out = COMMENT_RE.sub(lambda m: "\n" * m.group(0).count("\n"), text)
    if "<!--" in out:
        out = re.sub(r"<!--[^\n]*", "", out)
        warnings.append("unterminated HTML comment removed up to the end of its line")
    return out, warnings


def find_fill(text: str) -> list[tuple[int, str]]:
    """Return (line number, line text) for every line that holds a [FILL marker."""
    return [(n, line.strip()) for n, line in enumerate(text.splitlines(), 1) if FILL_RE.search(line)]


@dataclass
class Block:
    kind: str  # name | contact | section | entry | subentry | meta | bullet | para
    text: str
    level: int = 1
    line: int = 0


_CONTINUABLE = {"contact", "para", "bullet"}


def parse_cv(text: str) -> list[Block]:
    """Parse already comment-stripped CV markdown into blocks."""
    blocks: list[Block] = []
    expect_contact = False
    prev_blank = True
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip():
            prev_blank = True
            continue
        contiguous = not prev_blank
        prev_blank = False

        heading = HEADING_RE.match(line)
        if heading:
            depth = len(heading.group(1))
            kind = {1: "name", 2: "section", 3: "entry"}.get(depth, "subentry")
            blocks.append(Block(kind, heading.group(2), line=number))
            expect_contact = depth == 1
            continue
        if RULE_RE.match(line):
            continue
        bullet = BULLET_RE.match(line)
        if bullet:
            indent = len(bullet.group(1).expandtabs(4))
            blocks.append(Block("bullet", bullet.group(3), level=2 if indent >= 2 else 1, line=number))
            expect_contact = False
            continue

        stripped = line.strip()
        if expect_contact:
            blocks.append(Block("contact", stripped, line=number))
            expect_contact = False
            continue
        if META_RE.match(stripped):
            blocks.append(Block("meta", stripped, line=number))
            continue
        previous = blocks[-1] if blocks else None
        indented = line[0] in " \t"
        if (previous is not None and contiguous and previous.kind in _CONTINUABLE
                and (indented or not LABEL_RE.match(stripped))):
            previous.text += " " + stripped
            continue
        blocks.append(Block("para", stripped, line=number))
    for block in blocks:
        block.text = " ".join(block.text.split())
    return blocks


def parse_inline(text: str) -> list[tuple[str, bool, bool]]:
    """Split text into (segment, bold, italic) runs. Links become plain text."""
    runs: list[tuple[str, bool, bool]] = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            runs.append((text[pos:m.start()], False, False))
        if m.group("b") is not None:
            runs.append((m.group("b"), True, False))
        elif m.group("i") is not None:
            runs.append((m.group("i"), False, True))
        else:
            label, url = m.group("lt").strip(), m.group("lu")
            runs.append((url if label == url else f"{label} ({url})", False, False))
        pos = m.end()
    if pos < len(text):
        runs.append((text[pos:], False, False))
    return runs


# ------------------------------------------------------------------- docx

def have_docx() -> bool:
    try:
        import docx  # noqa: F401
    except ImportError:
        return False
    return True


def _set_fonts(rpr, font: str) -> None:
    """Pin a run-properties element to a concrete font (drop theme font links)."""
    from docx.oxml.ns import qn

    rfonts = rpr.get_or_add_rFonts()
    for attr in ("asciiTheme", "hAnsiTheme", "eastAsiaTheme", "cstheme"):
        rfonts.attrib.pop(qn("w:" + attr), None)
    for attr in ("ascii", "hAnsi", "eastAsia", "cs"):
        rfonts.set(qn("w:" + attr), font)


_AFTER_PBDR = (
    "w:shd", "w:tabs", "w:suppressAutoHyphens", "w:kinsoku", "w:wordWrap", "w:overflowPunct",
    "w:topLinePunct", "w:autoSpaceDE", "w:autoSpaceDN", "w:bidi", "w:adjustRightInd",
    "w:snapToGrid", "w:spacing", "w:ind", "w:contextualSpacing", "w:mirrorIndents",
    "w:suppressOverlap", "w:jc", "w:textDirection", "w:textAlignment", "w:textboxTightWrap",
    "w:outlineLvl", "w:divId", "w:cnfStyle", "w:rPr", "w:sectPr", "w:pPrChange",
)


def _set_bottom_border(style, color: str = "808080") -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    ppr = style.element.get_or_add_pPr()
    for old in ppr.findall(qn("w:pBdr")):
        ppr.remove(old)
    border = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    for key, value in (("val", "single"), ("sz", "4"), ("space", "1"), ("color", color)):
        bottom.set(qn("w:" + key), value)
    border.append(bottom)
    ppr.insert_element_before(border, *_AFTER_PBDR)


def _clear_border(style) -> None:
    from docx.oxml.ns import qn

    ppr = style.element.pPr
    if ppr is not None:
        for old in ppr.findall(qn("w:pBdr")):
            ppr.remove(old)


def _style_document(doc, font: str, size: float) -> None:
    from docx.enum.style import WD_STYLE_TYPE
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.shared import Pt, RGBColor

    black = RGBColor(0, 0, 0)

    defaults = doc.styles.element.find(qn("w:docDefaults"))
    if defaults is not None:
        rpr_default = defaults.find(qn("w:rPrDefault"))
        rpr = rpr_default.find(qn("w:rPr")) if rpr_default is not None else None
        if rpr is not None:
            _set_fonts(rpr, font)

    def configure(name, pt, bold=False, italic=False, before=0.0, after=0.0, keep_next=False):
        style = doc.styles[name]
        _set_fonts(style.element.get_or_add_rPr(), font)
        style.font.size = Pt(pt)
        style.font.bold = bold
        style.font.italic = italic
        style.font.color.rgb = black
        fmt = style.paragraph_format
        fmt.space_before = Pt(before)
        fmt.space_after = Pt(after)
        fmt.line_spacing = 1.0
        fmt.keep_with_next = keep_next
        return style

    configure("Normal", size, after=2.5)
    title = configure("Title", 18, bold=True, after=2, keep_next=True)
    title.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _clear_border(title)
    h1 = configure("Heading 1", size + 1.5, bold=True, before=9, after=3, keep_next=True)
    _set_bottom_border(h1)
    configure("Heading 2", size + 0.5, bold=True, before=5, after=0.5, keep_next=True)
    configure("Heading 3", size, bold=True, italic=True, before=3, after=0.5, keep_next=True)
    configure("List Bullet", size, after=1.5)
    configure("List Bullet 2", size, after=1.5)
    configure("Footer", 9, after=0)

    contact = doc.styles.add_style("CV Contact", WD_STYLE_TYPE.PARAGRAPH)
    contact.base_style = doc.styles["Normal"]
    contact.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contact.paragraph_format.space_after = Pt(4)
    meta = doc.styles.add_style("CV Meta", WD_STYLE_TYPE.PARAGRAPH)
    meta.base_style = doc.styles["Normal"]
    meta.font.italic = True
    meta.paragraph_format.space_after = Pt(1.5)
    meta.paragraph_format.keep_with_next = True


def _add_runs(paragraph, text: str) -> None:
    for segment, bold, italic in parse_inline(text):
        run = paragraph.add_run(segment)
        if bold:
            run.bold = True
        if italic:
            run.italic = True


def _add_field(paragraph, instruction: str, placeholder: str = "1") -> None:
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn

    def char(kind: str) -> None:
        element = OxmlElement("w:fldChar")
        element.set(qn("w:fldCharType"), kind)
        paragraph.add_run()._r.append(element)

    char("begin")
    code = OxmlElement("w:instrText")
    code.set(qn("xml:space"), "preserve")
    code.text = f" {instruction} "
    paragraph.add_run()._r.append(code)
    char("separate")
    paragraph.add_run(placeholder)
    char("end")


def _add_footer(doc, template: str, warnings: list[str]) -> None:
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    footer = doc.sections[0].footer
    footer.is_linked_to_previous = False
    paragraph = footer.paragraphs[0]
    paragraph.style = doc.styles["Footer"]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    for part in FOOTER_TOKEN_RE.split(template):
        if not part:
            continue
        if part in FOOTER_FIELDS:
            _add_field(paragraph, FOOTER_FIELDS[part])
            continue
        if FOOTER_TOKEN_RE.fullmatch(part):
            warnings.append(f"unknown footer placeholder {part} left as literal text (use {{page}} / {{total}})")
        paragraph.add_run(part)


def build_docx(blocks: list[Block], *, font: str, size: float, paper: str, footer: str | None,
               warnings: list[str]):
    from docx import Document
    from docx.shared import Inches, Mm

    doc = Document()
    _style_document(doc, font, size)

    section = doc.sections[0]
    if paper == "a4":
        section.page_width, section.page_height = Mm(210), Mm(297)
    else:
        section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.left_margin = section.right_margin = Inches(0.75)
    section.top_margin = section.bottom_margin = Inches(0.7)
    section.header_distance = section.footer_distance = Inches(0.4)

    styles = {"name": "Title", "contact": "CV Contact", "section": "Heading 1", "entry": "Heading 2",
              "subentry": "Heading 3", "meta": "CV Meta", "para": "Normal"}
    for block in blocks:
        if block.kind == "bullet":
            style = "List Bullet 2" if block.level > 1 else "List Bullet"
        else:
            style = styles[block.kind]
        paragraph = doc.add_paragraph(style=style)
        if block.kind in ("name", "section", "entry", "subentry"):
            paragraph.add_run(" ".join(p[0] for p in parse_inline(block.text)))
        else:
            _add_runs(paragraph, block.text)
        if "**" in paragraph.text:
            warnings.append(f"line {block.line}: unbalanced ** bold markers left in the text")

    if footer:
        _add_footer(doc, footer, warnings)

    name = next((b.text for b in blocks if b.kind == "name"), "")
    props = doc.core_properties
    props.author = props.last_modified_by = ""
    props.comments = props.keywords = props.subject = ""
    props.title = name or "CV"
    props.created = props.modified = dt.datetime.now(dt.timezone.utc).replace(microsecond=0, tzinfo=None)
    return doc


# -------------------------------------------------------------------- pdf

def find_soffice() -> str | None:
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    candidates: list[Path] = []
    if sys.platform.startswith("win"):
        for var in ("ProgramFiles", "ProgramW6432", "ProgramFiles(x86)"):
            base = os.environ.get(var)
            if base:
                candidates.append(Path(base) / "LibreOffice" / "program" / "soffice.exe")
    elif sys.platform == "darwin":
        candidates.append(Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"))
    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return None


def convert_to_pdf(soffice: str, docx_path: Path, out_dir: Path, timeout: int = 180) -> tuple[Path | None, str | None]:
    """Convert with a throw-away LibreOffice profile (a running GUI instance would otherwise swallow the job)."""
    pdf_path = out_dir / (docx_path.stem + ".pdf")
    try:
        pdf_path.unlink()
    except FileNotFoundError:
        pass
    except OSError as exc:
        return None, f"PDF skipped: cannot replace existing {pdf_path.name} ({exc})"
    profile = tempfile.mkdtemp(prefix="render_cv_lo_")
    cmd = [soffice, f"-env:UserInstallation={Path(profile).resolve().as_uri()}", "--headless",
           "--convert-to", "pdf", "--outdir", str(out_dir), str(docx_path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        return None, f"PDF skipped: soffice did not finish within {timeout}s"
    except OSError as exc:
        return None, f"PDF skipped: could not run soffice ({exc})"
    finally:
        shutil.rmtree(profile, ignore_errors=True)
    if proc.returncode != 0 or not pdf_path.is_file():
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return None, "PDF skipped: soffice conversion failed" + (f" ({detail[-1]})" if detail else "")
    return pdf_path, None


# -------------------------------------------------------------------- cli

def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render CV markdown to an ATS-safe DOCX (and optional PDF).")
    parser.add_argument("--in", dest="in_path", required=True, help="CV markdown file")
    parser.add_argument("--out-dir", required=True, help="output directory (created if missing)")
    parser.add_argument("--basename", help="output file name without extension (default: input file stem)")
    parser.add_argument("--pdf", action="store_true", help="also convert to PDF with soffice (skipped with a warning when absent)")
    parser.add_argument("--footer", help='footer template, e.g. "{page} of {total}" (right-aligned, real PAGE/NUMPAGES fields)')
    parser.add_argument("--allow-fill", action="store_true", help="render even if [FILL: ...] markers remain")
    parser.add_argument("--font", choices=("Calibri", "Arial"), default="Calibri")
    parser.add_argument("--size", type=float, choices=(10.5, 11.0), default=10.5, help="body font size in pt")
    parser.add_argument("--paper", choices=("letter", "a4"), default="letter")
    return parser.parse_args(argv)


def fail(message: str, code: int = EXIT_USAGE) -> int:
    sys.stderr.write(message.rstrip("\n") + "\n")
    return code


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if not have_docx():
        return fail(INSTALL_HINT)

    in_path = Path(args.in_path)
    try:
        raw = in_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return fail(f"cannot read --in {in_path}: {exc}")

    basename = args.basename if args.basename else in_path.stem
    if basename.lower().endswith(".docx"):
        basename = basename[:-5]
    if not basename or any(sep in basename for sep in ("/", "\\")) or basename in (".", ".."):
        return fail(f"invalid --basename {args.basename!r}: give a plain file name without directories")

    warnings: list[str] = []
    text, comment_warnings = strip_comments(CONTROL_RE.sub("", raw))
    warnings.extend(comment_warnings)

    fills = find_fill(text)
    if fills:
        listing = "; ".join(f"line {n}: {t[:70]}" for n, t in fills[:10])
        if not args.allow_fill:
            return fail(f"refusing to render: {len(fills)} [FILL] placeholder(s) remain ({listing}). "
                        "Supply the facts or pass --allow-fill.")
        warnings.append(f"{len(fills)} [FILL] placeholder(s) kept in the document ({listing})")

    blocks = parse_cv(text)
    if not blocks:
        return fail(f"nothing to render: {in_path} has no content")
    if not any(b.kind == "name" for b in blocks):
        warnings.append("no '# Full Name' heading found")

    doc = build_docx(blocks, font=args.font, size=args.size, paper=args.paper,
                     footer=args.footer, warnings=warnings)

    out_dir = Path(args.out_dir).resolve()
    docx_path = out_dir / f"{basename}.docx"
    tmp_path = out_dir / f".{basename}.docx.tmp"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        doc.save(str(tmp_path))
        os.replace(tmp_path, docx_path)
    except OSError as exc:
        try:
            tmp_path.unlink()
        except OSError:
            pass
        return fail(f"cannot write {docx_path}: {exc} (is it open in Word?)", EXIT_WRITE)

    pdf_path = None
    if args.pdf:
        soffice = find_soffice()
        if soffice is None:
            warnings.append("PDF skipped: LibreOffice (soffice) not found on PATH or in the standard "
                            "install locations; install LibreOffice to enable --pdf")
        else:
            pdf_path, warning = convert_to_pdf(soffice, docx_path, out_dir)
            if warning:
                warnings.append(warning)

    print(json.dumps({"docx": str(docx_path), "pdf": str(pdf_path) if pdf_path else None,
                      "warnings": warnings}))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
