---
description: Prepare a candidate fast for a screening interview or short technical test - map must-haves to CV evidence with honest gap labels, write CV-grounded answers, verify study videos, add rapid-fire concepts and coding warm-ups, and deliver one keepable cheat sheet
---

# Screening Interview Quick Prep Workflow

Use this when the user says "help me prepare for this interview/test
quickly", "what should I study before tomorrow", or "find me videos to
study". The output is one short document the candidate can read in the last
hour. It is built from the posting, the interview format, and the candidate's
own CV, never from invented experience.

Every claim in the answers must trace to a source the user provided. Nothing
here sends anything; sharing the sheet or replying to the recruiter stays
behind `rules/human-comment-reply-gate.md` and
`rules/external-write-authorization.md`.

---

## Phase 0 - Collect inputs

1. **Job description**: copy the must-haves and nice-to-haves verbatim. If
   only a link exists, read the posting page text; if it is unreachable, ask
   the user to paste it.
2. **Interview format**: duration, split (for example discussion vs coding),
   language of the interview, who interviews (human, recorded, AI-assisted),
   and the proctoring rules (camera, microphone, screen share, full screen,
   tab-switch flags, required app).
3. **CV or master profile**: the latest version, plus any list of projects
   the user says is accurate. This is the only source of experience claims.
4. **Time available**: hours or minutes. Scale the output to it: under 2
   hours means the intro, top 3 must-haves, 3 videos, and warm-ups only.
5. **Target language** for the coding part, if stated; otherwise ask once and
   default to the CV's strongest language.

If an input is missing, list it as an open question; do not guess it.

## Phase 1 - Map must-haves to CV evidence

Build a table with one row per must-have (and the top nice-to-haves):

| Must-have | CV evidence (role, project, quote) | Label | Prep action |
| --- | --- | --- | --- |

Use exactly one honest label per row:

- **have in production**: shipped and run for real users or a real business;
- **used in dev-test**: built or run in a lab, side project, course, or test
  environment;
- **concept only**: studied, understood, not built;
- **none**: no evidence in the CV.

Rules:

1. Quote or point to the CV line behind every label above `none`. A label is
   downgraded, never upgraded, when the evidence is ambiguous.
2. Rows labelled `concept only` or `none` are the gaps. Each gets a bridge
   (Phase 2) and a video or reading item (Phase 3).
3. Rank rows by how heavily the posting weights them (title, first bullets,
   repeated words) so the sheet leads with what will be asked.

## Phase 2 - Write the answers

1. **60-second intro**: who the candidate is, the two or three CV facts most
   relevant to this posting, one concrete result, why this role. About 150
   spoken words.
2. **Per must-have answers**, in this order: the likely question, a 3-5
   sentence answer grounded in the CV, and one follow-up with its answer. Use
   the situation, action, result shape and keep it conversational.
3. **Numbers**: use a number only if a source contains it. Otherwise write a
   `<real>` placeholder (for example `<real: requests per second>`) and list
   all placeholders at the top of the document for the candidate to fill from
   memory. Never estimate a figure for them.
4. **Bridge pattern for gaps**: "What I did" (the nearest real experience) +
   "how I would do it on X" (a correct, concrete approach) + "what I would
   check first". Example: "I have not run it in production; in a test
   environment I did A, and in production I would start with B and measure C."
5. **Phrases to say**: short reusable lines such as "let me restate the
   problem", "my first approach is brute force, then I will optimize", "I have
   not used that in production; here is how I would approach it".
6. **Hard limits**: never claim production experience, certifications,
   employers, team sizes, frameworks, or metrics that the CV and user-provided
   sources do not support. When unsure, leave it out and ask.

## Phase 3 - Find and verify study videos

1. Search for short, focused videos (ideally under 20 minutes) per gap row,
   plus one on the interview format if relevant. Prefer official or
   well-established channels. Pick 3-4 core videos and mark any extras
   `optional`.
2. **Verify every URL before it enters the document.** Fetch the oEmbed
   endpoint:
   `https://www.youtube.com/oembed?url=<watch-url>&format=json`
   If it fails, fall back to
   `https://noembed.com/embed?url=<watch-url>`.
   A URL that returns no JSON is dropped. Never publish a link from memory or
   search-snippet text alone.
3. Record **title** and **channel** from the oEmbed response; do not retype
   them from the search results.
