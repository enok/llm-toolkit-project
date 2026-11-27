---
name: current-events-briefing
description: Brief the user on a live or just-finished public event (debate, hearing, election night, court ruling, earnings call, major incident) - what happened, how independent analysts read it, what fact-checkers found, what new polls or data say - with symmetric coverage and an honest "no consolidated verdict yet" when that is the truth. Use whenever the user asks "what is the analysis of X right now", "who won the debate", "who did better", "who lied more", "fact-check what they said", "any new polls", "what happened at the hearing/ruling/call", or "send me the analysis when it is out", even for casual or dictated questions that never say "briefing".
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.1.0"
---

# Current events briefing

Answers questions about an event that is happening now or just ended. The facts
post-date any model's training, the verdicts arrive in stages, and partisan
sources publish first, so the job is to report the event at the maturity it
has actually reached, evenly for every side.

Source tiers, fact-checker selection, and the poll-reading checklist live in
`references/source-tiers-and-polls.md`. Load it at step 3 of the flow.

## Principles

These hold on every turn; each has a reason, so apply the intent in cases not listed.

- **Search before answering**, every time, however familiar the topic feels:
  the facts post-date training data. Pin the current date and time with the session's clock tool first.
- **Symmetry.** Same search effort, same source tiers, same tone and length for
  each side. Differences in the answer come only from differences in the facts.
  When a question is about a political contest, run separate searches per side
  so one query's bias does not decide the coverage.
- **Give no verdict of your own on contested political questions**; an
  assistant that picks a winner loses the trust of half its readers. Report what
  independent analysts and fact-checkers concluded, attributed to them. State
  settled facts plainly.
- **Partisan outlets are evidence of what a camp claims, never a verdict.**
  Name them as partisan when you mention them at all, applying the same test
  (party channel, campaign site, openly aligned editorial line) to every side.
- **Paraphrase.** Short attributed quotes only where exact wording matters.

## Flow

1. **Pin the event.** What, when (date, time, timezone), live or finished, and
   how long ago. A debate that ended twenty minutes ago and one that ended
   yesterday need different answers.
2. **Classify maturity** with the verdict-lag ladder before writing anything:

   | Time since the event | What exists | What to say |
   | --- | --- | --- |
   | Live / under ~1 h | Live blogs, quotes, checks "in progress" | What was said and the main clashes each side scored with; no consolidated verdict yet |
   | A few hours | First fact-check roundups, first analyst columns | Attributed early reads; flag that they are early |
   | Next day | Consolidated analysis, viewer snap polls where they exist | Consensus or split among independent analysts; snap polls with method caveats |
   | 2-7 days | Opinion polls with fieldwork after the event | Whether vote intention moved, same pollster vs its previous wave |

   See `learnings/live-event-verdicts-lag-the-event.md` for why this step
   exists.
3. **Search in tiers** (reference file): wire services and major outlets for
   what happened; independent fact-checkers for claims; registered polls for
   numbers; analysts across the spectrum for "who did better".
4. **Answer by question type.**
   - *"Who won / who did better?"* Report independent-analyst consensus if it
     exists, the split if it is split, or "no verdict yet" plus the main
     clashes for each side. Never fill the gap with a partisan headline.
   - *"Who lied more?"* Fact-checkers rate claims, not intent, so answer it as
     "who made more false or misleading claims, per published ratings". Use
     only published tallies by independent fact-checkers: count per side by
     rating category, cite each checker, and add that counts depend on claim
     selection and speaking time. Never build your own tally from news
     fragments; it will be partial and asymmetric.
   - *"Fact-check what they said."* Without a transcript or recording, do not
     run a partial check of whatever claims happened to appear in coverage.
     Offer two paths: the user names a specific claim and you check it against
     primary sources, or you wait for the fact-checkers' full roundup and
     summarize it for both sides. With a transcript, select claims by a
     symmetric rule (for example every checkable numeric claim from each side)
     and check each against primary sources.
   - *"Any new polls?"* Pollster, fieldwork dates, sample, margin of error,
     registration where the law requires it, total vs valid votes; compare only
     against the same pollster's previous wave (reference checklist).
5. **"Send it to me when it is out."** This is a deferred follow-up, not a
   limitation. Apply `learnings/deferred-follow-up-declared-impossible.md`, then the
   "Deferred follow-ups" section of `workflows/automation-maintenance.md`: time
   the run after the publication window from step 2 and carry every scope the
   user asked for (analysis, fact-checks, polls) into the run.
6. **Format.** Match the user's language and register. Casual or dictated
   questions get one or two short paragraphs and at most one offer; end with a
   "Sources:" list when the answer drew on links.

## Output template

```
<Maturity line: event, when it ended, how long ago, what exists so far>
<Side A: what was said / scored, attributed>
<Side B: same length and tone>
<Analyst, fact-check, or poll read: consensus, split, or "no verdict yet">
<One offer at most, e.g. a follow-up when fact-check roundups publish>
Sources: <links>
```

Example (question: "who won the debate?", asked 30 minutes after it ended):
"The debate ended about half an hour ago, so independent analysis has not
appeared yet; only live blogs exist. Candidate A pressed on prices and
Candidate B on security, with clashes over ... (attributed). No consolidated
verdict yet. Want me to send the fact-check roundup and first analyst reads
tomorrow morning?" followed by Sources.

## Done when

- Every claim about the event traces to a retrieved source from this turn.
- Both sides received the same treatment (searches, tiers, length).
- The answer states the maturity reached and what is still pending.
- Any follow-up the user asked for is scheduled with a tool-confirmed ID and
  time, or the user was told plainly what could not be scheduled and why.

## Known pitfalls

- A source that refuses automated fetches (robots rules): go to another primary document, never retry the refused page
  through another tool. See `learnings/webfetch-robots-disallowed-marketplace-pages.md`.
- A primary source that is blocked: cross-check independent pages and label provenance in the answer. See
  `learnings/blocked-primary-source-cross-check-and-label-provenance.md`.
