"""Tests for scripts/kb.py (no Docker, no outside network)."""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import plistlib
import re
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kb_cli_under_test", REPO / "scripts" / "kb.py")
kb = importlib.util.module_from_spec(SPEC)
sys.modules["kb_cli_under_test"] = kb
SPEC.loader.exec_module(kb)

AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"  # assembled so the test file itself holds no literal key


class StubCore:
    """Minimal stand-in for kb/service/kb_core.py (the contract subset kb.py uses)."""

    INDEXED_EXTENSIONS = {".md", ".txt"}
    _RULES = [("aws-access-key-id", re.compile(r"AKIA[0-9A-Z]{16}")),
              ("secret-assignment", re.compile(r"(?i)password\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}"))]

    @classmethod
    def find_secrets(cls, text):
        return [name for name, rx in cls._RULES if rx.search(text)]

    @classmethod
    def mask_secrets(cls, text):
        for name, rx in cls._RULES:
            text = rx.sub(f"[REDACTED:{name}]", text)
        return text

    @staticmethod
    def parse_front_matter(text):
        m = re.match(r"^---\n(.*?)\n---\n?(.*)$", text, re.S)
        if not m:
            return {}, text
        meta = {}
        for line in m.group(1).splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                meta[k.strip()] = v.strip().strip('"')
        return meta, m.group(2)

    @staticmethod
    def iter_corpus_files(root):
        for p in sorted(Path(root).rglob("*.md")):
            yield p.relative_to(root).as_posix(), str(p)


class FakeService:
    """Local HTTP server on an ephemeral 127.0.0.1 port."""

    def __init__(self, dedupe_verdict="novel"):
        self.dedupe_verdict = dedupe_verdict
        self.requests = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, payload):
                body = json.dumps(payload).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                outer.requests.append(("GET", self.path, None))
                self._send({"collection": "t", "chunks": 7, "files": 2, "last_scan": "x", "quarantined": {}})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
                outer.requests.append(("POST", self.path, payload))
                if self.path == "/search":
                    self._send({"hits": [{"source": "repo", "path": "rules/a.md", "kind": "rule", "title": "A",
                                          "heading": "Intro", "chunk": 0, "chunks": 1, "distance": 0.2,
                                          "text": "alpha text"}]})
                elif self.path == "/dedupe":
                    self._send({"verdict": outer.dedupe_verdict,
                                "nearest": [{"source": "repo", "path": "rules/a.md", "heading": "Intro", "distance": 0.1}]})
                else:
                    self._send({"indexed": []})

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()


def free_port():
    import socket
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class KBTestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.home = self.tmp / "home"
        self.home.mkdir()
        self.data = self.tmp / "data"
        self.corpus = self.tmp / "corpus"
        self.corpus.mkdir()
        env = {k: v for k, v in os.environ.items() if not k.startswith("LLM_KB_") and k != "LLM_RUN_LOG"}
        env.update({"HOME": str(self.home), "USERPROFILE": str(self.home),
                    "LLM_KB_ENV_FILE": str(self.tmp / "kb.env"),
                    "LLM_KB_DATA_DIR": str(self.data), "LLM_KB_CORPUS_DIR": str(self.corpus),
                    "LLM_RUN_LOG": str(self.tmp / "run-log.jsonl")})
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self._tmp.cleanup)
        kb.set_core(StubCore)
        self.addCleanup(kb.set_core, None)

    def run_main(self, *argv, stdin=None):
        buf, ebuf = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(ebuf):
            if stdin is not None:
                with mock.patch.object(sys, "stdin", io.StringIO(stdin)):
                    rc = kb.main(list(argv))
            else:
                rc = kb.main(list(argv))
        return rc, buf.getvalue(), ebuf.getvalue()

    def use_service(self, svc):
        os.environ["LLM_KB_PORT"] = str(svc.port)


class HelpTests(unittest.TestCase):
    COMMANDS = ["init", "up", "down", "status", "index", "search", "check", "add", "inbox", "sync-status",
                "sessions", "schedule", "scheduled-run", "hook", "doctor"]

    def test_help_exits_zero_for_all(self):
        for argv in [["--help"]] + [[c, "--help"] for c in self.COMMANDS]:
            with self.subTest(argv=argv), contextlib.redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as cm:
                    kb.main(argv)
                self.assertEqual(cm.exception.code, 0)

    def test_cli_process_help(self):
        proc = subprocess.run([sys.executable, str(REPO / "scripts" / "kb.py"), "--help"],
                              capture_output=True, text=True, cwd=tempfile.gettempdir())
        self.assertEqual(proc.returncode, 0)


