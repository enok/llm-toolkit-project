---
title: Tags and topics for a study repo, article and post
tags: [study-repo, tags, topics, hashtags, github-topics, medium-topics, linkedin, ledger]
---

# Tags and topics

Standing requirement: the tags of every study repo, article and post represent all the
important topics of the content: the main topic, the principle and architecture acronyms, the
architecture concepts, the language, the named frameworks. Generic for any pattern or topic.

## 1. Derive one tag list from the finished content

Build the first list from the finished docs (it feeds the repo topics). When the article draft
and the post draft exist, extend it with what they name, and re-check section 4 before each
approval gate; if the list grew after the topics were set, re-set them (a new settings change,
its own approval). Read the content; do not use a fixed list or the title alone. Cover each of
these when the content has it:

| Source in the content | Examples of tags (illustrative) |
| --- | --- |
| Main topic and its family | the pattern, its family (behavioural, creational, structural), "design patterns" |
| Principles and their acronyms | SOLID and the specific letters the principles page maps, DRY, KISS, YAGNI when discussed |
| Architecture styles and concepts the content actually covers | hexagonal architecture / ports and adapters, clean architecture, branch by abstraction, multi-tenancy, backpressure, feature flags |
| Language | each language of the example set |
| Frameworks or products the content names | only those the article or post names, each backed by its cited claim |

Rules: tag only what the content covers (a concept named in passing does not earn a tag); an
acronym and its long form are both candidates; no tag for a framework the content does not name.

## 2. Keep one ledger

Keep the list in one place, the repo-side ledger or the publication notes, as a table, so the
three destinations stay consistent:

| Tag | GitHub topic | Medium topic | LinkedIn hashtag |
| --- | --- | --- | --- |
| `<tag>` | `<lowercase-hyphenated>` | yes / no (the five picked) | `<CamelCase>` or no |

The ledger is the superset. GitHub topics are the at most 20 tags the repo itself backs (its
docs and code, not topics that only the article or post cover); Medium picks its five; LinkedIn
uses the tags the post's text names. Update the ledger first when content changes, then the
destinations.

## 3. Per destination

| Destination | Format and limits | How to set | Approval |
| --- | --- | --- | --- |
| GitHub repository topics | lowercase, hyphen-separated; at most 20 topics, each at most 50 characters (GitHub's limits); only tags the repo backs | the repository topics API once the docs are final (re-set if the ledger grows); read the topics back | a settings change on the user's repo: its own external-write approval (`rules/external-write-authorization.md`) |
| Medium topics | at most 5 per story: the five that best represent the content (main topic, the architecture concept, the principles, the language) | publish dialog: type without Enter, click the exact suggestion, read the chips back (`learnings/medium-topic-autocomplete-swaps-typed-topic.md`, `skills/medium-publishing/references/publish-dialog.md`) | part of the draft the user approves |
| LinkedIn hashtags | CamelCase, no spaces, at the end of the post; one for every important topic the post names, none for what it does not mention; there is no cap on the count, the post's text decides (post order: `skills/medium-publishing/references/content-angle.md`) | part of the post text, hash-verified before Post (`skills/linkedin-publishing/SKILL.md`) | part of the text the user approves |

GitHub topics call (illustrative; not run in the authoring sandbox, which has no GitHub
access). Write the body to a file (on Windows PowerShell 5.1 write it with
`Out-File -Encoding ascii`: a redirect writes UTF-16,
`learnings/powershell-redirect-writes-utf16.md`), replace all topics, read them back:

```bash
printf '{"names": ["<topic-one>", "<topic-two>"]}' > topics.json
gh api -X PUT repos/<owner>/<repo>/topics --input topics.json
gh api repos/<owner>/<repo>/topics
```

If GitHub rejects a name, shorten or re-case it (limits and allowed characters are
GitHub's; check its documentation) and keep the ledger in step.

## 4. Check before the approval gates

- The ledger covers every row of section 1 that the content has.
- GitHub topics: at most 20, each at most 50 characters, lowercase and hyphenated.
- Medium: five topics, chips read back equal the list.
- LinkedIn: every hashtag matches a topic the post text names.
