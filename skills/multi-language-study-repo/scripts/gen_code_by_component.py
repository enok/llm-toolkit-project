#!/usr/bin/env python3
"""Generate a "code by component" Markdown page from a JSON config (stdlib only, Python 3.9+).

One section per pattern component; inside each section the same component in every
language, one collapsible <details> block per language (the first one open), whole
files only, each preceded by a `<!-- source: <repo-relative path> -->` marker so that
check_docs.py can guard the page against drift.

Config (JSON; unknown and duplicate keys are rejected; run with cwd-relative or absolute --config):
  title       page H1, plain text (Markdown/HTML characters are escaped), one line
  intro       Markdown shown under the title (optional, written as given, stripped)
  languages   [{"key", "label", "fence", "dir"}]  dir = language folder relative to --root;
              label is plain text (HTML-escaped in the <summary>); fence matches [A-Za-z0-9_+.#-]+
  components  [{"title", "role", "files": {<language key>: [paths relative to that dir]}}]
              title is plain text, role one line of Markdown; a language without files for a
              component is skipped for that component
Paths must stay inside the repository (no absolute or drive-letter paths, no `..` escapes, no
symlinks leading outside) and contain no control characters or `-->`.

Usage: gen_code_by_component.py --config components.json --root REPO
                                [--out docs/05-code-by-component.md] [--check]
Without --check the page is written and its path printed. With --check nothing is
written: exit 0 when the page on disk equals the generated text, 1 when it is stale or
missing. Exit 2: invalid config, missing source file, bad arguments or I/O error.
"""
from __future__ import annotations

import argparse
import html
import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, NamedTuple, Optional, Sequence, Tuple

DEFAULT_OUT = "docs/05-code-by-component.md"

TOP_KEYS = ("title", "intro", "languages", "components")
LANGUAGE_KEYS = ("key", "label", "fence", "dir")
COMPONENT_KEYS = ("title", "role", "files")
FENCE_RE = re.compile(r"[A-Za-z0-9_+.#-]+")
CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")
SEPARATOR = "\u00b7"


class ConfigError(Exception):
    """Invalid configuration or missing input; reported with exit code 2."""


class Language(NamedTuple):
    key: str
    label: str
    fence: str
    dir: str


class Component(NamedTuple):
    title: str
    role: str
    files: Dict[str, List[str]]  # language key -> paths relative to the language dir


class Config(NamedTuple):
    title: str
    intro: str
    languages: List[Language]
    components: List[Component]


def _no_duplicate_keys(pairs: List[Tuple[str, Any]]) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError(f"duplicate key in config: {key!r}")
        result[key] = value
    return result


def load_config(path: Path) -> Config:
    try:
        raw = path.read_bytes().decode("utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"cannot read config {path}: {exc}") from exc
    try:
        data = json.loads(raw, object_pairs_hook=_no_duplicate_keys)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"config {path} is not valid JSON: {exc}") from exc
    return parse_config(data)


def _text(value: Any, where: str, allow_empty: bool = False, one_line: bool = False) -> str:
    if not isinstance(value, str) or (not allow_empty and not value.strip()):
        raise ConfigError(f"{where} must be a {'string' if allow_empty else 'non-empty string'}")
    if one_line and CONTROL_RE.search(value):
        raise ConfigError(f"{where} must be a single line without control characters")
    return value


def _check_keys(obj: Any, where: str, allowed: Sequence[str], required: Sequence[str]) -> Dict[str, Any]:
    if not isinstance(obj, dict):
        raise ConfigError(f"{where} must be an object")
    unknown = sorted(set(obj) - set(allowed))
    if unknown:
        raise ConfigError(f"{where}: unknown key(s) {', '.join(unknown)} (allowed: {', '.join(allowed)})")
    missing = [key for key in required if key not in obj]
    if missing:
        raise ConfigError(f"{where}: missing key(s) {', '.join(missing)}")
    return obj


def _absolute(path: str) -> bool:
    """Absolute on POSIX, a drive letter (C:/x, C:x) or a UNC prefix (already slash-normalised)."""
    return posixpath.isabs(path) or bool(re.match(r"^[A-Za-z]:", path))