class EnvFileTests(KBTestCase):
    def test_parse(self):
        got = kb.parse_env_text("# c\n\nA=1\nexport B = two \nC=\"q x\"\nbad line\n")
        self.assertEqual(got, {"A": "1", "B": "two", "C": "q x"})

    def test_merge_precedence_process_over_file_over_default(self):
        (self.tmp / "kb.env").write_text("LLM_KB_PORT=9001\nLLM_KB_COLLECTION=fromfile\n")
        cfg = kb.load_config()
        self.assertEqual(cfg["LLM_KB_PORT"], "9001")
        self.assertEqual(cfg["LLM_KB_CHROMA_PORT"], "8010")  # default
        os.environ["LLM_KB_PORT"] = "9100"
        cfg = kb.load_config()
        self.assertEqual(cfg["LLM_KB_PORT"], "9100")  # process wins
        self.assertEqual(cfg["LLM_KB_COLLECTION"], "fromfile")

    def test_env_file_relocation(self):
        other = self.tmp / "elsewhere.env"
        other.write_text("LLM_KB_COLLECTION=moved\n")
        os.environ["LLM_KB_ENV_FILE"] = str(other)
        self.assertEqual(kb.load_config()["LLM_KB_COLLECTION"], "moved")

    def test_default_env_path_uses_home(self):
        del os.environ["LLM_KB_ENV_FILE"]
        self.assertEqual(kb.env_file_path(), self.home / ".llm-toolkit" / "kb.env")

    def test_toolkit_default_is_repo_and_corpus_follows(self):
        del os.environ["LLM_KB_CORPUS_DIR"]
        cfg = kb.load_config()
        self.assertEqual(cfg["LLM_KB_TOOLKIT_DIR"], REPO.resolve().as_posix())
        self.assertEqual(cfg["LLM_KB_CORPUS_DIR"], cfg["LLM_KB_TOOLKIT_DIR"])


class InitTests(KBTestCase):
    def setUp(self):
        super().setUp()
        # init must read its own env file, not the process-level data dir override
        for key in ("LLM_KB_DATA_DIR", "LLM_KB_CORPUS_DIR"):
            os.environ.pop(key)

    def test_init_creates_layout_and_is_idempotent_and_preserves_keys(self):
        envf = self.tmp / "kb.env"
        envf.write_text("# keep me\nLLM_KB_COLLECTION=custom\nUNRELATED=1\n")
        rc, _, _ = self.run_main("init", "--data-dir", str(self.data), "--corpus", str(self.corpus), "--port", "9011")
        self.assertEqual(rc, 0)
        for sub in kb.DATA_SUBDIRS:
            self.assertTrue((self.data / sub).is_dir())
        first = envf.read_text()
        self.assertIn("# keep me", first)
        self.assertIn("LLM_KB_COLLECTION=custom", first)
        self.assertIn("UNRELATED=1", first)
        self.assertIn("LLM_KB_PORT=9011", first)
        rc, _, _ = self.run_main("init")  # no flags: nothing may change
        self.assertEqual(rc, 0)
        self.assertEqual(envf.read_text(), first)
        rc, _, _ = self.run_main("init", "--port", "9022")
        self.assertIn("LLM_KB_PORT=9022", envf.read_text())
        self.assertIn("LLM_KB_COLLECTION=custom", envf.read_text())
        self.assertEqual(envf.read_text().count("LLM_KB_PORT="), 1)

    def test_compose_env_rendering(self):
        self.run_main("init", "--data-dir", str(self.data), "--corpus", str(self.corpus), "--port", "9011")
        text = (self.data / "state" / "compose.env").read_text()
        keys = [l.split("=", 1)[0] for l in text.splitlines() if l and not l.startswith("#")]
        self.assertEqual(keys, ["KB_DATA_DIR", "KB_CORPUS_DIR", "KB_CHROMA_PORT", "KB_PORT", "KB_COLLECTION",
                                "KB_MAX_DISTANCE", "KB_DUP_DISTANCE", "KB_NEAR_DISTANCE", "KB_SCAN_SECONDS",
                                "KB_SYNC_SAFE_INDEX"])
        vals = dict(l.split("=", 1) for l in text.splitlines() if l and not l.startswith("#"))
        self.assertEqual(vals["KB_DATA_DIR"], self.data.as_posix())
        self.assertEqual(vals["KB_CORPUS_DIR"], self.corpus.as_posix())
        self.assertEqual(vals["KB_PORT"], "9011")
        self.assertNotIn("\\", text)
        self.assertTrue(Path(vals["KB_DATA_DIR"]).is_absolute())


