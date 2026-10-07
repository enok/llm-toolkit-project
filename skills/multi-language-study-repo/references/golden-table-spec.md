---
title: Shared example spec and golden table
tags: [example-spec, golden-table, testing, consistency, multi-language, single-language, design-patterns]
---

# Shared example spec and golden table

One spec file, named `EXAMPLE-SPEC.md` throughout this skill and in lane
prompts, is the single source of truth for the example in every chosen
language. The language set is a per-project decision and one language is
fine. With several languages the spec keeps parallel lanes consistent: each
implements the same model, passes the same golden table and prints the same
demo text. With one language it still fixes the model, the tests and the demo
text, and keeps the docs honest. Write it BEFORE any code, keep the example a
focused slice that explains the topic (not a full application), and give every
lane the same copy.

`EXAMPLE-SPEC.md` lives in the work folder and every lane gets the same copy.
Its human-readable parts (domain, participants, golden table, demo output) are
copied into `docs/03-application-example.md`; the lane instructions (naming
map, layout, toolchain targets) stay in `EXAMPLE-SPEC.md` only. The repo name
is `<repo>` = `<prefix>-<topic>`; `<pattern>` below is the `<topic>` when it is
a design pattern.

## Rules that make it work

1. **Integer money.** Amounts are integers in the smallest unit (cents). No
   floating point money, no locale-dependent formatting. Format `5589` as
   `55.89` with integer division and padding, never with floats.
2. **One golden table.** A grid of inputs and the exact expected integer
   outputs. Every language's tests assert ALL cells, not a sample.
3. **Exact demo text.** The demo entry point of every language prints the same
   text; each language has a test that compares captured output to it
   (normalise line endings to LF first; Windows prints CRLF).
4. **Pick edge cases deliberately** for the golden rows: exactly at a
   threshold and one below it, zero, a value that rounds up just past an exact
   multiple, a large value. Rounding uses integer ceil-division (`Math.ceilDiv`
   in Java, `-(-a // b)` in Python, integer-only arithmetic in JS and TS with
   inputs kept as safe integers); keep the rule of each chosen language only.
5. **Verify the table independently** (hand-check, or a few lines of Python)
   before any lane starts. A wrong cell is copied into every test suite (one
   per chosen language) and into the docs.
6. **Idiomatic errors, same rule.** Invalid input is rejected in every
   language with that language's argument error (table below).
7. **Open abstraction.** The pattern's abstraction stays open for extension
   (not sealed), so a new variant needs no change to the context; plain
   functions or lambdas must be accepted wherever the pattern's behavior is a
   single operation.

## Template

````markdown
# <topic> - shared example spec (EXAMPLE-SPEC.md, single source of truth)

All implementations (<chosen languages and versions; one or more>) and the example docs MUST
implement exactly this model and pass exactly this golden table. Keep it a
focused slice that explains the pattern, NOT a full application.

## Domain: <one-line domain>

<2-3 sentences: what varies, what stays fixed, why the pattern fits.>

### Participants (pattern roles)

| Role | Name | Notes |
| --- | --- | --- |
| <abstraction role> | `<Name>` | <operation signature in prose; integer return> |
| <concrete role> | `<Name>` | <exact rule with numbers, including thresholds> |
| <ad-hoc variant> | function/lambda | proves "behavior = a value" |
| <context role> | `<Name>` | holds the abstraction by composition; <operation>; swappable at runtime |
| <value object> | `<Name>` | <fields, ranges>; immutable |

Rules:
- Money is integer cents everywhere.
- <value object> rejects <invalid input> (language-idiomatic argument error).
- <context> rejects a null/None/undefined abstraction at construction and on swap.
- The abstraction stays OPEN; functions/lambdas are accepted.
- Each language folder has a tiny demo entry point that runs input A through all
  variants, then shows a runtime swap. Demo output (exact):

```text
<line 1: input summary>
<variant 1> -> <result> | <total>
...
Swapped at runtime: <from> -> <to> | total <a> -> <b>
```

(Formatting rule: cents as `units.cc`. The only allowed label difference
between languages: <for example "(lambda)" vs "(function)" in Python>.)

## Golden table (every implementation's tests assert ALL cells)

| Input | <field 1> | <field 2> | <variant 1> | <variant 2> | <variant 3> | <ad-hoc> |
| --- | --- | --- | --- | --- | --- | --- |
| A | ... | ... | ... | ... | ... | ... |
| B (at threshold) | ... | ... | ... | ... | ... | ... |
| C (below threshold, zero edge) | ... | ... | ... | ... | ... | ... |
| D (large, rounds up) | ... | ... | ... | ... | ... | ... |

(State whether values are totals or component amounts. Also list the
component-only values if they help debugging.)

Additional required tests (each chosen language): runtime swap (<input> from <a> to
<b>); null abstraction rejected (constructor and setter); each invalid input
rejected; demo output equals the exact text above.

## Naming map

Keep one column per chosen language and drop the others (one language: a
single column). The columns below are the four-language case.

| Concept | Java 25 | Python 3 | JavaScript | TypeScript |
| --- | --- | --- | --- | --- |
| Abstraction | `interface <Name>` | `Protocol` class `<Name>` | duck-typed object or function (JSDoc `@typedef`) | `interface <Name>` |
| Concrete variants | one class per file | classes in one module | classes in one module | classes in one module |
| Value object | `record` | frozen slotted `dataclass` | frozen object / class | `readonly` fields |
| Files | `PascalCase.java` | `snake_case.py` | `kebab-case.js` | `kebab-case.ts` |
| Invalid argument | `IllegalArgumentException` | `ValueError` | `RangeError` (range), `TypeError` (type) | same as JS |
| Null check | `Objects.requireNonNull` | explicit `is None` check | explicit `== null` check | explicit check |

## Layout and toolchain targets

<copy the repo tree and the version table from repo-layout-and-protection.md and toolchain-notes.md>

## Lane rules

- Each lane writes only inside its own folder (one language: one lane).
- Tests assert every golden cell, the swap, the rejections, and the demo text.
- Whole, small files: the docs show files whole, so one pattern component
  maps to one file or a small, fixed group of files per language.
- No dependencies beyond the test framework and the toolchain.
````

## Choosing the example

- A domain every reader grasps in one sentence (shipping cost, discount,
  notification channel, sort order), with 3 concrete variants plus one
  ad-hoc function.
- Numbers that make thresholds and rounding visible, so a wrong
  implementation fails a golden cell.
- No I/O, network, clock or randomness: results must be deterministic.
- Keep it under roughly 150 lines of code per language, so the code-by-component
  page stays readable ([code-by-component.md](code-by-component.md)).

## After the lanes finish

The root runs the demo of each language, diffs the output against the exact
text, and confirms every test file contains every golden cell (a quick
`grep` for each value in each language's tests catches an omitted row). Then
the example docs and diagrams are written from this spec, never from memory of
the code.
