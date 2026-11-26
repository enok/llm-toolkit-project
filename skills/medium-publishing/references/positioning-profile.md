---
title: Publication positioning profile - what a publication is for, and its budgets
tags: [medium, linkedin, positioning, profile, budgets, system-design, hashtags, titles, drafts-only, check-publication]
---

# Publication positioning profile

AIDA ([aida-narrative.md](aida-narrative.md)) fixes the ORDER of a piece. It does not fix what
the piece is about, how long it runs, or how many hashtags it carries, so a complete, correct,
cited draft can still miss its purpose (`learnings/study-posts-system-design-first-short-teaser.md`).
A positioning profile records those decisions once, as numbers and rules a script and a reviewer
can check. The always-on rule is `rules/publication-positioning.md`; the read-only validator is
`tool-subagents/publication-reviewer.md`; the measuring script is
`skills/medium-publishing/scripts/check_publication.py` (subcommands `post` and `article`, option `--profile`).

## 1. What the profile fixes

| Field | What it decides | Check |
| --- | --- | --- |
| Target roles | The level titles and hooks speak at (for example a senior or lead role, an architect role) | Title, subtitle and hook name a concept at that level |
| Primary focus (and secondary) | What the piece is mainly about; everything else is supporting material | The title names the primary focus; the pattern or tool is the mechanism inside it |
| Pattern placement | Where the study topic may appear (default under a system-design focus: the body only, in one short section) | The study topic is absent from the title and subtitle (`article --title ... --subtitle ... --forbid-title <topic>`) and from the post hook (`post --forbid <topic>`) |
| Length budgets | Article words, post characters, hook characters (the hook is the first paragraph of the post: the text before the first blank line) | `article --max-words`, `post --max-chars`, `post --hook-chars` |
| Code budget | Code blocks and lines in the article | `--max-code-blocks`, `--max-code-lines` |
| Image count | Diagrams in the article; one hero image in the post | `--min-images`, `--max-images` |
| Hashtag cap | Most hashtags in the post | `post --max-hashtags` |
| Topic count | Medium topics per story (at most 5) | Chips read back in the publish dialog |
| Title rules | Title at most 100 characters, subtitle at most 140 | Counted before typing |
| Approval mode | Exactly two names: `gated` (default: every external write waits for explicit approval) and `drafts-only` (creating the Medium draft and the LinkedIn draft is pre-approved and nothing else is) | Procedure of the publishing skills |
| Voice | Person, tone, banned patterns (hype words, emojis, long dashes), labels such as "my reading" | Reviewer agent |

## 2. Where a consumer keeps it

- The profile belongs to the consumer project, never to this toolkit: file `PUBLICATION-PROFILE.md`
  at the project root, or the path the project's own instructions name. The toolkit holds only the
  template (section 4) and the defaults (section 5).
- Read it at the start of every article or post task, before drafting. Show which profile was used
  (path and the budget values) with the `NOT POSTED` draft.
- Precedence: the user's current message, then the profile, then these defaults. A profile overrides
  older publishing rules where they conflict (for example a hashtag count that followed topic
  coverage). Never invent a profile or a target role: when none exists, ask once, then use the
  defaults and say so.
- A profile change is a decision of the user; record it in the profile file (a PR when the project
  protects its default branch), not in a chat.

## 3. Machine-readable settings

The profile ends with one fenced `json` block. `check_publication.py --profile <path>` reads the
first fenced `json` block of the file; the Markdown around it is for people. The numbers below are
one consumer's example values (for instance 1,300 article words), not toolkit defaults; section 5
lists the defaults (1,500 article words).

````markdown
```json
{
  "post": {"max_chars": 1300, "max_hashtags": 5, "hook_chars": 200},
  "article": {"max_words": 1300, "max_code_blocks": 1, "max_code_lines": 15,
              "min_images": 2, "max_images": 3},
  "forbid_title_terms_from": "pattern name of the study (pass with --forbid-title)"
}
```
````

- `post.max_chars`, `post.max_hashtags`, `post.hook_chars` map to the `post` options of the same
  names; `article.*` map to the `article` options (`--max-words`, `--max-code-blocks`,
  `--max-code-lines`, `--min-images`, `--max-images`).
- `forbid_title_terms_from` is a note, not a term: the study topic changes per study, so its name is
  passed on the command line for each run: `article --forbid-title "<pattern name>"` (title and
  subtitle) and `post --forbid "<pattern name>"` (the hook).
- Each limit comes from the first of: its command-line flag, the profile, the script's built-in
  default (section 5). A key the profile leaves out falls back to the default; a key the script does
  not know (such as `forbid_title_terms_from`) is ignored. A missing or malformed json block is an
  input error (exit 2). The title (100) and subtitle (140) limits are fixed.