class ComposeCommandTests(KBTestCase):
    def test_command_shape(self):
        cfg = kb.load_config()
        cmd = kb.compose_command(cfg, "up", "-d")
        toolkit = Path(cfg["LLM_KB_TOOLKIT_DIR"])
        self.assertEqual(cmd[:7], ["docker", "compose", "-p", "llm-toolkit-kb", "-f",
                                   (toolkit / "kb" / "docker-compose.yml").as_posix(), "--env-file"])
        self.assertEqual(cmd[7], (self.data / "state" / "compose.env").as_posix())
        self.assertEqual(cmd[8:], ["up", "-d"])

    def test_up_down_index_go_through_builder(self):
        calls = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(kb, "run_cmd", fake):
            self.run_main("up", "--build")
            self.run_main("down")
            self.run_main("index")
        self.assertEqual(calls[0][-3:], ["up", "-d", "--build"])
        self.assertEqual(calls[1][-1], "down")
        self.assertEqual(calls[2][-6:], ["--profile", "tools", "run", "--rm", "-T", "ingest"][-6:])
        self.assertTrue(all(c[:4] == ["docker", "compose", "-p", "llm-toolkit-kb"] for c in calls))


class SearchTests(KBTestCase):
    def test_search_via_service(self):
        with FakeService() as svc:
            self.use_service(svc)
            rc, text, _ = self.run_main("search", "alpha", "-k", "3", "--kind", "rule")
            payload = [r for r in svc.requests if r[1] == "/search"][0][2]
        self.assertEqual(rc, 0)
        self.assertEqual(payload["k"], 3)
        self.assertEqual(payload["kind"], "rule")
        self.assertEqual(payload["max_distance"], 0.55)
        self.assertIn("0.200  rule  rules/a.md › Intro", text)
        self.assertIn("alpha text", text)

    def test_fallback_exit_3_when_service_down(self):
        (self.corpus / "a.md").write_text("The quick brown fox\njumps over\n")
        (self.corpus / "b.md").write_text("nothing relevant\n")
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, err = self.run_main("search", "quick fox")
        self.assertEqual(rc, 3)
        self.assertIn("a.md", text)
        self.assertNotIn("b.md", text)
        self.assertIn("unreachable", err)

    def test_fallback_without_core_module(self):
        kb.set_core(None)
        (self.corpus / "x.txt").write_text("needle here\n")
        (self.corpus / ".hidden").mkdir()
        (self.corpus / ".hidden" / "y.md").write_text("needle\n")
        os.environ["LLM_KB_TOOLKIT_DIR"] = str(self.tmp / "no-toolkit")
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, _ = self.run_main("search", "needle")
        self.assertEqual(rc, 3)
        self.assertIn("x.txt", text)
        self.assertNotIn("y.md", text)


class CheckTests(KBTestCase):
    def check(self, text, verdict="novel", up=True):
        if not up:
            os.environ["LLM_KB_PORT"] = str(free_port())
            return self.run_main("check", "-", stdin=text)
        with FakeService(verdict) as svc:
            self.use_service(svc)
            return self.run_main("check", "-", stdin=text)

    def test_exit_codes(self):
        self.assertEqual(self.check("A harmless note.\n", "novel")[0], 0)
        self.assertEqual(self.check("A harmless note.\n", "duplicate")[0], 3)
        self.assertEqual(self.check("A harmless note.\n", "near")[0], 5)
        self.assertEqual(self.check("A harmless note.\n", up=False)[0], 6)

    def test_security_hit_exit_4_rule_names_only(self):
        rc, text, err = self.check(f"key {AWS_KEY} here\n")
        self.assertEqual(rc, 4)
        self.assertIn("aws-access-key-id", text)
        self.assertNotIn(AWS_KEY, text + err)

    def test_security_checked_before_service(self):
        rc, _, _ = self.check(f"key {AWS_KEY}\n", up=False)
        self.assertEqual(rc, 4)

    def test_json_output(self):
        with FakeService("near") as svc:
            self.use_service(svc)
            rc, text, _ = self.run_main("check", "-", "--json", stdin="note\n")
        self.assertEqual(rc, 5)
        data = json.loads(text)
        self.assertEqual(data["verdict"], "near")
        self.assertEqual(data["exit_code"], 5)

    def test_surface_scanner_findings_block(self):
        fake_toolkit = self.tmp / "tk"
        (fake_toolkit / "scripts").mkdir(parents=True)
        (fake_toolkit / "scripts" / "scan-llm-surface-security.py").write_text(
            "import sys\nprint('docs/candidate.md:3: ignore-instructions: msg: SECRET LINE', file=sys.stderr)\nsys.exit(1)\n")
        os.environ["LLM_KB_TOOLKIT_DIR"] = str(fake_toolkit)
        rc, text, err = self.check("anything\n")
        self.assertEqual(rc, 4)
        self.assertIn("ignore-instructions", text)
        self.assertNotIn("SECRET LINE", text + err)