def repo_path(directory: str, name: str, where: str) -> str:
    """Repo-relative POSIX path of `name` inside `directory`; rejects absolute and escaping paths."""
    name = name.replace("\\", "/")
    directory = directory.replace("\\", "/")
    if CONTROL_RE.search(name) or "-->" in name or CONTROL_RE.search(directory) or "-->" in directory:
        raise ConfigError(f"{where}: path must not contain control characters or '-->': {name}")
    if _absolute(directory):
        raise ConfigError(f"{where}: language dir must be relative to the repository root: {directory}")
    if _absolute(name):
        raise ConfigError(f"{where}: path must be relative to the language dir: {name}")
    joined = posixpath.normpath(posixpath.join(directory, name))
    if _absolute(joined) or joined == ".." or joined.startswith("../"):
        raise ConfigError(f"{where}: path leaves the repository: {name}")
    return joined


def parse_config(data: Any) -> Config:
    top = _check_keys(data, "config", TOP_KEYS, ("title", "languages", "components"))
    title = _text(top["title"], "config.title", one_line=True)
    intro = _text(top.get("intro", ""), "config.intro", allow_empty=True).replace("\r\n", "\n").strip()

    raw_languages = top["languages"]
    if not isinstance(raw_languages, list) or not raw_languages:
        raise ConfigError("config.languages must be a non-empty list")
    languages: List[Language] = []
    for i, raw in enumerate(raw_languages):
        where = f"config.languages[{i}]"
        obj = _check_keys(raw, where, LANGUAGE_KEYS, LANGUAGE_KEYS)
        language = Language(
            _text(obj["key"], f"{where}.key", one_line=True),
            _text(obj["label"], f"{where}.label", one_line=True),
            _text(obj["fence"], f"{where}.fence"),
            _text(obj["dir"], f"{where}.dir", allow_empty=True, one_line=True),
        )
        if not FENCE_RE.fullmatch(language.fence):
            raise ConfigError(f"{where}.fence must match [A-Za-z0-9_+.#-]+: {language.fence!r}")
        if any(language.key == other.key for other in languages):
            raise ConfigError(f"{where}.key: duplicate language key {language.key!r}")
        repo_path(language.dir, ".", f"{where}.dir")  # the folder itself must stay inside the repo
        languages.append(language)
    dirs = {language.key: language.dir for language in languages}

    raw_components = top["components"]
    if not isinstance(raw_components, list) or not raw_components:
        raise ConfigError("config.components must be a non-empty list")
    components: List[Component] = []
    for i, raw in enumerate(raw_components):
        where = f"config.components[{i}]"
        obj = _check_keys(raw, where, COMPONENT_KEYS, COMPONENT_KEYS)
        raw_files = obj["files"]
        if not isinstance(raw_files, dict):
            raise ConfigError(f"{where}.files must be an object mapping language keys to file lists")
        files: Dict[str, List[str]] = {}
        for key, names in raw_files.items():
            if key not in dirs:
                raise ConfigError(f"{where}.files: unknown language key {key!r} "
                                  f"(languages: {', '.join(dirs)})")
            if not isinstance(names, list):
                raise ConfigError(f"{where}.files.{key} must be a list of file paths")
            files[key] = [_text(name, f"{where}.files.{key}[{j}]") for j, name in enumerate(names)]
            for name in files[key]:
                repo_path(dirs[key], name, f"{where}.files.{key}")
        if not any(files.values()):
            raise ConfigError(f"{where} ({obj['title']!r}) lists no files in any language")
        components.append(Component(_text(obj["title"], f"{where}.title", one_line=True),
                                    _text(obj["role"], f"{where}.role", one_line=True), files))
    return Config(title, intro, languages, components)


def anchor(text: str) -> str:
    """GitHub-style heading anchor."""
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def md_text(text: str) -> str:
    """Plain text made safe for a Markdown heading or link text (shown literally, no HTML)."""
    return re.sub(r"([\\`*_\[\]<>&])", r"\\\1", text)


def fence_for(code: str) -> str:
    longest = max((len(run) for run in re.findall(r"`+", code)), default=0)
    return "`" * max(3, longest + 1)