- Keep numbers and prose in step: when a budget changes, change both. The script and the reviewer
  read the numbers; people read the prose.
- Run: `python skills/medium-publishing/scripts/check_publication.py article <draft> --profile PUBLICATION-PROFILE.md --title "<title>" --subtitle "<subtitle>" --forbid-title "<topic>"`
  and `... post <draft> --profile PUBLICATION-PROFILE.md --forbid "<topic>" --require-link "<article url>"`. Use `python3` where `python` is missing or is not Python 3.
  Exit 0 passes, 1 means a rule failed (do not show the draft as ready), 2 means a usage or file error.

## 4. Generic template

Copy to the consumer project and replace every `<...>`.

````markdown
# Publication profile: <series or project name>

Read by the toolkit's publishing skills, the publication-reviewer agent and
`check_publication.py --profile`. Stated by <owner> on <date>; it overrides older publishing
rules where they conflict.

## Positioning

- Target roles: <role one>; <role two>. Titles and hooks speak at that level.
- Primary focus: <main subject>. Secondary: <subjects>.
- The <study topic> is internal to the article: the mechanism inside the <primary focus> story,
  introduced in the body in one short section. Never in the title, subtitle or post hook.
- Language of code: <language and version>. The repo stays the complete teaching material; the
  article links to it instead of repeating it.

## Medium article

- Shape: <primary focus>-first, AIDA (Attention, Interest, Desire, Action).
- At most <N> words of body text. <N> diagrams, one of them the hero diagram.
- At most <N> code snippet(s) of at most <N> lines (or none).
- Title at most 100 characters, subtitle at most 140; both name the problem or capability at the
  target role's level, never the study topic's name.
- Ends with a "Your next step" section, then the repo and post links.
- <N> Medium topics, led by the primary focus.

## LinkedIn post

- A short teaser whose job is to send readers to the article, structured with AIDA.
- At most <N> characters in total; the hook (the first paragraph, the text before the first blank
  line) is at most <N> characters.
- One primary call to action: the article link. The repo link is optional and secondary.
- At most <N> hashtags, each naming a topic the post text mentions.
- Image: the hero diagram, legible at feed width.

## Voice and gates

- <person, tone>; no hype words, emojis or long dashes.
- Every claim is backed by the repo or its fact table; "my reading" labels where a source does
  not call something by the topic's name.
- Approval mode: <gated | drafts-only>. `gated` (default): every external write waits for explicit
  approval. `drafts-only`: creating the Medium draft and the LinkedIn draft for final review is
  pre-approved; publish, post, edit, delete, pointer and unlist only after explicit approval of that action.

## Machine-readable settings

(the fenced json block of section 3)
````

## 5. Toolkit defaults when no profile exists

These are defaults, general guidance for a short study publication. They are not any person's
profile; a real profile replaces every row it states.

| Setting | Default |
| --- | --- |
| Article body | at most 1,500 words |
| Article diagrams | 2-3, one of them the hero diagram |
| Article code | at most one block of at most 15 lines (or none) |
| Title / subtitle | at most 100 / 140 characters, naming the problem or capability, not the study topic |
| Post length | at most 1,300 characters in total |
| Post hook | the first paragraph (text before the first blank line), at most 200 characters |
| Hashtags | at most 5, each backed by text in the post |
| Medium topics | 5, led by the main subject |
| Target role | ask once at intake; without an answer, position at the highest level the body supports |
| Approval mode | `gated`: explicit approval of each draft creation, publish, post, edit and delete (`rules/external-write-authorization.md`) |

The script's built-in defaults are these numbers, so without a profile the plain commands apply
them:

```bash
python skills/medium-publishing/scripts/check_publication.py article draft.md \
  --title "<title>" --subtitle "<subtitle>" --forbid-title "<topic name>"
python skills/medium-publishing/scripts/check_publication.py post post.txt \
  --forbid "<topic name>" --require-link "<article url>"
```

## 6. Using the profile in a run

1. Read the profile (or state that the defaults apply) before drafting; copy its budgets into the
   task's acceptance criteria (`workflows/task-quality-loop.md`).
2. Draft to the budgets, not to the source's size: the repo is the complete material and the
   article links to it ([system-design-article.md](system-design-article.md)).
3. Run `check_publication.py` on the article and on the post; a non-zero exit is a defect list.
4. Run the `publication-reviewer` agent for what a script cannot measure (title level, hook,
   whether the pattern stays internal, claim support).
5. Show the profile used, the stage map ([aida-narrative.md](aida-narrative.md)), the script output and
   the reviewer verdict with the `NOT POSTED` drafts.
6. In `drafts-only` mode create the two drafts (pre-approved) and stop; every other external write
   still waits for explicit approval of that action; replacing an already published piece follows
   [replace-published-story.md](replace-published-story.md).