class AddTests(KBTestCase):
    def add(self, text, verdict="novel", *extra):
        with FakeService(verdict) as svc:
            self.use_service(svc)
            return self.run_main("add", "-", "--title", "My Great: Note!", *extra, stdin=text)

    def test_add_writes_front_matter_and_slug(self):
        rc, text, _ = self.add("Body text.\n")
        self.assertEqual(rc, 0, text)
        files = list((self.data / "inbox").glob("*.md"))
        self.assertEqual(len(files), 1)
        self.assertRegex(files[0].name, r"^\d{4}-\d{2}-\d{2}-my-great-note\.md$")
        content = files[0].read_text()
        meta, body = StubCore.parse_front_matter(content)
        self.assertEqual(meta["title"], "My Great: Note!")
        self.assertEqual(meta["kind"], "learning")
        self.assertEqual(meta["status"], "pending")
        self.assertEqual(meta["origin"], "manual")
        self.assertRegex(meta["created"], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
        self.assertIn("Body text.", body)

    def test_add_kind_origin_and_same_slug_gets_suffix(self):
        self.add("One.\n", "novel", "--kind", "rule", "--origin", "session")
        self.add("Two.\n")
        names = sorted(p.name for p in (self.data / "inbox").glob("*.md"))
        self.assertEqual(len(names), 2)
        first = [n for n in names if not n.endswith("-2.md")]
        self.assertEqual(len(first), 1)
        meta, _ = StubCore.parse_front_matter((self.data / "inbox" / first[0]).read_text())
        self.assertEqual(meta["kind"], "rule")
        self.assertEqual(meta["origin"], "session")

    def test_refusals(self):
        self.assertEqual(self.add("x\n", "duplicate")[0], 3)
        self.assertEqual(self.add("x\n", "near")[0], 5)
        self.assertEqual(self.add(f"{AWS_KEY}\n")[0], 4)
        self.assertFalse(list((self.data / "inbox").glob("*.md")))
        rc, _, _ = self.add("x\n", "near", "--allow-near")
        self.assertEqual(rc, 0)
        self.assertEqual(len(list((self.data / "inbox").glob("*.md"))), 1)

    def test_secret_text_never_printed_or_written(self):
        rc, text, err = self.add(f"leak {AWS_KEY}\n")
        self.assertNotIn(AWS_KEY, text + err)
        self.assertFalse((self.data / "inbox").exists() and list((self.data / "inbox").iterdir()))

    def test_slugify(self):
        self.assertEqual(kb.slugify("  Ação -- Test_Case 1 "), "acao-test-case-1")
        self.assertEqual(kb.slugify("!!!"), "note")
        self.assertLessEqual(len(kb.slugify("a" * 200)), 60)


class InboxTests(KBTestCase):
    def test_list_and_archive_moves_not_deletes(self):
        inbox = self.data / "inbox"
        inbox.mkdir(parents=True)
        (inbox / "2026-01-01-a.md").write_text('---\ntitle: "A"\nkind: rule\n---\nbody\n')
        (inbox / "2026-01-01-b.md").write_text("---\ntitle: B\n---\nbody\n")
        rc, text, _ = self.run_main("inbox", "--json")
        self.assertEqual([i["name"] for i in json.loads(text)], ["2026-01-01-a.md", "2026-01-01-b.md"])
        rc, _, _ = self.run_main("inbox", "archive", "2026-01-01-a.md")
        self.assertEqual(rc, 0)
        self.assertFalse((inbox / "2026-01-01-a.md").exists())
        self.assertTrue((self.data / "archive" / "2026-01-01-a.md").is_file())
        self.assertTrue((inbox / "2026-01-01-b.md").is_file())

    def test_archive_collision_keeps_both(self):
        inbox, archive = self.data / "inbox", self.data / "archive"
        inbox.mkdir(parents=True)
        archive.mkdir(parents=True)
        (archive / "n.md").write_text("old")
        (inbox / "n.md").write_text("new")
        self.run_main("inbox", "archive", "n.md")
        self.assertEqual((archive / "n.md").read_text(), "old")
        self.assertEqual((archive / "n-2.md").read_text(), "new")

    def test_archive_rejects_paths(self):
        (self.data / "inbox").mkdir(parents=True)
        outside = self.data / "keep.md"
        outside.write_text("x")
        rc, _, err = self.run_main("inbox", "archive", "../keep.md")
        self.assertEqual(rc, 2)
        self.assertTrue(outside.exists())


class SyncStatusTests(KBTestCase):
    def write_log(self, rows):
        Path(os.environ["LLM_RUN_LOG"]).write_text("\n".join(json.dumps(r) if isinstance(r, dict) else r for r in rows) + "\n")

    def test_run_log_watermark_logic(self):
        self.write_log([{"ts": "2026-01-01T10:00:00Z", "n": 1}, {"ts": "2026-01-02T10:00:00Z", "n": 2},
                        {"n": 3}, "not json", {"ts": "2026-01-03T10:00:00Z", "n": 4}])
        recs, undated = kb.run_log_since(Path(os.environ["LLM_RUN_LOG"]), None)
        self.assertEqual([r["n"] for r in recs], [1, 2, 4])
        self.assertEqual(undated, 1)
        recs, _ = kb.run_log_since(Path(os.environ["LLM_RUN_LOG"]), kb.parse_iso("2026-01-02T10:00:00Z"))
        self.assertEqual([r["n"] for r in recs], [4])  # strictly newer
        self.assertEqual(kb.run_log_since(self.tmp / "missing.jsonl", None), ([], 0))

    def test_sync_status_mark_persists_watermark(self):
        self.write_log([{"ts": "2026-01-01T10:00:00Z"}])
        with FakeService() as svc:
            self.use_service(svc)
            rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch", "--mark")
            data = json.loads(text)
            self.assertEqual(rc, 0)
            self.assertTrue(data["service"]["up"])
            self.assertEqual(data["run_log"]["new"], 1)
            self.assertIsNone(data["watermark"])
            state = json.loads((self.data / "state" / "sync-state.json").read_text())
            self.assertRegex(state["watermark"], r"^\d{4}-")
            rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch")
            data = json.loads(text)
        self.assertEqual(data["run_log"]["new"], 0)
        self.assertEqual(data["watermark"], state["watermark"])
        self.assertFalse(data["corpus"]["git"])

    def test_service_down_reported(self):
        os.environ["LLM_KB_PORT"] = str(free_port())
        rc, text, _ = self.run_main("sync-status", "--json", "--no-fetch")
        self.assertEqual(rc, 0)
        self.assertFalse(json.loads(text)["service"]["up"])


class SessionsTests(KBTestCase):
    def make_root(self):
        root = self.tmp / "projects"
        proj = root / "-some-project"
        proj.mkdir(parents=True)
        rows = [
            {"type": "user", "message": {"role": "user", "content": f"Please fix this. key {AWS_KEY}"}},
            {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "working"}]}},
            {"type": "assistant", "message": {"role": "assistant", "content": [
                {"type": "text", "text": "Done. password=" + "Abcdefgh12345678XYZ"}, {"type": "tool_use", "name": "x"}]}},
        ]
        (proj / "sess-1.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n")
        return root

    def test_refuses_without_opt_in(self):
        root = self.make_root()
        rc, text, err = self.run_main("sessions", "--since", "2000-01-01", "--root", str(root))
        self.assertEqual(rc, 2)
        self.assertEqual(text, "")
        self.assertIn("opt-in", err)

    def test_digest_redacts_and_writes_nothing(self):
        root = self.make_root()
        before = sorted(p.as_posix() for p in self.tmp.rglob("*"))
        rc, text, err = self.run_main("sessions", "--since", "2000-01-01", "--root", str(root), "--force", "--json")
        self.assertEqual(rc, 0, err)
        self.assertNotIn(AWS_KEY, text)
        self.assertNotIn("Abcdefgh12345678XYZ", text)
        data = json.loads(text)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["project"], "-some-project")
        self.assertEqual(data[0]["session"], "sess-1")
        self.assertIn("[REDACTED:aws-access-key-id]", data[0]["first_prompt"])
        self.assertTrue(data[0]["last_assistant"].startswith("Done."))
        self.assertEqual(before, sorted(p.as_posix() for p in self.tmp.rglob("*")))

    def test_env_opt_in_and_length_limits_and_since_filter(self):
        root = self.make_root()
        long_file = root / "-p2" / "long.jsonl"
        long_file.parent.mkdir()
        rows = [{"type": "user", "message": {"role": "user", "content": "q" * 500}},
                {"type": "assistant", "message": {"role": "assistant", "content": "a" * 900}}]
        long_file.write_text("\n".join(json.dumps(r) for r in rows))
        os.environ["LLM_KB_HARVEST_SESSIONS"] = "1"
        rc, text, _ = self.run_main("sessions", "--since", "2000-01-01", "--root", str(root), "--json")
        self.assertEqual(rc, 0)
        longd = [d for d in json.loads(text) if d["session"] == "long"][0]
        self.assertEqual(len(longd["first_prompt"]), 200)
        self.assertEqual(len(longd["last_assistant"]), 600)
        rc, text, _ = self.run_main("sessions", "--since", "2999-01-01", "--root", str(root), "--json")
        self.assertEqual(json.loads(text), [])


