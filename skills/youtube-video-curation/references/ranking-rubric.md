---
title: YouTube explainer video ranking rubric
tags: [youtube, video, ranking, curation, documentation]
---

# Ranking Rubric

How `scripts/youtube_search.py rank` orders candidate videos, and how to judge
them by hand. The script implements exactly the order below; if either changes,
change both and the tests together.

## Criteria, in priority order

A higher criterion always wins. A lower one only decides among videos that are
equal (or in the same bucket) on everything above it.

1. **Shows code in the requested language.** Script tier from title and snippet:

   | Tier | Meaning |
   | --- | --- |
   | 3 | language named in the title, and a code word (code, example, implementation, tutorial, programming, walkthrough, project, build, hands-on) in the title or snippet |
   | 2 | language named in the title only |
   | 1 | language named only in the description snippet |
   | 0 | language not named |

   Language matching is whole-token (`java` does not match `JavaScript`) and knows
   common aliases (`js`, `ts`, `py`, `c#`, `c++`). The script cannot see the
   video: tier 3 means "likely shows code", which step 4 of the procedure confirms.
2. **Views relative to age.** `views_per_year = views / max(age_years, 0.25)`, with
   age from the "N years/months/weeks/days ago" text (unknown age counts as 1
   year). The score is a half-decade bucket, `floor(2 * log10(views_per_year + 1))`.
   Bucket 11 covers roughly 316k to 1M views per year and bucket 10 roughly 100k to
   316k, so 400k and 600k per year tie (other criteria decide) while 250k falls one
   bucket lower. A recent video with healthy traction can beat an old one with more
   total views. Negative, NaN, or infinite counts are treated as unknown (0).
3. **Channel focus and credibility.** Observable proxy: the number of qualified
   results from the same channel in the pool, capped at 3 (a channel with several
   relevant videos is usually focused on the subject). A channel passed with
   `--prefer-channel` scores 10. Credibility is a human call; prefer channels
   dedicated to the language or to software design over general entertainment.
4. **Length 2 to 30 minutes.** Inside 120 to 1800 seconds scores ok. Shorter is
   rarely a full explanation; longer is a course lecture, not a doc companion.

## Tie-breakers

Applied in order after the four criteria are equal:

1. A normal upload over a recorded live stream (`published` starts with "Streamed").
2. Length closest to 10 minutes.
3. More total views.
4. Lexicographic video ID, so the result is stable across runs and input orders.

## Disqualifiers

Disqualified videos are listed, with reasons, after the ranking and never count
toward `--top`.

| Reason | Detected by |
| --- | --- |
| `short` | `/shorts/` URL, length <= 60 s, or `#shorts` in the title |
| `live` | LIVE badge, upcoming event, or a "watching" count instead of views |
| `playlist` | playlist flag or `/playlist` URL |
| `invalid-id` | ID is not 11 characters of `[A-Za-z0-9_-]` |
| `non-english` | mostly non-Latin title, or an explicit language marker (for example "Hindi", "Espanol"); override with `--allow-non-english` |
| `other-code-language:<name>` | title names a different known language and not the requested one |

`other-code-language` assumes a title that names only another language is not
the code the document needs. A title that names several languages including the
requested one stays eligible.

## Manual check (after the script)

For the top two or three candidates, confirm before choosing:

- The requested language and version appear in code on screen, not only in a slide.
- Audio is in the requested language (English by default).
- The explanation covers the topic, not a neighbouring one with a similar name.
- No disabling issues: age-restricted, members-only, or embedding disabled
  (`verify` exit 1 with HTTP 401).

If the script's top pick fails the manual check, take the next rank and note why.

## Limits

- Title and snippet heuristics miss videos that show code without naming the
  language in either; rank tier 0 can still contain a good video. When fewer
  than three candidates are tier 2 or 3, run a second query.
- View counts and ages come from the results page at pull time; keep the `pulled_at`
  date with the decision.
- The channel proxy cannot see subscriber counts or reputation. Use
  `--prefer-channel` for channels the requester trusts.
