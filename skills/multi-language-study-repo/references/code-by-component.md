---
title: Code by component page
tags: [documentation, code-by-component, github-details, medium, generated-docs, drift-guard, single-language]
---

# Code by component

Readers compare how each language expresses the same role. So the code page is
organised by pattern component, and every component shows the same code in
every chosen language, like language tabs. GitHub Markdown has no tabs, so each
language is a collapsible `<details>` section. Medium has no tabs, so each
language is a labelled code block in a fixed language order.

The language set is a per-project decision. With ONE language the page works
unchanged: one `<details open>` section per component, no comparison, and the
page still guarantees whole-file code that cannot drift from the source tree
(the generator and `check_docs.py` accept a one-entry `languages` list).

The page is generated from the source tree and guarded in CI. Never hand-type
or edit it; whole files only, never excerpts.

## 1. Components and order

Order for a typical pattern (rename for the topic, keep the flow from the
abstraction to the caller):

| # | Component | Typical content |
| --- | --- | --- |
| 1 | Abstraction (pattern interface) | interface / Protocol / type; adapters from functions |
| 2 | Concrete implementations | one class per variant |
| 3 | Value object | immutable data the variants work on; validates itself |
| 4 | Context | holds the abstraction by composition, delegates, swappable at runtime |
| 5 | Client (demo) | picks variants, hands them to the context, prints the demo text |

Other topics rename the roles (for example Observer: subject interface,
concrete observers, event value object, subject, client), but keep the order.
Language labels and order are fixed everywhere: `Java 25`, `Python 3`,
`JavaScript (ES2026)`, `TypeScript 7` (keep only the repo's chosen languages
and versions, in that order).

Design the source files for this page: map each component to whole files per
language (for example the Python Protocol and function adapter in their own
module, concrete classes in another). A component may list several files
(Java: interface plus a named-wrapper class; Python: `demo.py`, `__main__.py`,
`__init__.py` for the client). Give each language's list in the config.

## 2. Config (`components.json`)

```json
{
  "title": "Code by component — Java 25 · Python 3 · JavaScript (ES2026) · TypeScript 7",
  "intro": "This page reads the <pattern> example component by component: the same role in every language, one collapsible section per language. Files are shown whole and generated from the source tree, so they cannot drift. Run commands are in each language folder.",
  "languages": [
    { "key": "java",       "label": "Java 25",             "fence": "java",       "dir": "java/src/main/java/<package path>/" },
    { "key": "python",     "label": "Python 3",            "fence": "python",     "dir": "python/src/<python_package>/" },
    { "key": "javascript", "label": "JavaScript (ES2026)", "fence": "javascript", "dir": "javascript/src/" },
    { "key": "typescript", "label": "TypeScript 7",        "fence": "typescript", "dir": "typescript/src/" }
  ],
  "components": [
    {
      "title": "<Abstraction>",
      "role": "<One sentence: the pattern role this component plays.>",
      "files": {
        "java": ["<Abstraction>.java"],
        "python": ["<abstraction>.py"],
        "javascript": ["<abstraction>.js"],
        "typescript": ["<abstraction>.ts"]
      }
    }
  ]
}
```

- `languages` order = display order = label order everywhere.
- `dir` is the language folder relative to `--root`; component paths are
  relative to it.
- `files[<lang key>]` lists paths relative to that language's `dir`, in
  display order. List every language for every component yourself: the
  generator skips a language that has no files for a component, so an
  omission is not reported. After generating, check that each component shows
  all chosen languages (for example `grep -c "<details" docs/05-code-by-component.md`
  equals components times chosen languages).
- Paths must stay inside the repo (no absolute paths, no `..`, no symlinks
  leading outside); a missing source file or invalid config exits 2.
- `scripts/components.example.json` in this skill is a complete generic copy
  (four languages; delete the entries of the languages you do not use).

