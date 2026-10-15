---
title: The short system-design article for a study topic
tags: [medium, article, system-design, aida, short-form, hero-diagram, trade-offs, positioning, study-repo]
---

# The short system-design article for a study topic

Default shape of the Medium article of a study publication (a design pattern, an algorithm, a
protocol) when the positioning profile ([positioning-profile.md](positioning-profile.md)) or the
toolkit defaults say system-design-first. The article tells one system design story; the study
topic is the mechanism inside it. The repo holds the complete teaching material and is linked,
never repeated. The long "everything the repo holds" order stays available in
[content-angle.md](content-angle.md) for a profile that asks for a full tutorial.

## 1. Shape

AIDA ([aida-narrative.md](aida-narrative.md)) in five blocks. Section names are suggestions;
show the stage map with the draft, not the stage words in the text.

| Block | AIDA | Content | Share of the word budget |
| --- | --- | --- | --- |
| Title, subtitle, first paragraph | Attention | The system design problem or capability at the profile's role level, with one concrete number, failure or requirement. Never the study topic's name. | about 10% |
| The forces | Interest | The system, its requirements and constraints: load, rate of change, team or service boundaries, failure modes, what must stay fixed. A reader new to the topic can name the problem afterwards. | about 20% |
| The design decisions | Desire | Two to four decisions, each as: the decision, the alternative not taken, the cost accepted (the trade-off). The hero diagram sits here. Results come only from the repo or its fact table. | about 45% |
| Where the pattern lives | Desire (proof) | One short section: the study topic named once as the mechanism behind the decisions, mapped to the seam in the hero diagram. Required: ONE sentence naming the main design and architecture principles the design realises, taken from the repo's principles page. Optional: at most two cited framework appearances, one snippet. | about 15% |
| Your next step | Action | One concrete step the reader can take (an experiment, a check on their own system, a question to ask their team), then the repo link, the post link and the curated video link. | about 10% |

The percentages are guidance for staying inside the budget (toolkit default 1,500 words; an example
consumer profile uses 1,300), not limits.

## 2. Title and subtitle

- Name the problem or capability, not the tool: what the system must do under which pressure
  (for example "how a service lets a new market change its rules without a release"), at the level
  of the profile's target roles.
- The study topic's name is absent from title and subtitle. `check_publication.py article ... --title "<title>" --subtitle "<subtitle>" --forbid-title "<topic name>"`
  fails when it is present in either.
- Title at most 100 characters, subtitle at most 140, counted before typing
  ([publish-dialog.md](publish-dialog.md) section 1).
- Every noun in title, subtitle and first paragraph can be pointed to in the body
  (positioning rule in [aida-narrative.md](aida-narrative.md)).

## 3. Diagrams

- Two or three images: one hero system-design diagram, one or two supporting ones (a decision or
  failure path, a sequence at the seam). Components and services, not classes.
- The hero diagram shows the whole system on one canvas, labels the seam where the study topic
  acts, and is readable at feed width: it is also the post image (square or 4:5)
  (`skills/image-quality-inspection/SKILL.md`, `skills/diagram-authoring/SKILL.md`).
- Class-level and generic diagrams stay in the repo.
- Every image URL is pinned to a commit SHA that already holds the file
  ([paste-recipe.md](paste-recipe.md)). When the repo has no system design view yet, add it to the
  repo through the normal pull request first and pin the merged SHA; the article cannot cite a diagram
  that is not on the default branch.

## 4. Code

- At most one snippet, at most 15 lines, or none; the profile sets the numbers.
- The snippet is one contiguous, unchanged range of a repo file, quoted from the repo's default
  branch. Record file and line range, and hash-check the pasted block against that range with the
  normalisation of [editor-verification.md](editor-verification.md) section 3.
- Full listings, tests and the other language folders stay in the repo, linked.

## 5. What stays in the repo

The repo holds the explanation, generic and class-level diagrams, the complete code, the principles
page and the video list. The article links to them in the closing section and may point to one of
them in the body ("the repo shows the class-level view"). Do not paste them back. A piece that
re-teaches the pattern has become a tutorial: either cut it or change the profile.

Framework sightings ("hidden in `<framework>`") are optional in this shape: at most two, each a
fact-table row with an official source checked on the day ([content-angle.md](content-angle.md),
citation rules). Mark readings the source does not state as "my reading".

## 6. Medium constraints

Medium has no tables or inline code ([paste-recipe.md](paste-recipe.md)): write trade-offs as
short paragraphs or `Label: value` list items. Keep the words that count (the body) under the
budget; code blocks, image captions and the title do not count in the script's measure.

## 7. Before the approval gate

- Profile or defaults named in the draft message; `check_publication.py article` exits 0 with the
  profile's budgets (and `--title`, `--subtitle`, `--forbid-title` for the topic's name).
- The one-sentence principles line is present and matches the repo's principles page; the full
  "Principles behind it" section belongs to a full-tutorial profile only.
- Stage map shown with the `NOT POSTED` draft: one line per stage naming the section that carries it.
- Title level, internal placement of the topic and claim support checked by the
  `publication-reviewer` agent (`tool-subagents/publication-reviewer.md`).
- Each design decision has its trade-off; each number or result traces to the repo or fact table.
- The "Your next step" section exists, and the post (a teaser, [content-angle.md](content-angle.md)
  post order) links this article as its one primary call to action.
- Article and post agree on the claim and the links.
