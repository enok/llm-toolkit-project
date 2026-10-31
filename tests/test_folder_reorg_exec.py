from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "folder-reorganization" / "scripts"
EXEC = SCRIPTS / "reorg_exec.py"
SCAN = SCRIPTS / "reorg_scan.py"

SHARED_STRINGS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="2" uniqueCount="2">'
    "<si><t>Link</t></si><si><t>docs/old-notes/a.md</t></si></sst>"
)
XLSX_MEMBERS = [
    ("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/'
                            'package/2006/content-types"><Default Extension="xml" '
                            'ContentType="application/xml"/></Types>'),
    ("xl/workbook.xml", '<?xml version="1.0" encoding="UTF-8"?><workbook><sheets><sheet name="Sheet1" sheetId="1"/>'
                        "</sheets></workbook>"),
    ("xl/worksheets/sheet1.xml", '<?xml version="1.0" encoding="UTF-8"?><worksheet><sheetData><row r="1">'
                                 '<c r="A1" t="s"><v>1</v></c></row></sheetData></worksheet>'),
    ("xl/sharedStrings.xml", SHARED_STRINGS),
]
FILES = {
    "README.md": b"Start at docs/readme.md\n",
    "desktop.ini": b"[.ShellClassInfo]\r\n",
    "docs/readme.md": b"Notes live in docs/old-notes/ now.\n",
    "docs/crlf.txt": b"line one\r\nsee docs/old-notes/a.md\r\n",
    "docs/desktop.ini": b"[.ShellClassInfo]\r\n",
    "docs/old-notes/a.md": b"# A\n\nSee docs/old-notes/b.md\n",
    "docs/old-notes/b.md": b"# B\n",
    "logs/2026-01-run.log": b"moved docs/old-notes/a.md\n",
    "src/Main.java": b"class Main {}\n",
    "data/image.png": b"\x89PNG\r\n\x1a\n\x00\x00docs/old-notes/a.md\x00",
    "data/blob.dat": b"\x00\x01docs/old-notes/a.md\x00\x02",
}
PATHMAP = """op,wave,action,old_path,new_path
1,1,mkdir,,archive
2,1,mkdir,,archive/spare
3,1,move,docs/old-notes,archive/notes
4,2,move,logs,archive/logs
5,2,rename,src/Main.java,src/main.java
"""
EDITS = {
    "edits": [
        {"file": "archive/notes/a.md", "kind": "text",
         "replacements": [{"old": "docs/old-notes/b.md", "new": "archive/notes/b.md", "count": 1}]},
        {"file": "docs/readme.md", "kind": "text",
         "replacements": [{"old": "docs/old-notes/", "new": "archive/notes/", "count": 1}]},
        {"file": "docs/crlf.txt", "kind": "text",
         "replacements": [{"old": "docs/old-notes/a.md", "new": "archive/notes/a.md", "count": 1}]},
        {"file": "data/report.xlsx", "kind": "xlsx-xml",
         "replacements": [{"old": "xl/sharedStrings.xml|docs/old-notes/a.md", "new": "archive/notes/a.md",
                           "count": 1}]},
    ],
    "whitelist": [{"file_prefix": "archive/logs/", "why": "historical run log, kept as written"}],
}
FINAL_FILES = {
    "README.md", "desktop.ini", "docs/readme.md", "docs/crlf.txt", "docs/desktop.ini", "archive/notes/a.md",
    "archive/notes/b.md", "archive/logs/2026-01-run.log", "src/main.java", "data/image.png", "data/blob.dat",
    "data/report.xlsx",
}


def make_xlsx(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as z:
        for i, (name, text) in enumerate(XLSX_MEMBERS):
            info = zipfile.ZipInfo(name, date_time=(2024, 1, 2, 3, 4, 6 + 2 * i))
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, text.encode("utf-8"))


def build_tree(root: Path) -> None:
    for rel, data in FILES.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    make_xlsx(root / "data" / "report.xlsx")
    (root / "empty-existing").mkdir()