Single-language config (same schema, one entry in `languages`, one key in
every component's `files`):

```json
{
  "title": "Code by component — Java 25",
  "intro": "This page reads the <pattern> example component by component. Files are shown whole and generated from the source tree, so they cannot drift. Run commands are in the [java folder](../java/README.md).",
  "languages": [
    { "key": "java", "label": "Java 25", "fence": "java", "dir": "java/src/main/java/<package path>/" }
  ],
  "components": [
    {
      "title": "<Abstraction>",
      "role": "<One sentence: the pattern role this component plays.>",
      "files": { "java": ["<Abstraction>.java"] }
    }
  ]
}
```

## 3. GitHub page (`docs/05-code-by-component.md`)

Generated structure:

- H1 with the title, one intro paragraph (links to the language folders and
  their READMEs for run commands), and a numbered component table of contents.
- Per component: `## n. <Component>`, one sentence on its pattern role, then one
  collapsible section per language, the first one `open`.
- Several files for a component in one language: each file gets its own
  `<!-- source: ... -->` line and fenced block inside the same `<details>`.

````markdown
<details open>
<summary><b>Java 25</b> · <code>FileName.java</code></summary>

<!-- source: java/src/main/java/<package path>/<Abstraction>.java -->
```java
...exact file content...
```

</details>
````

Format rules (the guard depends on them):

- The `<!-- source: <repo-relative path> -->` line sits on the line directly
  above the fence (no blank line between), and the path is relative to the
  repo root and stays inside it. A marker not followed by a fence is reported
  by `check_docs.py`, because it would guard nothing.
- Fence language = the config's `fence` (`java`, `python`, `javascript`,
  `typescript`). If a file itself contains a run of backticks, the fence is
  longer than the longest run.
- Content is the file with LF line endings and one trailing newline removed.
- A blank line separates `<summary>`, the marker/fence and `</details>`, or
  GitHub does not render the Markdown inside `<details>`.
- `.gitattributes` with `* text=auto eol=lf` keeps checkouts on Windows
  byte-comparable.

## 4. Medium article

Medium is produced from the same components, never retyped:

- One section for all chosen languages' code, with the same five components in
  the same order. Per component: a short H3 heading, one sentence on its role,
  then per language a bold label paragraph `Java 25 — <File>` followed by a code
  block with the whole file, in the fixed language order. With one language the
  label paragraph can be dropped when the section heading already names the
  language.
- Before the components: 2-4 sentences per language on the idioms used (a
  compact list; one language: one short paragraph), plus links to each
  language folder and the run commands.
- Code blocks must be byte-identical to the repo files: hash-check each one.
  Medium-specific block mechanics (explicit language, blank lines) belong to
  `skills/medium-publishing/SKILL.md`.

## 5. Generate and check

```bash
python scripts/gen_code_by_component.py --config components.json --root <repo> [--out docs/05-code-by-component.md]
python scripts/gen_code_by_component.py --config components.json --root <repo> --check
python scripts/check_docs.py --root <repo>
```

Use `python3` where `python` is missing or not Python 3 (on Windows keep
`python`; `python3` is often a Microsoft Store stub).

- Without `--check` the page is written. With `--check`, exit 1 means the
  file on disk differs from what the config and sources generate.
- `check_docs.py` independently re-verifies every `<!-- source: ... -->`
  block against its file, so a hand edit is caught by two guards. It also
  reports relative links whose target is missing, escapes the repo root, or
  matches only with different letter case (GitHub paths are case-sensitive);
  links inside code and `#anchor` parts are not checked.
- In CI (`docs` job) run both with `--root .` and `--check`. Fix a failure by
  regenerating, never by editing the page.

## 6. Pitfalls

| Symptom | Cause and fix |
| --- | --- |
| `--check` fails after a code change | The page was not regenerated; run the generator and commit |
| Source drift reported for one block only | The page was hand-edited, or CRLF files were committed; regenerate and add `.gitattributes` |
| Missing source reported (generator exit 2) | A file was renamed or moved but `components.json` still lists the old path |
| Source marker reported as not followed by a fence | A blank line or text sits between the marker and the fence; regenerate |
| Blocks render as plain text on GitHub | Missing blank line after `<summary>` or before `</details>` |
| A language folder holds an extra helper file | Add it to its component's list or keep it out of `src/`; unlisted files are simply not shown |
| A removed language still appears on the page | Remove it from `languages` and from every component's `files`, regenerate, and commit page and config in the same PR as the folder removal (see `repo-layout-and-protection.md`, "Changing the language set later") |
