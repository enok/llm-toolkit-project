# Provenance

- Source repository: github.com/JuliusBrussee/caveman (no URL is fetched or called by this skill).
- Commit: e74a11c (v4.2.0).
- Date fetched: 2026-11-26.
- Licence: Apache-2.0. `LICENSE` and `NOTICE` are copied unchanged from the upstream repository root. `NOTICE` mostly concerns upstream code that is not vendored here (engine, browse, CLI); it is kept whole so the attribution stays intact.
- Upstream files used: `skills/caveman/SKILL.md`, `skills/ultracave/SKILL.md`, `skills/megacave/SKILL.md`. Nothing else was copied: no scripts, hooks, installers, CLI, proxy, icons or logos.

## Changes made (Apache-2.0 section 4)

- Renamed the skill from `caveman` to `terse-output`; the variants `ultracave` and `megacave` became `references/ultra.md` and `references/wenyan.md`.
- Rewrote the frontmatter to this repository's convention (broader trigger phrases in the description, `license`, `metadata`). Removed `disable-model-invocation` from the variants because references are not skills.
- Removed the hook-related text (`Caveman mode:` hook value, `/caveman-compress` exemption, `/caveman ultra` and `wenyan` aliases) because those parts do not exist in this repository. Added "terse status" wording that works without a hook.
- Neutralised the "caveman" voice words in the prose of the rules ("Never perform", variant intros) so the skill reads as plain English. Trigger phrases "caveman" and "stop caveman" are kept so users of the upstream name still reach it.
- Added to "When to break the rules": reports to a human owner, and anything a later reader must be able to follow, stay in full sentences; irreversible-action confirmation waits for the answer. Added a fifth pre-send check and a Related link.
- Added a notice at the top of each reference saying the base exemptions still apply.
- Added `evals/` cases written for this repository.

## Trademark

This is a renamed vendored derivative. It is not affiliated with, endorsed by or sponsored by the upstream project. "Caveman", its wordmark and its logo are trademarks of their owner, Julius Brussee; Apache-2.0 grants no trademark rights. The upstream name appears here only to say where the text came from and which phrases trigger the skill.

## Update rule

Pinned to the commit above. On any update, re-diff the three upstream `SKILL.md` files against this directory before accepting changes.