def state(root: Path, skip_meta: bool = True) -> tuple[dict, set]:
    """-> ({posix rel: bytes}, {posix rel dir}) with on-disk name case; the _meta dir is left out by default."""
    files, dirs = {}, set()
    for dp, dns, fns in os.walk(root):
        if skip_meta and Path(dp) == root:
            dns[:] = [d for d in dns if d != "_meta"]
        for d in dns:
            dirs.add(Path(os.path.relpath(os.path.join(dp, d), root)).as_posix())
        for fn in fns:
            full = os.path.join(dp, fn)
            files[Path(os.path.relpath(full, root)).as_posix()] = Path(full).read_bytes()
    return files, dirs


def zip_members(data: bytes) -> list:
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        return [(i.filename, i.date_time, i.compress_type, z.read(i)) for i in z.infolist()]


class ReorgExecTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.base = Path(self._tmp.name)
        self.root = self.base / "root"
        self.meta = self.root / "_meta"
        self.root.mkdir()
        build_tree(self.root)
        self.original = state(self.root)
        self.pathmap = self.write("pathmap.csv", PATHMAP)
        self.edits = self.write("edits.json", json.dumps(EDITS, indent=2))
        self.inv = self.meta / "before-inventory.tsv"
        self.bakdir = self.meta / "reorg-edit-backups"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # helpers ---------------------------------------------------------------
    def write(self, name: str, text: str) -> Path:
        p = self.base / name
        p.write_text(text, encoding="utf-8", newline="\n")
        return p

    def run_script(self, script: Path, *args, expect: int = 0) -> str:
        p = subprocess.run([sys.executable, "-B", str(script), *[str(a) for a in args]], cwd=str(self.base),
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = p.stdout + p.stderr
        self.assertEqual(p.returncode, expect, out)
        return out

    def rx(self, mode: str, *args, expect: int = 0) -> str:
        return self.run_script(EXEC, mode, "--root", self.root, "--meta", self.meta, *args, expect=expect)

    def inventory(self) -> Path:
        self.run_script(SCAN, "inventory", "--root", self.root, "--out-dir", self.meta, "--label", "before")
        return self.inv

    def snapshot_and_run(self, pathmap: Path | None = None) -> None:
        pm = pathmap or self.pathmap
        self.rx("snapshot", "--pathmap", pm, "--edits", self.edits)
        self.rx("run", "--pathmap", pm)

    def full_flow(self) -> None:
        self.inventory()
        self.snapshot_and_run()
        self.rx("edits", "--edits", self.edits)

    def names(self, rel: str) -> list:
        return sorted(os.listdir(self.root / rel))

    def edited_bytes(self) -> dict:
        return {
            "archive/notes/a.md": b"# A\n\nSee archive/notes/b.md\n",
            "docs/readme.md": b"Notes live in archive/notes/ now.\n",
            "docs/crlf.txt": b"line one\r\nsee archive/notes/a.md\r\n",
        }

    # full flow -------------------------------------------------------------
    def test_full_flow_end_to_end(self) -> None:
        inv = self.inventory()
        out = self.run_script(EXEC, "plan-check", "--pathmap", self.pathmap, "--inventory", inv,
                              "--edits", self.edits)
        self.assertIn("plan-check: OK", out)
        before_meta = state(self.root, skip_meta=False)
        out = self.rx("preflight", "--pathmap", self.pathmap, "--inventory", inv, "--edits", self.edits)
        self.assertIn("preflight: OK", out)
        self.assertEqual(state(self.root, skip_meta=False), before_meta, "preflight must write nothing")
        self.rx("snapshot", "--pathmap", self.pathmap, "--edits", self.edits)
        self.assertTrue((self.meta / "reorg-tree-before.txt").is_file())
        self.assertTrue((self.meta / "reorg-rollback.ps1").is_file())
        out = self.rx("run", "--pathmap", self.pathmap)
        self.assertIn("ok=5, skip-done=0", out)
        out = self.rx("edits", "--edits", self.edits)
        self.assertIn("edits: 4 files applied, 0 already applied", out)
        self.rx("verify", "--pathmap", self.pathmap, "--inventory", inv, "--edits", self.edits)
        report = (self.meta / "reorg-verify.txt").read_text(encoding="utf-8")
        self.assertIn("RESULT: OK", report)
        self.assertRegex(report, r"covered by whitelist\s+: 1\n")
        self.rx("tree-after")
        files, dirs = state(self.root)
        self.assertEqual(set(files), FINAL_FILES)
        self.assertNotIn("docs/old-notes", dirs)
        self.assertNotIn("logs", dirs)
        self.assertIn("archive/spare", dirs)
        self.assertIn("empty-existing", dirs)
        for rel, data in self.edited_bytes().items():
            self.assertEqual(files[rel], data, rel)
        self.assertEqual(files["archive/notes/b.md"], self.original[0]["docs/old-notes/b.md"])
        self.assertEqual(sorted(os.listdir(self.bakdir)),
                         sorted(e["file"].replace("/", "__") for e in EDITS["edits"]))
        self.assertFalse((self.meta / "reorg-tmp").exists())
        tree_after = (self.meta / "reorg-tree-after.txt").read_text(encoding="utf-8").splitlines()
        self.assertEqual(tree_after[0], "rel_path\tbytes\tmtime_utc")
        self.assertEqual(len(tree_after) - 1, len(FINAL_FILES) - 2)        # desktop.ini x2 ignored
        log = (self.meta / "reorg-log.md").read_text(encoding="utf-8")
        self.assertIn("mode=run", log)
        self.assertIn("mode=edits", log)

    def test_xlsx_edit_keeps_untouched_members_byte_identical(self) -> None:
        self.full_flow()
        before = zip_members(self.original[0]["data/report.xlsx"])
        after = zip_members((self.root / "data" / "report.xlsx").read_bytes())
        self.assertEqual([m[:3] for m in before], [m[:3] for m in after])
        for b, a in zip(before, after):
            if b[0] == "xl/sharedStrings.xml":
                self.assertEqual(a[3], b[3].replace(b"docs/old-notes/a.md", b"archive/notes/a.md"))
            else:
                self.assertEqual(a[3], b[3], b[0])
        self.rx("verify", "--pathmap", self.pathmap, "--inventory", self.inv, "--edits", self.edits)
        report = (self.meta / "reorg-verify.txt").read_text(encoding="utf-8")
        self.assertIn("3 untouched members byte-identical, 1 changed members as expected, 0 problem(s)", report)

    def test_resume_run_and_edits_are_idempotent(self) -> None:
        self.full_flow()
        done = state(self.root)
        out = self.rx("run", "--pathmap", self.pathmap)
        self.assertIn("ok=0, skip-done=5", out)
        out = self.rx("edits", "--edits", self.edits)
        self.assertIn("edits: 0 files applied, 4 already applied", out)
        self.assertEqual(out.count("already-applied:"), 4)
        self.assertEqual(state(self.root), done)

    def test_stop_after_partial_run_then_resume(self) -> None:
        self.rx("snapshot", "--pathmap", self.pathmap)
        out = self.rx("run", "--pathmap", self.pathmap, "--stop-after", "3")
        self.assertIn("partial run: ops with id <= 3 (3 of 5)", out)
        self.assertIn("ok=3, skip-done=0", out)
        self.assertEqual(self.names("archive"), ["notes", "spare"])
        self.assertIn("logs", self.names("."))
        self.assertEqual(self.names("src"), ["Main.java"])
        out = self.rx("run", "--pathmap", self.pathmap)
        self.assertIn("ok=2, skip-done=3", out)
        self.assertEqual(self.names("archive"), ["logs", "notes", "spare"])
        self.assertEqual(self.names("src"), ["main.java"])

    # rollback --------------------------------------------------------------
    def test_python_rollback_restores_tree_and_edited_bytes(self) -> None:
        self.full_flow()
        out = self.rx("rollback", "--pathmap", self.pathmap, "--edits", self.edits)
        self.assertIn("rolled back 3 moves", out)
        self.assertIn("IDENTICAL", out)
        self.assertIn("left in place: 2", out)
        tb = (self.meta / "reorg-tree-before.txt").read_text(encoding="utf-8")
        self.assertEqual((self.meta / "reorg-tree-rolledback.txt").read_text(encoding="utf-8"), tb)
        files, dirs = state(self.root)
        self.assertEqual(files, self.original[0])          # every byte, edited files included
        self.assertEqual(dirs - self.original[1], {"archive", "archive/spare"})
        self.assertEqual(self.names("src"), ["Main.java"])

    def test_case_only_rename_and_its_rollback(self) -> None:
        self.snapshot_and_run()
        self.assertEqual(self.names("src"), ["main.java"])
        self.assertEqual((self.root / "src" / "main.java").read_bytes(), FILES["src/Main.java"])
        out = self.rx("rollback", "--pathmap", self.pathmap)
        self.assertIn("IDENTICAL", out)
        self.assertEqual(self.names("src"), ["Main.java"])

    def test_rollback_prune_empty_removes_only_empty_created_dirs(self) -> None:
        self.full_flow()
        (self.root / "archive" / "desktop.ini").write_bytes(b"[.ShellClassInfo]\r\n")   # sync-client churn
        out = self.rx("rollback", "--pathmap", self.pathmap, "--edits", self.edits, "--prune-empty")
        self.assertIn("pruned 1 empty mkdir-created directories, kept 1 that are not empty", out)
        self.assertIn("IDENTICAL", out)
        self.assertFalse((self.root / "archive" / "spare").exists())
        self.assertEqual(self.names("archive"), ["desktop.ini"])
        self.assertTrue((self.root / "empty-existing").is_dir())
        files, _ = state(self.root)
        files.pop("archive/desktop.ini")
        self.assertEqual(files, self.original[0])

    @unittest.skipUnless(
        sys.platform == "win32" and (shutil.which("powershell") or shutil.which("pwsh")),
        "the generated rollback script targets Windows PowerShell paths",
    )
    def test_powershell_rollback_script(self) -> None:
        self.full_flow()
        exe = shutil.which("powershell") or shutil.which("pwsh")
        cmd = [exe, "-NoProfile", "-NonInteractive"]
        if os.name == "nt":
            cmd += ["-ExecutionPolicy", "Bypass"]
        cmd += ["-File", str(self.meta / "reorg-rollback.ps1"), "-PruneEmpty"]
        p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        files, dirs = state(self.root)
        self.assertEqual(files, self.original[0])
        self.assertEqual(dirs, self.original[1])
        self.assertEqual(self.names("src"), ["Main.java"])
        self.rx("tree-after")
        self.assertEqual((self.meta / "reorg-tree-after.txt").read_text(encoding="utf-8"),
                         (self.meta / "reorg-tree-before.txt").read_text(encoding="utf-8"))

    # plan-check / preflight negatives ----------------------------------------
    def test_plan_check_reports_collision_and_missing_source(self) -> None:
        inv = self.inventory()
        bad = self.write("bad-pathmap.csv", "op,wave,action,old_path,new_path\n"
                                            "1,1,move,docs/readme.md,README.md\n"
                                            "2,1,move,nope/x.md,docs/x.md\n")
        before = state(self.root, skip_meta=False)
        out = self.run_script(EXEC, "plan-check", "--pathmap", bad, "--inventory", inv, expect=1)
        self.assertIn("op 1 move: destination already exists: README.md", out)
        self.assertIn("COLLISION: 2 files end up at", out)
        self.assertIn("op 2 move: source missing: nope/x.md", out)
        self.assertEqual(state(self.root, skip_meta=False), before)

    def test_inventory_error_rows_are_refused(self) -> None:
        inv = self.write("err-inventory.tsv", "rel_path\tbytes\tmtime_utc\tkind\n"
                                              "README.md\t24\t2026-01-01T00:00:00Z\tfile\n"
                                              "docs/locked.md\t-1\t\tERR [Errno 13] Permission denied\n")
        out = self.run_script(EXEC, "plan-check", "--pathmap", self.pathmap, "--inventory", inv, expect=1)
        self.assertIn("is an error row", out)

    def assert_preflight_refuses(self, expected: str, pathmap: Path | None = None) -> None:
        before = state(self.root, skip_meta=False)
        out = self.rx("preflight", "--pathmap", pathmap or self.pathmap, "--inventory", self.inv,
                      "--edits", self.edits, expect=1)
        self.assertIn(expected, out)
        self.assertEqual(state(self.root, skip_meta=False), before, "preflight must change nothing")

    def test_preflight_refuses_lock_file(self) -> None:
        self.inventory()
        (self.root / "data" / "~$report.xlsx").write_bytes(b"lock")
        self.assert_preflight_refuses("lock file present (close the application that owns it): data/~$report.xlsx")

    def test_preflight_refuses_existing_mkdir_target(self) -> None:
        self.inventory()
        (self.root / "archive").mkdir()
        self.assert_preflight_refuses("op 1 mkdir: target already exists: archive")

    def test_preflight_refuses_missing_source(self) -> None:
        self.inventory()
        pm = self.write("missing-pathmap.csv", PATHMAP + "6,3,move,nope,archive/nope\n")
        self.assert_preflight_refuses("op 6 move: source missing: nope", pm)

    # run / edits negatives ---------------------------------------------------
    def test_run_refuses_without_snapshot(self) -> None:
        before = state(self.root, skip_meta=False)
        out = self.rx("run", "--pathmap", self.pathmap, expect=1)
        self.assertIn("refusing to run: snapshot not taken", out)
        self.assertEqual(state(self.root, skip_meta=False), before)
        self.assertFalse(self.meta.exists())

    def test_run_stops_at_destination_collision(self) -> None:
        (self.root / "archive" / "logs").mkdir(parents=True)
        self.rx("snapshot", "--pathmap", self.pathmap)
        out = self.rx("run", "--pathmap", self.pathmap, expect=1)
        self.assertIn("FAILED at op 4", out)
        self.assertIn("destination already exists", out)
        files, dirs = state(self.root)
        self.assertIn("archive/notes/a.md", files)                 # ops before the failure stay done
        self.assertNotIn("docs/old-notes", dirs)
        self.assertIn("logs/2026-01-run.log", files)               # the failing op moved nothing
        self.assertEqual(self.names("archive/logs"), [])
        self.assertEqual(self.names("src"), ["Main.java"])         # later ops did not run
        log = (self.meta / "reorg-log.md").read_text(encoding="utf-8")
        self.assertIn("| op 4 | move | logs -> archive/logs | FAIL:", log)
        self.assertNotIn("| op 5 |", log)

    def test_edits_count_mismatch_writes_nothing(self) -> None:
        self.snapshot_and_run()
        bad = json.loads(json.dumps(EDITS))
        bad["edits"][1]["replacements"][0]["count"] = 2
        bad_path = self.write("bad-edits.json", json.dumps(bad))
        before = state(self.root)
        out = self.rx("edits", "--edits", bad_path, expect=1)
        self.assertIn("expected 2 x old, found 1 x old", out)
        self.assertIn("nothing written (all-or-nothing)", out)
        self.assertEqual(state(self.root), before)
        self.assertFalse(self.bakdir.exists())

    def test_edits_refuse_stale_backup(self) -> None:
        self.snapshot_and_run()
        self.bakdir.mkdir(parents=True)
        (self.bakdir / "docs__readme.md").write_bytes(b"an older version\n")
        before = state(self.root)
        out = self.rx("edits", "--edits", self.edits, expect=1)
        self.assertIn("docs/readme.md: file differs from its existing backup", out)
        self.assertEqual(state(self.root), before)
        self.assertEqual(os.listdir(self.bakdir), ["docs__readme.md"])

    # verify ------------------------------------------------------------------
    def test_verify_ignores_desktop_ini_churn_and_honours_allow_new(self) -> None:
        self.full_flow()
        args = ("--pathmap", self.pathmap, "--inventory", self.inv, "--edits", self.edits)
        (self.root / "desktop.ini").unlink()
        (self.root / "archive" / "desktop.ini").write_bytes(b"[.ShellClassInfo]\r\n")
        self.rx("verify", *args)
        (self.root / "archive" / "notes" / "new.txt").write_bytes(b"added after the move\n")
        out = self.rx("verify", *args, expect=1)
        self.assertIn("EXTRA    archive/notes/new.txt", out)
        out = self.rx("verify", *args, "--allow-new", "archive/notes/new.txt")
        self.assertIn("ALLOWED  archive/notes/new.txt", out)
        self.assertIn("RESULT: OK", out)

    def test_verify_reports_uncovered_old_path(self) -> None:
        self.full_flow()
        (self.root / "docs" / "late.md").write_bytes(b"still points at docs/old-notes/a.md\n")
        out = self.rx("verify", "--pathmap", self.pathmap, "--inventory", self.inv, "--edits", self.edits,
                      "--allow-new", "late.md", expect=1)
        self.assertRegex(out, r"UNCOVERED hits\s+: 1\n")
        self.assertIn("HIT  docs/late.md  [line 1]", out)


if __name__ == "__main__":
    unittest.main()
