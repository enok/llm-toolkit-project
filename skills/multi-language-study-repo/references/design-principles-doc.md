---
title: Design-principles page of a study repo
tags: [study-repo, design-principles, solid, architecture-principles, docs, tension, citations]
---

# Design-principles page (`docs/06-design-principles.md`)

Standing requirement: every study repo correlates its pattern with the design and architecture
principles it applies, not only with the pattern's own definition. The page is generic for any
pattern. It feeds the article's "Principles behind it" section and the post's one principle line
(`skills/medium-publishing/references/content-angle.md`); the three quote the same facts.

## What the page must hold

1. **Principle table.** One row per applicable principle: how the pattern realises it (name the
   participant or seam that does it) and where it can be violated.
2. **Principles that do not apply.** One line each with the reason. Skip a principle only with a
   reason; never force a mapping that does not hold.
3. **Tension and when not to use it.** The principle the pattern can violate when misused (for
   example YAGNI or KISS when only two fixed variants exist) and a rule of thumb for when not to
   use the pattern.
4. **Architecture-level correlation.** For each application on `docs/09-architecture-perspective.md`,
   the principle it realises and the seam where it does. If there is no architecture page, say so
   in one line.
5. **Sources.** Only when the page attributes or quotes something (see Rules).

## Principles to check

Cover these groups when they apply. Definitions are generic and well known.

| Group | Principle | Meaning in one line |
| --- | --- | --- |
| SOLID | SRP | A module has one reason to change |
| SOLID | OCP | Add behaviour by extension, without editing working code |
| SOLID | LSP | Any implementation can stand in for its contract without surprising callers |
| SOLID | ISP | Clients depend only on the operations they use |
| SOLID | DIP | High-level policy depends on abstractions, not on concrete details |
| Object-oriented design | Encapsulate what varies | Isolate the part that changes behind a stable boundary |
| Object-oriented design | Program to an interface | Callers use the contract, not the implementation |
| Object-oriented design | Favor composition over inheritance | Combine collaborating objects instead of extending a class |
| Object-oriented design | Loose coupling | Interacting objects know as little about each other as they can |
| General | DRY, KISS, YAGNI | One source of each fact; the simplest design that works; nothing built for a need that is not there |
| General | Separation of concerns, high cohesion / low coupling, least knowledge | Each part has one concern; related things together; talk only to close collaborators |
| Architecture | Dependency rule (clean / hexagonal) | Source dependencies point inward, toward policy |
| Architecture | Policy vs detail | Business rules do not depend on delivery or storage details |
| Architecture | Stable abstractions | The more a module is depended on, the more abstract it is |

For the object-oriented group use the list the study source names (when it has one), in your own
words; never paste passages from it.

## Rules

- Say how, not only which: each row names the participant or seam (class, interface, port, module
  boundary) that realises the principle, using the roles of the example spec, not
  language-specific names.
- The tension is mandatory, even for a pattern that looks harmless.
- Attributions stay out unless sourced. Any statement of who coined or taught a principle, and any
  quote, needs a citation to a primary source (the originator's own publication) or is left out.
  Never attribute from memory.
- Article table and post line are copied from this page, so update the page first.
- The page is a normal doc: relative links and diagrams are covered by `scripts/check_docs.py`.

## Skeleton

```markdown
# Design principles behind <pattern>

<One paragraph: which principles the pattern serves most.>

## Principles the pattern realises

| Principle | How (participant or seam) | Where it can be violated |
| --- | --- | --- |
| <principle> | <participant or seam> | <misuse> |

## Principles that do not apply

- <principle>: <one-line reason>

## Tension and when not to use it

<Principle at risk, misuse example, rule of thumb.>

## Architecture-level correlation

| Architecture application | Principle realised | Seam |
| --- | --- | --- |
| <application> | <principle> | <seam> |

## Sources

<Only if the page attributes or quotes: primary-source citations.>
```