class SchedulerTests(KBTestCase):
    CMD = ["/usr/bin/python3", "/opt/kb/scripts/kb.py", "scheduled-run"]

    def test_parse_field(self):
        self.assertEqual(kb.parse_field("8-20/2", 0, 23), [8, 10, 12, 14, 16, 18, 20])
        self.assertEqual(kb.parse_field("1-5", 0, 7), [1, 2, 3, 4, 5])
        self.assertEqual(kb.parse_field("9,17", 0, 23), [9, 17])
        for bad in ("25", "5-2", "a"):
            with self.assertRaises((kb.KBError, ValueError)):
                kb.parse_field(bad, 0, 23)

    def test_launchd_plist(self):
        plist = kb.make_launchd_plist("8-20/2", "1-5", self.CMD, "/x/log")
        self.assertEqual(plist["Label"], "dev.llm-toolkit.kb-sync")
        ivs = plist["StartCalendarInterval"]
        self.assertEqual(len(ivs), 35)
        self.assertEqual({i["Weekday"] for i in ivs}, {1, 2, 3, 4, 5})
        self.assertEqual({i["Hour"] for i in ivs}, {8, 10, 12, 14, 16, 18, 20})
        self.assertTrue(all(i["Minute"] == 0 for i in ivs))
        self.assertEqual(plist["ProgramArguments"], self.CMD)
        self.assertEqual(plistlib.loads(plistlib.dumps(plist))["Label"], plist["Label"])

    def test_cron_line(self):
        line = kb.make_cron_line("8-20/2", "1-5", self.CMD)
        self.assertTrue(line.startswith("0 8-20/2 * * 1-5 "))
        self.assertTrue(line.endswith(kb.CRON_MARKER))
        self.assertIn("scheduled-run", line)

    def test_cron_edit_only_touches_own_line(self):
        other = "5 4 * * * /bin/backup"
        line = kb.make_cron_line("8-20/2", "1-5", self.CMD)
        installed = kb.cron_edit(other + "\n", line)
        self.assertEqual(installed.splitlines()[0], other)
        self.assertEqual(kb.cron_edit(installed, line).count(kb.CRON_MARKER), 1)  # idempotent
        self.assertEqual(kb.cron_edit(installed), other + "\n")
        self.assertEqual(kb.cron_edit(line + "\n"), "")

    def test_schtasks_uniform_hours(self):
        tasks = kb.make_schtasks_args("8-20/2", "1-5", self.CMD)
        self.assertEqual(len(tasks), 1)
        a = tasks[0]
        self.assertEqual(a[a.index("/TN") + 1], "llm-toolkit-kb-sync")
        self.assertEqual(a[a.index("/SC") + 1], "WEEKLY")
        self.assertEqual(a[a.index("/D") + 1], "MON,TUE,WED,THU,FRI")
        self.assertEqual(a[a.index("/ST") + 1], "08:00")
        self.assertEqual(a[a.index("/RI") + 1], "120")
        self.assertEqual(a[a.index("/DU") + 1], "0012:01")  # 08:00 .. 20:00 inclusive
        self.assertIn("scheduled-run", a[a.index("/TR") + 1])

    def test_schtasks_irregular_hours_one_task_per_hour(self):
        tasks = kb.make_schtasks_args("9,13,20", "1-5", self.CMD)
        self.assertEqual([t[t.index("/ST") + 1] for t in tasks], ["09:00", "13:00", "20:00"])
        self.assertEqual([t[t.index("/TN") + 1] for t in tasks],
                         ["llm-toolkit-kb-sync-09", "llm-toolkit-kb-sync-13", "llm-toolkit-kb-sync-20"])

    def test_generators_are_pure(self):
        with mock.patch.object(kb, "run_cmd", side_effect=AssertionError("must not execute")):
            kb.make_launchd_plist("8-20/2", "1-5", self.CMD, "/l")
            kb.make_cron_line("8-20/2", "1-5", self.CMD)
            kb.make_schtasks_args("8-20/2", "1-5", self.CMD)

    def test_install_remove_linux_uses_crontab_with_fake_runner(self):
        store = {"tab": "0 1 * * * /bin/other\n"}

        def fake(cmd, **kw):
            if cmd[:2] == ["crontab", "-l"]:
                return subprocess.CompletedProcess(cmd, 0, store["tab"], "")
            if cmd[:2] == ["crontab", "-"]:
                store["tab"] = kw["input"]
                return subprocess.CompletedProcess(cmd, 0, "", "")
            raise AssertionError(cmd)

        with mock.patch.object(kb, "run_cmd", fake), mock.patch.object(kb, "detect_os", return_value="Linux"):
            self.assertEqual(self.run_main("schedule", "install")[0], 0)
            self.assertIn("0 8-20/2 * * 1-5 ", store["tab"])
            self.assertIn("/bin/other", store["tab"])
            self.assertEqual(self.run_main("schedule", "status")[0], 0)
            self.assertEqual(self.run_main("schedule", "remove")[0], 0)
            self.assertEqual(store["tab"], "0 1 * * * /bin/other\n")


