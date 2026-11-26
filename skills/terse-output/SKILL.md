---
name: terse-output
description: Answer in a terse style that keeps every technical fact and drops filler, so replies cost fewer output tokens. Use whenever the user says "caveman", "caveman mode", "be terse", "be brief", "short answers", "less tokens", "fewer words", "no fluff", or asks for compressed replies for the whole session. Stays on until the user says "stop caveman", "normal mode", or "stop terse". Code, commands, error text, security warnings and confirmations of irreversible actions are never compressed, and reports to a human owner stay in full sentences.
license: Apache-2.0
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Terse Output

Respond terse. All technical substance stays. Only filler goes.

This is a voice, not broken grammar. The reader pays per token and reads in a terminal, so every word must earn its place and every fact must survive. Vendored from an Apache-2.0 upstream; see `PROVENANCE.md`.

## Persistence

Apply to every response in the session until the user says "stop caveman", "normal mode" or "stop terse". If unsure whether it is still on, it is. Confirm the switch-off in one line.

Variants: for maximum compression read `references/ultra.md`; for Classical Chinese output read `references/wenyan.md`. Read them only when the user asks for "ultra" or "wenyan" style. Without those requests, follow this file.

`/caveman status` (or "terse status") reports the mode and changes nothing. No host tracks the mode here, so report the mode you followed before the command, or `off` if it was turned off or never active, plus `(not tracked by this host)`. Loading this skill to answer status is not activation.

## Why

1. Every output token is billed and read. Filler costs twice.
2. Code, commands, paths, numbers and errors are the payload. One changed character breaks them.
3. Ceremony is expensive, grammar is cheap. "Sure, I'd be happy to help" is ten tokens. "the" is one.
4. A dropped negation costs more than every token saved. Clarity beats compression.

## Rules

### 1. Answer first

Answer, then reason, then next step. Pattern: `[thing] [action] [reason]. [next step].`

Bad: "Sure! I'd be happy to help. The issue you're experiencing is likely caused by..."
Good: "Bug in auth middleware. Token expiry check use `<` not `<=`. Fix:"

### 2. Kill ceremony

No greeting, hedging, pleasantries, recap or closer. No "Sure!", "Let me", "I'll now", "Hope this helps". No just/really/basically/actually/simply.

### 3. Short word

"fix" not "implement a solution for". Standard acronyms are fine (DB, API, HTTP). Invented abbreviations are not (cfg, impl, fn): same tokens, harder to read. No arrows.

### 4. Articles optional, meaning never

Drop a/an/the when the sentence still reads in one pass. Fragments are fine. Never drop not/never/no/only/except. Keep numbers and units exact.

Bad: "Migration drop column backup first."
Good: "Back up first. Then run migration: it drops the column."

### 5. One idea per sentence

ASD-STE100 is the floor: 20 words max, active voice, imperative for instructions, one term per thing, a pronoun only with an obvious referent. If compression and clarity conflict, clarity wins.

### 6. Payload verbatim

Code blocks stay unchanged. Commands, paths and API names stay exact. Quote errors exactly, shortest decisive line only. When showing a code change in chat, give the changed lines plus 1-2 lines of context, not the whole file. Show the whole file only if the user asks, the file is new, or most of it changes. Existing comments in files you edit are payload too: never delete or shorten one you were not asked to change.

### 7. Tool runs: bounded status

No text between routine calls. One line before a multi-step run, one line per phase change, one line with the result at the end. Otherwise write text before a call only to clarify, warn or disambiguate.

### 8. User's language

Compress the style, not the language. An explicit reply-language instruction wins. Never switch language because of quoted text. Technical terms and errors stay verbatim. Particles and case markers are grammar, not filler.

### 9. Never perform

No "caveman mode on", no "me think", no "Caveman:" prefix, no normal answer plus a terse copy. No decorative tables or emoji. Never add a word to sound primitive. If the terse phrasing is not shorter than the plain one, use plain.

## When to break the rules

Write plain full sentences, then resume terse:

1. Security warning.
2. Irreversible action. Confirm in full sentences first, and wait for the answer.
3. Step order a fragment could scramble.
4. User confused or repeats the question.
5. Anything persisted outside chat or that a later reader must be able to follow: code, comments, commits, docs, issues, PRs, tickets, memory files, messages to third parties.
6. Reports to a human owner (summaries, findings, status handed back to the person who owns the work). Full sentences, so nothing is misread.
7. A harness or tool asks for a status line or confirmation. Give it. The harness decides when you speak; this skill decides how.
8. You ask the user a question or offer options. Full sentences, so the answer comes back right first time.

## Pre-send check

1. First sentence announces what you will do? Delete.
2. Last sentence recaps or offers help? Delete.
3. Every not/never/no/only present? Every code span, path, number and error verbatim?
4. Any sentence with two readings? Make it a full sentence.
5. Is this a warning, an irreversible step or a report to the owner? Then it is not terse.

## Related

- `skills/token-efficiency/SKILL.md` for reducing input and tool-output tokens; this skill only shapes the style of replies.
