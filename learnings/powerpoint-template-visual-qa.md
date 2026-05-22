---
title: PowerPoint template decks need rendered visual QA
category: toolchain
created: 2026-05-22
tags: [powerpoint, pptx, template, visual-qa, pdf-export, presentation, mba-usp-esalq]
---

# Problem

A formal defense deck was generated from an official PowerPoint template and
looked structurally correct in the script, but rendered slides exposed issues
that would be penalized: missing or hidden template logos, cover typography
drift, text overflow in content cards, wrapped chart labels, and final-slide
content that did not match the expected defense flow.

# Failed Approaches

- Treating the generated PPTX as valid after `python-pptx` saved successfully.
- Checking only extracted text instead of the rendered slide images.
- Rebuilding template slides too freely, which risked changing official cover
  typography and brand chrome.
- Using a single final "thank you/questions" slide when the defense needed a
  cleaner sequence: conclusion, acknowledgements, questions.
- Leaving chart labels as embedded image text when PowerPoint rendering made
  some labels wrap or clip.

# Solution

Use the official template as the source of truth, preserve its logo and visual
system, and validate the final deck by rendering it before delivery:

1. Generate a versioned PPTX instead of overwriting a file that may be open in
   PowerPoint, for example `*_final_v8.pptx`.
2. Export the PPTX to PDF and to full-slide JPG/PNG images using PowerPoint COM
   automation or an equivalent renderer.
3. Create a contact sheet and inspect high-risk slides at full size.
4. Search extracted PPTX/PDF text for removed phrases and template placeholders.
5. Keep only the canonical submitted version in the working folder and archive
   intermediate renders/decks.

For the final submitted deck, the stable pattern was 17 slides: cover; roadmap;
technical story; a dedicated conclusion slide; a clean acknowledgements slide
without names; and a final questions slide with a strong visual cue.

# Why

PowerPoint layout correctness is a render-time property. Text boxes, template
artwork, fonts, footer positions, and image labels can look acceptable in code
or XML but fail when PowerPoint renders the slide or exports the PDF. A deck
that must follow an official template needs template-fidelity checks and visual
QA, not just file generation and text extraction.
