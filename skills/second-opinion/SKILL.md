---
name: second-opinion
description: "Get a pragmatic second opinion on plans, designs, or code by running it through a secondary AI model alongside the primary model's own review. Use when the user wants a sanity check, peer review, consensus check, or second set of eyes on any artifact before implementation. Trigger on 'review this plan', 'does this design make sense', 'sanity check', 'gut check', 'what am I missing', 'second opinion', or 'run this by another model'."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Second Opinion

Get a side-by-side sanity check from two different AI perspectives before committing to an approach. The primary model reviews the artifact, then a secondary model reviews the same artifact independently. You see both perspectives together.

## Why this exists

Every model has blind spots. The value isn't in either individual review — it's in the **delta** between them. When both flag the same thing, it's almost certainly real. When they disagree, that's where your judgment matters most.

The anti-pattern this skill fights: models love to enumerate every conceivable issue, including ones that will never happen in practice. This skill is tuned to suppress that instinct and focus on what actually matters for shipping working software.

## When to use

- Before implementing a plan — "does this approach make sense?"
- Before committing a design — "am I missing anything structural?"
- Before a PR — "quick sanity check on this code"
- When you're unsure about a tradeoff — "is this the right call?"

## Flow

### Step 1: Identify the artifact

Figure out what's being reviewed. It's one of:

| Type | How to identify | What to pass |
|------|----------------|--------------|
| **Plan** | `.md` file with tasks, steps, architecture | The file path |
| **Design doc** | Architecture doc, API spec, data model | The file path |
| **Code files** | Source files, a diff, or a directory | File paths or directory |
| **Inline content** | User pasted something in the conversation | Write to a temp file first |

If the user says "review this" without specifying, check what they've been working on — the most recently discussed or edited files are probably it.

### Step 2: Primary review (do this yourself, inline)

Before calling the secondary model, write your own brief review. This keeps your perspective independent — you haven't seen the other take yet.

**Review frame — apply this to your own review too:**

Focus on these five dimensions only. Skip any that don't apply to this artifact type:

1. **Correctness** — Will this actually work? Are there logic errors, wrong assumptions, or misunderstandings of the domain?
2. **Gaps** — What's missing that would cause a real problem? Not theoretical gaps — things that would actually bite someone during implementation.
3. **Sequencing** — Are dependencies in the right order? Will anything block something else?
4. **Simplicity** — Is there unnecessary complexity? Could something be simpler without losing capability?
5. **Risk** — What's the one thing most likely to go wrong? Not the scariest thing — the most *probable* thing.

**Calibration rules:**
- If you can't explain why something matters in one sentence tied to a concrete outcome, don't mention it
- "Someone might want to..." is not a real issue. "This will fail when..." is.
- Three important findings beat ten minor ones
- If everything looks solid, say so. "No major concerns" is a valid review.

### Step 3: Get second perspective

Use whatever secondary model or tool is available in the environment (Codex CLI, another agent, etc.). If no secondary model is available, note this and present only the primary review.

**The review prompt for the secondary model:**

```
You are doing a pragmatic sanity check on [artifact type] before implementation begins.

Review: [file path(s) or directory]

Focus only on what applies:
1. CORRECTNESS — Will this work? Logic errors, wrong assumptions, domain misunderstandings.
2. GAPS — What's missing that would cause a REAL problem during implementation? Not theoretical.
3. SEQUENCING — Dependencies in wrong order? Anything that blocks something else?
4. SIMPLICITY — Unnecessary complexity that could be cut?
5. RISK — The single most PROBABLE thing to go wrong. Not scariest — most likely.

Rules:
- 3-7 findings maximum. If everything looks solid, say so.
- Each finding must tie to a concrete outcome in one sentence.
- Do NOT suggest adding error handling, logging, tests, or docs unless their absence would cause a specific failure.
- Do NOT flag style issues, naming preferences, or "best practices" that don't affect correctness.
```

### Step 4: Present side-by-side

Once you have both reviews, present them together. Don't editorialize or merge — let the user see the raw perspectives.

```
## Second Opinion: [artifact name]

### Primary Review
**Verdict:** [Looks solid / Minor concerns / Needs revision]
[findings]

### Secondary Review
**Verdict:** [...]
[findings]

### Where we agree
[List items both flagged — these are high-confidence signals]

### Where we diverge
[List items only one flagged, with brief context on why the difference might exist]

### Bottom line
[One sentence: is this ready to implement, or does something need attention first?]
```

The "where we agree" and "where we diverge" sections are the real value. Agreement = high confidence. Divergence = worth the user's attention but not necessarily a blocker.

## Edge cases

- **No secondary model available:** Present the primary review alone with a note.
- **User wants just one perspective:** Skip the dual review, present the single result.
- **Large artifact (>500 lines):** Focus on specific files or sections rather than the entire codebase.

## What this skill does NOT do

- It doesn't modify any files
- It doesn't make decisions — it presents perspectives for the human to judge
- It doesn't chase down every concern — it's calibrated for pragmatism
- It doesn't replace thorough code review — it's a quick sanity check

## Related Skills

- **ticket-review** (or **review**) — in-agent AI diff review
- **pre-pr-check** — full pre-PR validation
- **pathfinder** — decompose plans into slices before review
