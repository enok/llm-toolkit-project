---
title: Medium's Change topics popover adds only the first suggestion, on Enter
category: toolchain
created: 2026-10-08
tags: [medium, topics, change-topics, typeahead, edit-published-story, normalisation, browser-automation]
---

# Problem

Changing the topics of an already published Medium story. The story editor's "..." menu
has "Change topics", a popover with the current topic chips (each with a remove control),
an "Add a topic..." field and Save / Cancel. Two chips were removed and new topics added.
While inserting new text into the same story, read-back comparisons against the approved
text also failed.

# Failed Approaches

1. Typing the topic and clicking the matching suggestion with the mouse: no chip was added
   and the field kept the typed text.
2. A dispatched mousedown followed by a click on the suggestion's list item: no chip was
   added either. This differs from the publish dialog, where a DOM click had worked
   (`learnings/medium-topic-autocomplete-swaps-typed-topic.md`).
3. Comparing the inserted paragraph and a heading with the approved text byte for byte:
   the editor held curly quotes where the paste had straight ones, and a heading held
   no-break spaces, so the match failed although the text was right.

# Solution

- Remove the chips to replace with their remove control (that worked).
- Type the topic until the exact topic is the first suggestion; read the suggestion list
  before pressing anything (each suggestion shows a number).
- Press Enter: it adds the first suggestion. Read the chips back.
- When the intended name is not offered as such (typing "SOLID" offered Solidity, Solid,
  Solid Principles, Solidarity, Solidão; "Solid" is a different topic), ask the user before
  adding a substitute unless the approved draft already names it. With approval, extend the
  text until the substitute is first (typing " Principles" after "SOLID" made "Solid
  Principles" first), then press Enter.
- Click the popover's Save (it closed the popover); then "Save and publish" published and
  the live page showed the new topics. Whether Save alone publishes the topics was not
  checked (inference: they go out with the publish).
- Normalise before comparing text. The mapping to apply: curly double quotes (U+201C,
  U+201D) to `"`, curly single quotes (U+2018, U+2019) to `'`, no-break space (U+00A0) to a
  space.

Durable guidance: skills/medium-publishing/references/publish-dialog.md (section 7) and
skills/medium-publishing/references/editor-verification.md (section 4).

# Why

Observed: the pasted paragraph's straight quotes became curly quotes in the editor, and a
heading's text held no-break spaces; why was not investigated (inference: editor typography
on paste). Why the popover ignores clicks was not investigated either.