4. **Durations**: read them from the watch page only if it loads. If the page
   is rate-limited (HTTP 429) or blocked, write "duration unverified" and do
   not guess. Do not retry in a tight loop.
5. For each video give one line: which gap it covers and what to watch for
   ("watch the first 10 minutes on request flow").

## Phase 4 - Rapid-fire concepts and coding warm-ups

1. **Rapid-fire concepts**: 8-12 terms taken from the must-haves and the gap
   rows. Format: term, one-sentence definition, one trade-off or when not to
   use it. Examples of the shape: "API gateway - single entry point for
   routing, auth, and rate limiting; adds a hop and a failure point".
2. **Three coding warm-ups** in the target language, short enough to do in
   10 minutes each, each with its complexity:
   - a hash-map problem (for example finding a pair with a target sum), time
     O(n), space O(n);
   - a stack or two-pointer problem (for example balanced brackets or a
     palindrome check), time O(n), space O(n) or O(1);
   - a sliding-window or sorting problem (for example the longest substring
     without repeats, or merging intervals), time O(n) or O(n log n).

   Give the prompt, the brute-force idea, the optimized idea, and the
   complexity for each. The candidate writes the code; include a reference
   solution only if asked.
3. **Coding routine for AI-assisted or proctored rounds**: restate the
   problem and the constraints; state a brute-force solution and its cost;
   optimize and say why; code it in small steps while narrating; test with a
   normal case, an empty or minimal input, a duplicate or boundary case, and a
   large-input thought; state final time and space complexity. If stuck, say
   what you are considering instead of going silent.

## Phase 5 - Proctoring and setup checklist

Include only the lines that match the stated format:

1. Test camera, microphone, screen share, and network at least 30 minutes
   before; plug in power; close notification sources.
2. Close other monitors, AI assistants, desktop agents, remote-control tools,
   transcription tools, and automating browser extensions if the rules
   forbid them. Read the rules again for the exact list.
3. Stay in full screen and in one browser window if tab switches are flagged;
   keep notes on paper, not in another window, unless the rules allow notes.
4. If a required app must be installed, run
   `workflows/third-party-installer-vetting.md` first. Do not open a one-time
   interview link as a test; it may start or consume the attempt.
5. If the setup is unacceptable (unsupported operating system, virtual
   machine, privacy concern), ask the recruiter for an alternative format
   before the session. Do not work around a restriction silently.
6. **Pause any conversation monitoring that opens browser tabs** during the
   session (`workflows/conversation-monitoring.md`, Phase 4) and resume only
   when the user asks.
7. Afterwards, check that any temporary app uninstalled itself.

## Phase 6 - Fact-check (mandatory)

When subagents or earlier drafts wrote any answers, the root agent verifies
them before delivery:

1. Extract every factual claim: employers, titles, dates, frameworks, tools,
   practices, team sizes, scale numbers, certifications.
2. For each claim, search the CV or master profile text (`grep` for the term
   and its synonyms) and record the supporting line.
3. Remove or rewrite every claim with no supporting line, including a wrong
   employer, a stack the candidate never used, and a practice that sounds
   plausible. Replace it with the bridge pattern or a `<real>` placeholder.
4. Report the removals to the user in one short list ("removed: X, no CV
   evidence"). Do not defend an unsupported claim.

Optionally run `workflows/task-quality-loop.md` on the answers with this phase
as the validator.

## Phase 7 - Deliver one keepable document

1. Length: at most about 2 printed pages. Order: placeholders to fill, intro,
   evidence table, answers by priority, rapid-fire list, three warm-ups plus
   the coding routine, verified videos, proctoring checklist, do/don't list.
2. Format: a single file in the format the user prefers; if none, Markdown.
   Keep it in the user's working folder, not in the toolkit. Do not store
   candidate data in `rules/`, `workflows/`, or `learnings/`.
3. End with a **do/don't** list. Do: restate the question, answer in 60-90
   seconds, name gaps honestly and bridge them, ask a clarifying question
   before coding, narrate. Don't: invent numbers, claim certifications or
   production use you lack, read answers aloud from a script, speak badly of
   past employers, or rush into code.
4. Final reply: the file path, the open `<real>` placeholders, the claims
   removed in Phase 6, and the videos whose duration is unverified.