class HookTests(KBTestCase):
    def settings(self):
        path = self.tmp / "claude" / "settings.json"
        path.parent.mkdir()
        original = {"model": "x", "permissions": {"allow": ["Bash(ls)"]},
                    "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "echo mine"}]}],
                              "Stop": [{"hooks": [{"type": "command", "command": "echo stop"}]}]}}
        path.write_text(json.dumps(original, indent=4))
        return path, original

    def test_install_backup_and_other_entries_untouched(self):
        path, original = self.settings()
        os.environ["LLM_KB_PORT"] = "9011"
        rc, _, _ = self.run_main("hook", "install", "--settings", str(path))
        self.assertEqual(rc, 0)
        backups = list(path.parent.glob("settings.json.bak-*"))
        self.assertEqual(len(backups), 1)
        self.assertEqual(json.loads(backups[0].read_text()), original)
        data = json.loads(path.read_text())
        cmds = [h["command"] for g in data["hooks"]["UserPromptSubmit"] for h in g["hooks"]]
        self.assertEqual(cmds, ["echo mine", "curl -s --max-time 2 http://localhost:9011/hook -d @-"])
        self.assertEqual(data["hooks"]["Stop"], original["hooks"]["Stop"])
        self.assertEqual(data["permissions"], original["permissions"])
        self.assertEqual(self.run_main("hook", "status", "--settings", str(path))[0], 0)

    def test_install_twice_keeps_one_entry_and_updates_port(self):
        path, _ = self.settings()
        os.environ["LLM_KB_PORT"] = "9011"
        self.run_main("hook", "install", "--settings", str(path))
        os.environ["LLM_KB_PORT"] = "9012"
        self.run_main("hook", "install", "--settings", str(path))
        text = path.read_text()
        self.assertEqual(text.count("/hook -d @-"), 1)
        self.assertIn("localhost:9012", text)

    def test_remove_restores_equivalent_settings(self):
        path, original = self.settings()
        self.run_main("hook", "install", "--settings", str(path))
        rc, _, _ = self.run_main("hook", "remove", "--settings", str(path))
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(path.read_text()), original)
        self.assertEqual(self.run_main("hook", "status", "--settings", str(path))[0], 1)

    def test_install_creates_missing_settings_and_remove_prunes_empty(self):
        path = self.tmp / "new" / "settings.json"
        self.assertEqual(self.run_main("hook", "install", "--settings", str(path))[0], 0)
        self.assertFalse(list(path.parent.glob("*.bak-*")))  # nothing to back up
        self.run_main("hook", "remove", "--settings", str(path))
        self.assertEqual(json.loads(path.read_text()), {})

    def test_invalid_json_refused_and_untouched(self):
        path = self.tmp / "bad.json"
        path.write_text("{not json")
        rc, _, err = self.run_main("hook", "install", "--settings", str(path))
        self.assertEqual(rc, 2)
        self.assertEqual(path.read_text(), "{not json")

    def test_remove_when_absent_leaves_no_stray_backup(self):
        path, original = self.settings()
        self.run_main("hook", "remove", "--settings", str(path))
        self.assertEqual(json.loads(path.read_text()), original)
        self.assertFalse(list(path.parent.glob("*.bak-*")))


