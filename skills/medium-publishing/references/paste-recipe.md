---
title: Medium paste recipe
tags: [medium, publishing, html, clipboard, code-blocks, browser-automation]
---

# Medium paste recipe

How to shape the HTML and move it into the Medium editor so code, images, and
text arrive intact. `scripts/medium_paste_html.py build` automates only the
mechanical code-block rules (attributes, a space on empty lines, non-ASCII
encoding). The other rules are the author's job; `check` reports violations.

Observed live in the original session: explicit mode 2 with `java` (auto-detect
had guessed Lua), empty lines splitting a code box, `<br>` not helping, Windows
PowerShell 5.1 mangling non-ASCII, and pasted images being re-hosted on Medium's
CDN. Everything else below is expected behaviour, marked "untested" where it
matters; confirm it with [editor-verification.md](editor-verification.md).

Run the script as `python skills/medium-publishing/scripts/medium_paste_html.py ...`;
use `python3` where `python` is missing or is not Python 3 (Windows often has a
`python3` Store stub instead, so prefer `python` or `py -3` there).

## 1. HTML rules

| Rule | Why | Handled by |
| --- | --- | --- |
| Code blocks are `<pre data-code-block-mode="2" data-code-block-lang="<lang>">` | Medium honoured the explicit language for Java; auto-detect guessed Lua. Other languages are expected to behave the same (untested). | `build`; `check` flags `<pre>` without attributes |
| Plain text blocks (logs, expected output, unknown language) are `<pre data-code-block-mode="0">` | Mode 0 is plain text, no highlighting. | `build` |
| Every empty line inside a `<pre>` becomes a single space (`learnings/medium-paste-splits-code-blocks-at-blank-lines.md`) | A truly empty line split one file into several code boxes; `<br>` instead of newlines did not help. Pasting back still yields valid code; Python ignores whitespace-only lines. | `build`; `check` flags remaining empty lines |
| No `<table>`: convert to a bullet list (`Label: value`) or a mode-0 `<pre>` with aligned columns | Medium has no tables. | author; `check` flags |
| No inline `<code>`: convert to plain text (use `<em>` or `<strong>` only when emphasis is wanted) | Medium has no inline-code style. | author; `check` flags |
| No markdown left in the HTML: scan for `](http` (`learnings/validators-must-scan-rendered-html-for-markdown-leftovers.md`) | A title like `[[x] y](url)` rendered as raw text. Scan the rendered HTML, not only the Markdown source. | author; `check` flags |
| Images are absolute `https` URLs from `raw.githubusercontent.com/<owner>/<repo>/<sha>/<path>` | Medium re-hosts pasted images, so the source must be fetchable by anyone; a SHA (not a branch) stops caching from serving a stale diagram. | author; `check` flags unpinned or foreign URLs |
| Entity-encode every non-ASCII character as `&#NNN;` | See section 3. | `build`; `check` flags leftovers |
| Start the document with the `<h1>` title | The title field is expected to take the first heading (untested); confirm it after pasting. | author |

Language names used by the script (extension to Medium language): `java`,
`py` to `python`, `js` to `javascript`, `ts` to `typescript`, `kt` to `kotlin`,
`go`, `rs` to `rust`, `cs` to `csharp`, `rb` to `ruby`, `sh` to `bash`, `sql`,
`json`, `yaml`/`yml` to `yaml`, `xml`, `html`, `css`. Only `java` was seen
working live. Every other name, including `python`, `javascript`, and
`typescript`, is an unverified guess at the names Medium accepts: after the
first paste containing a new language, read the attributes back and look at the
rendered highlighting ([editor-verification.md](editor-verification.md)). An
unknown extension or class falls back to mode 0.

## 2. How `build` finds the language

In priority order, per `<pre>`: a `language-<x>` (or `lang-<x>`) class on the
`<pre>`; the same on a sole wrapping `<code>` (the wrapper is then removed);
an existing `data-code-block-lang`; the text of a `<strong>path.ext</strong>`
label directly before the block (`<p><strong>src/Duck.java</strong></p>`). The
label only counts when nothing but whitespace sits between it and the `<pre>`.
Existing `<pre>` attributes other than the code-block pair are dropped. A
second `build` over the output changes nothing.

Label blocks with their file name in the article source so the language is
derivable and readers see which file they are reading.

## 3. Non-ASCII and the Windows clipboard

Windows PowerShell 5.1 `Set-Clipboard -AsHtml` mangles non-ASCII text on the
HTML clipboard (a right single quote became the replacement character;
`learnings/powershell-set-clipboard-ashtml-mangles-non-ascii.md`).
Entity-encode first (`build` does this for the whole document, including
`<pre>` bodies; `check` fails while any non-ASCII byte is left), then the file
is pure ASCII and encoding no longer matters.

```powershell
$html = [System.IO.File]::ReadAllText((Resolve-Path "article.paste.html").Path, [System.Text.Encoding]::ASCII)
Set-Clipboard -AsHtml -Value $html
```

Keep the paste file in a fresh filename per revision and confirm its length or
a marker on the machine that runs this command; one session saw a copy to an
existing path keep the old bytes
(`learnings/device-commit-to-existing-path-can-keep-stale-bytes.md`).

## 4. Pasting into the editor

1. In the user's own browser, open a new story (never automate login).
2. Put the HTML on the clipboard as `text/html` (below).
3. Click the title field, press Select All (Ctrl+A, Cmd+A on macOS), press
   Paste (Ctrl+V, Cmd+V on macOS). Select All first so the paste replaces the
   editor content instead of landing in the middle of an earlier attempt.
4. Wait for images to finish re-hosting (they move to Medium's CDN), then run
   [editor-verification.md](editor-verification.md).

macOS and Linux (not exercised in the original session): any tool that places
`text/html` on the clipboard works, for example `xclip -selection clipboard
-t text/html -i article.paste.html` (X11) or `wl-copy --type text/html <
article.paste.html` (Wayland). macOS has no stock command for HTML, so use a
small AppleScript or Swift helper that writes the `public.html` pasteboard
type, or open the paste file in a browser tab, select the rendered page, and
copy it. After any alternative, verify the editor DOM exactly as for Windows;
a rich copy from a rendered page may drop the code-block attributes
(untested).

## 5. Pre-flight checklist

- `check` exits 0, run with `--repo-raw-prefix https://raw.githubusercontent.com/<owner>/<repo>/`.
- The commit `<sha>` in the image URLs contains the final diagram files and is
  pushed (a raw URL for an unpushed commit returns 404 and the image is lost).
- Code files in the repo and the code in the article are the same bytes.
- Title is at most 100 characters and subtitle at most 140
  ([publish-dialog.md](publish-dialog.md)).
