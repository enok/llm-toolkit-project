from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAN = ROOT / "skills" / "folder-reorganization" / "scripts" / "reorg_scan.py"

FILES = {
    "README.md": b"Start at docs/readme.md\n",
    "desktop.ini": b"[.ShellClassInfo]\r\n",
    "docs/readme.md": b"Notes live in docs/old-notes/ now.\r\nAlso see docs\\old-notes\\b.md\r\n",
    "docs/moves.md": b"old: logs/2026-01-run.log\nnew: archive/logs/2026-01-run.log\n",
    "docs/old-notes/a.md": b"# A\n",
    "logs/2026-01-run.log": b"moved docs/old-notes/a.md\n",
    "data/image.png": b"\x89PNG\r\n\x1a\n\x00\x00docs/old-notes/a.md\x00",
    "data/blob.dat": b"\x00\x01docs/old-notes/a.md\x00\x02",
    ".git/config": b"[remote] url = docs/old-notes\n",
}
SHARED_STRINGS = ('<?xml version="1.0" encoding="UTF-8"?><sst><si><t>Link</t></si>'
                  "<si><t>docs/old-notes/a.md</t></si></sst>")
PATHMAP = """op,wave,action,old_path,new_path
1,1,mkdir,,archive
2,1,move,docs/old-notes,archive/notes
3,1,move,logs,archive/logs
"""
MTIME_RE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")


