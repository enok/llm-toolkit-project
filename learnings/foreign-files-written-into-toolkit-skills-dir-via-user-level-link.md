---
title: Foreign files appear in the toolkit skills/ folder through the user-level skills link
category: environment
created: 2026-11-26
tags: [skills, symlink, junction, untracked-files, git-status, search-index, global-install, sync]
---

# Problem
`docs/global-install.md` documents a user-level install that makes a tool's personal skills folder
ONE directory link (symbolic link, or junction on Windows) to the `skills/` folder of the toolkit
checkout; for one tool in its table it creates one link per skill directory instead.
On the machine observed on 2026-11-26 the single link existed, and two entries the repository does
not track sat directly inside the checkout's `skills/`: a folder `synced` and a hidden `.trash`,
both created in the same minute. `synced` held one account-scoped subfolder with 27 entries (26
skill definitions), 328 files in total; `.trash` held 70 files. The personal skills path and the
checkout's `skills/` path resolved to the same inode, so anything written to the personal skills
folder lands in the repository working tree.
Effects seen: `git status -sb` listed both as untracked and `git check-ignore -q skills/synced`
said not ignored (the ignore file has no entry). The scheduled fast-forward job pulls only on a
clean tree and logged "pull skipped (working tree not clean)" on every run that day, though an
older untracked path already caused that. The local search index walks the checkout and skips
dot-folders, two cache folders and links, so it indexed `synced` (`.trash` is skipped) and returned
four of five passages for a query from there, labelled as repository content, although that
content had passed no review or intake step. Separately, the index went from 732 to 876 files in
two hours with no new commit; not recorded whether all of the rise came from `synced`.

# Failed Approaches
None recorded beyond the first attempt described in Problem.

# Solution
Nothing was changed in the observed run (the checkout was read-only for it); no fix was tried.
Detection commands (untested as a recipe; run in the toolkit checkout):
- `git status --short -- skills`
- `git check-ignore -v skills/<name>`
- A jump in the search index file count without a new commit is another signal.
Prevention options, all UNTESTED / not tried in the session:
- Add ignore entries for the two names (repository ignore file or the checkout's local exclude).
- Use one link per skill so the parent folder stays a real folder outside the checkout (the
  install already does this for one tool).
- Build the index walk from the tracked file list.
Reasoned, not observed: a commit made with a stage-everything command here would add the foreign
files to the repository.

# Why
Cause of the exposure: the personal skills path and `skills/` are one directory, so any writer to
the personal folder writes into the working tree. Not recorded: which process wrote the entries,
whether any passage from `synced` changed an answer, whether the entries return after removal, and
whether the other tools in the install table behave the same way.