def read_source(root: Path, rel: str, where: str) -> str:
    path = root / rel
    if not path.is_file():
        raise ConfigError(f"missing file: {rel} ({where})")
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        raise ConfigError(f"file resolves outside the repository (symlink?): {rel} ({where})") from None
    try:
        text = path.read_bytes().decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise ConfigError(f"cannot read {rel} as UTF-8 ({where}): {exc}") from exc
    text = text.replace("\r\n", "\n")
    return text[:-1] if text.endswith("\n") else text


def render(config: Config, root: Path) -> str:
    out: List[str] = [f"# {md_text(config.title)}", ""]
    if config.intro:
        out += [config.intro, ""]
    for n, component in enumerate(config.components, 1):
        out.append(f"{n}. [{md_text(component.title)}](#{anchor(f'{n}. {component.title}')})")
    out.append("")
    for n, component in enumerate(config.components, 1):
        out += [f"## {n}. {md_text(component.title)}", "", component.role, ""]
        first = True
        for language in config.languages:
            names = component.files.get(language.key) or []
            if not names:
                continue
            summary = html.escape(", ".join(name.replace("\\", "/") for name in names), quote=False)
            out += [f"<details{' open' if first else ''}>",
                    f"<summary><b>{html.escape(language.label, quote=False)}</b> {SEPARATOR} "
                    f"<code>{summary}</code></summary>", ""]
            first = False
            for name in names:
                rel = repo_path(language.dir, name, "")
                code = read_source(root, rel, f"component {component.title!r}, language {language.key!r}")
                fence = fence_for(code)
                out += [f"<!-- source: {rel} -->", f"{fence}{language.fence}", code, fence, ""]
            out += ["</details>", ""]
    return "\n".join(out).rstrip("\n") + "\n"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="gen_code_by_component.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", required=True, type=Path, help="components JSON file")
    ap.add_argument("--root", required=True, type=Path, help="repository root")
    ap.add_argument("--out", default=DEFAULT_OUT, metavar="PATH",
                    help=f"page to write, relative to --root (default: {DEFAULT_OUT})")
    ap.add_argument("--check", action="store_true",
                    help="write nothing; exit 1 when the page on disk is stale or missing")
    return ap


def quote_command(parts: Sequence[str], windows: Optional[bool] = None) -> str:
    """Shell-ready command text: cmd.exe-style quoting on Windows, POSIX quoting elsewhere."""
    if windows is None:
        windows = os.name == "nt"
    return subprocess.list2cmdline(list(parts)) if windows else shlex.join(list(parts))


def harden_output_streams() -> None:
    """Never crash on a console/pipe whose encoding cannot represent a path or message."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="backslashreplace")
            except (OSError, ValueError):
                pass


def _fail(message: str) -> int:
    print(f"error: {message}", file=sys.stderr)
    return 2


def main(argv: Optional[Sequence[str]] = None) -> int:
    harden_output_streams()
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:  # argparse exits 2 on bad arguments, 0 for --help
        return exc.code if isinstance(exc.code, int) else 2
    if not args.root.is_dir():
        return _fail(f"root is not a directory: {args.root}")
    root = args.root.resolve()
    out_path = Path(os.path.normpath(str(root / args.out)))
    try:
        out_path.relative_to(root)
        out_path.resolve().relative_to(root)
    except ValueError:
        return _fail(f"--out must stay inside the root: {args.out}")

    try:
        page = render(load_config(args.config), root)
    except ConfigError as exc:
        return _fail(str(exc))

    if args.check:
        try:
            current: Optional[str] = out_path.read_bytes().decode("utf-8").replace("\r\n", "\n")
        except (OSError, UnicodeDecodeError):
            current = None
        if current == page:
            print(f"up to date: {out_path}")
            return 0
        command = quote_command(["python", Path(__file__).name, "--config", str(args.config),
                                 "--root", str(args.root), "--out", args.out])
        print(f"{args.out} is stale or missing; regenerate it with: {command}", file=sys.stderr)
        return 1

    try:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(page.encode("utf-8"))  # bytes: keep LF on every platform
    except OSError as exc:
        return _fail(f"cannot write {out_path}: {exc}")
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