def build_tree(root: Path) -> None:
    for rel, data in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    with zipfile.ZipFile(root / "data" / "report.xlsx", "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types/>')
        z.writestr("xl/sharedStrings.xml", SHARED_STRINGS)
        z.writestr("xl/media/note.txt", "docs/old-notes/a.md")          # not an XML member: not scanned


def read_tsv(path: Path) -> tuple[list, list]:
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[-1] == "", "TSV must end with a newline"
    rows = [ln.split("\t") for ln in lines[:-1]]
    return rows[0], rows[1:]


class ReorgScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.root = self.base / "root"
        self.root.mkdir()
        build_tree(self.root)
        self.pathmap = self.base / "pathmap.csv"
        self.pathmap.write_text(PATHMAP, encoding="utf-8", newline="\n")
        self.out = self.base / "refscan.tsv"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def scan(self, *args, expect: int = 0) -> str:
        p = subprocess.run([sys.executable, "-B", str(SCAN), *[str(a) for a in args]], cwd=str(self.base),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = p.stdout + p.stderr
        self.assertEqual(p.returncode, expect, out)
        return out

    def refscan(self, *args) -> list:
        self.scan("refscan", "--root", self.root, "--out", self.out, *args)
        header, rows = read_tsv(self.out)
        self.assertEqual(header, ["file", "line", "class", "pattern", "snippet"])
        for r in rows:
            self.assertEqual(len(r), 5, r)
        return rows

    # inventory -------------------------------------------------------------
    def test_inventory_columns_and_area_totals(self) -> None:
        meta = self.root / "_meta"
        out = self.scan("inventory", "--root", self.root, "--out-dir", meta, "--label", "before")
        self.assertIn("inventory: 9 files", out)
        header, rows = read_tsv(meta / "before-inventory.tsv")
        self.assertEqual(header, ["rel_path", "bytes", "mtime_utc", "kind"])
        expected = sorted(set(FILES) - {"desktop.ini"} | {"data/report.xlsx"})
        self.assertEqual([r[0] for r in rows], expected)       # sorted, forward slashes, no _meta, no desktop.ini
        for rel, size, mtime, kind in rows:
            self.assertEqual(int(size), (self.root / rel).stat().st_size, rel)
            self.assertRegex(mtime, MTIME_RE)
            self.assertEqual(kind, "file")
        header, totals = read_tsv(meta / "before-area-totals.tsv")
        self.assertEqual(header, ["area", "files", "bytes"])
        got = {r[0]: (int(r[1]), int(r[2])) for r in totals}
        want = {}
        for rel, size, _, _ in rows:
            area = rel.split("/", 1)[0] if "/" in rel else "(root files)"
            n, b = want.get(area, (0, 0))
            want[area] = (n + 1, b + int(size))
        want["TOTAL"] = (len(rows), sum(int(r[1]) for r in rows))
        self.assertEqual(got, want)
        self.assertEqual(totals[-1][0], "TOTAL")
        self.assertEqual(got["(root files)"][0], 1)

    def test_inventory_ignore_and_skip_dir(self) -> None:
        self.scan("inventory", "--root", self.root, "--out-dir", self.base, "--label", "x",
                  "--ignore", "*.png", "--skip-dir", ".git", "--no-default-ignore")
        _, rows = read_tsv(self.base / "x-inventory.tsv")
        names = [r[0] for r in rows]
        self.assertNotIn("data/image.png", names)
        self.assertNotIn(".git/config", names)
        self.assertIn("desktop.ini", names)

    def test_inventory_rejects_bad_label(self) -> None:
        out = self.scan("inventory", "--root", self.root, "--out-dir", self.base, "--label", "a b", expect=1)
        self.assertIn("--label may contain only", out)

    # refscan ---------------------------------------------------------------
    def test_refscan_live_hits_in_markdown_both_separators(self) -> None:
        rows = self.refscan("--pathmap", self.pathmap)
        md = [r for r in rows if r[0] == "docs/readme.md"]
        self.assertEqual([(r[1], r[2], r[3]) for r in md],
                         [("1", "live", "docs/old-notes"), ("2", "live", "docs/old-notes")])
        self.assertEqual(md[0][4], "Notes live in docs/old-notes/ now.")
        self.assertNotIn("README.md", [r[0] for r in rows])

    def test_refscan_new_path_is_not_a_hit(self) -> None:
        rows = self.refscan("--pathmap", self.pathmap)
        moves = [(r[1], r[3]) for r in rows if r[0] == "docs/moves.md"]
        self.assertEqual(moves, [("1", "logs")])               # line 2 only names the new path archive/logs

    def test_refscan_historical_class_by_glob(self) -> None:
        rows = self.refscan("--pathmap", self.pathmap)
        self.assertEqual({r[2] for r in rows if r[0] == "logs/2026-01-run.log"}, {"live"})
        rows = self.refscan("--pathmap", self.pathmap, "--historical", "logs")
        log = [r for r in rows if r[0] == "logs/2026-01-run.log"]
        self.assertEqual([(r[1], r[2], r[3]) for r in log], [("1", "historical", "docs/old-notes")])
        self.assertEqual({r[2] for r in rows if r[0] != "logs/2026-01-run.log"}, {"live"})

    def test_refscan_skips_binaries_and_default_skip_dirs(self) -> None:
        out = self.scan("refscan", "--root", self.root, "--out", self.out, "--pathmap", self.pathmap)
        self.assertIn("2 binary skipped", out)
        _, rows = read_tsv(self.out)
        files = {r[0] for r in rows}
        self.assertNotIn("data/image.png", files)
        self.assertNotIn("data/blob.dat", files)
        self.assertNotIn(".git/config", files)

    def test_refscan_hit_inside_xlsx_member(self) -> None:
        rows = self.refscan("--pathmap", self.pathmap)
        xl = [r for r in rows if r[0] == "data/report.xlsx"]
        self.assertEqual([(r[1], r[2], r[3]) for r in xl], [("xl/sharedStrings.xml", "live", "docs/old-notes")])
        self.assertIn("<t>docs/old-notes/a.md</t>", xl[0][4])

    def test_refscan_raw_pattern_and_output_inside_root(self) -> None:
        self.out = self.root / "refscan.tsv"
        rows = self.refscan("--pattern", r"Start at \S+")
        self.assertEqual([(r[0], r[1], r[3]) for r in rows], [("README.md", "1", r"Start at \S+")])
        rows = self.refscan("--pattern", r"Start at \S+", "--pattern", "refscan")
        self.assertNotIn("refscan.tsv", [r[0] for r in rows])  # its own output file is never scanned

    def test_refscan_needs_a_pattern_source(self) -> None:
        out = self.scan("refscan", "--root", self.root, "--out", self.out, expect=2)
        self.assertIn("refscan needs --pathmap or --pattern", out)
        self.assertFalse(self.out.exists())


if __name__ == "__main__":
    unittest.main()