def git(repo, *args):
    env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
           "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@example.invalid",
           "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@example.invalid"}
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=True)


@unittest.skipUnless(subprocess.run(["git", "--version"], capture_output=True).returncode == 0, "git missing")
class ScheduledRunTests(KBTestCase):
    def make_repo(self):
        git(self.tmp, "init", "-q", "-b", "main", str(self.corpus))
        (self.corpus / "a.md").write_text("a\n")
        git(self.corpus, "add", "a.md")
        git(self.corpus, "commit", "-q", "-m", "init")

    def run_scheduled(self):
        calls = []

        def fake(cmd, **kw):
            calls.append(list(cmd))
            if cmd[0] == "git":
                real = subprocess.run(cmd, capture_output=True, text=True, **{k: v for k, v in kw.items()
                                                                              if k in ("timeout",)})
                if "pull" in cmd:
                    return subprocess.CompletedProcess(cmd, 0, "", "")  # never really pull in tests
                return real
            return subprocess.CompletedProcess(cmd, 0, "", "")

        with mock.patch.object(kb, "run_cmd", fake):
            rc, text, _ = self.run_main("scheduled-run")
        return rc, text, calls

    def pulls(self, calls):
        return [c for c in calls if c[0] == "git" and "pull" in c]

    def test_pulls_on_default_branch_clean(self):
        self.make_repo()
        rc, text, calls = self.run_scheduled()
        self.assertEqual(rc, 0)
        self.assertEqual(len(self.pulls(calls)), 1)
        self.assertIn("--ff-only", self.pulls(calls)[0])
        self.assertIn("pull ok", text)
        log = (self.data / "state" / "schedule.log").read_text()
        self.assertIn("ok", log)

    def test_no_pull_on_feature_branch(self):
        self.make_repo()
        git(self.corpus, "checkout", "-q", "-b", "feat/x")
        rc, text, calls = self.run_scheduled()
        self.assertEqual(self.pulls(calls), [])
        self.assertIn("pull skipped", text)

    def test_no_pull_on_dirty_tree(self):
        self.make_repo()
        (self.corpus / "a.md").write_text("changed\n")
        rc, text, calls = self.run_scheduled()
        self.assertEqual(self.pulls(calls), [])
        self.assertIn("not clean", text)

    def test_no_pull_outside_git_and_no_other_git_writes(self):
        rc, text, calls = self.run_scheduled()
        self.assertEqual(self.pulls(calls), [])
        self.make_repo()
        _, _, calls = self.run_scheduled()
        allowed = {"rev-parse", "symbolic-ref", "status", "pull"}
        for c in calls:
            if c[0] == "git":
                self.assertIn(c[3], allowed, c)

    def test_stack_failure_logged_and_nonzero(self):
        def fail(cmd, **kw):
            return subprocess.CompletedProcess(cmd, 1, "", "boom")

        with mock.patch.object(kb, "run_cmd", fail):
            rc, text, _ = self.run_main("scheduled-run")
        self.assertEqual(rc, 1)
        self.assertIn("error", (self.data / "state" / "schedule.log").read_text())


class DoctorTests(KBTestCase):
    def test_doctor_runs_without_docker(self):
        with mock.patch.object(kb.shutil, "which", return_value=None):
            os.environ["LLM_KB_PORT"] = str(free_port())
            rc, text, _ = self.run_main("doctor")
        self.assertEqual(rc, 1)
        self.assertIn("docker on PATH", text)


@unittest.skipUnless((REPO / "kb" / "service" / "kb_core.py").is_file(), "kb_core.py not present yet")
class RealCoreContractTests(KBTestCase):
    """Run the key flows against the real shared module."""

    def setUp(self):
        super().setUp()
        kb.set_core(None)
        os.environ["LLM_KB_TOOLKIT_DIR"] = str(REPO)

    def test_loads_by_path_and_has_contract(self):
        core = kb.get_core(kb.load_config())
        for name in ("find_secrets", "mask_secrets", "parse_front_matter", "iter_corpus_files"):
            self.assertTrue(hasattr(core, name), name)

    def test_check_blocks_secret_and_add_front_matter(self):
        rc, text, err = self.run_main("check", "-", stdin=f"aws {AWS_KEY}\n")
        self.assertEqual(rc, 4)
        self.assertNotIn(AWS_KEY, text + err)
        with FakeService() as svc:
            self.use_service(svc)
            rc, _, _ = self.run_main("add", "-", "--title", "Real core note", stdin="Plain note body.\n")
        self.assertEqual(rc, 0)
        item = next((self.data / "inbox").glob("*real-core-note.md"))
        meta, _ = kb.get_core().parse_front_matter(item.read_text())
        self.assertEqual(meta.get("status"), "pending")

    def test_sessions_masking_with_real_core(self):
        root = self.tmp / "proj" / "p"
        root.mkdir(parents=True)
        (root / "s.jsonl").write_text(json.dumps({"type": "user", "message": {"role": "user", "content": f"k {AWS_KEY}"}}) + "\n")
        rc, text, _ = self.run_main("sessions", "--since", "2000-01-01", "--root", str(self.tmp / "proj"), "--force", "--json")
        self.assertEqual(rc, 0)
        self.assertNotIn(AWS_KEY, text)


if __name__ == "__main__":
    unittest.main()
