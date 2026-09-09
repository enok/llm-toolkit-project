---
title: Figma comparison checklist
tags: [figma-compare, design-qa]
---

# Figma comparison checklist

Use this when comparing a browser implementation to a Figma frame.

## Before comparing

- [ ] Same **breakpoint** width as the Figma frame
- [ ] Same **theme** (light or dark)
- [ ] Same **data state** (empty, loading, error, filled; match the mockup variant)
- [ ] Same **route** or modal open as the frame depicts
- [ ] Fonts loaded (no flash of unstyled text changing layout mid-screenshot)

## Structure

- [ ] All major regions present (header, sidebar, main, footer as applicable)
- [ ] Region order matches
- [ ] Heading levels roughly match the hierarchy

## Content

- [ ] Primary headings and body copy match (or match ticket-approved copy)
- [ ] Button and link labels match
- [ ] Empty and error messages match the specified copy
- [ ] Icons present where the design shows icons (the symbol need not be identical if it comes from the design system)

## Layout

- [ ] Horizontal alignment (left, center, right) matches intent
- [ ] Vertical spacing between sections within roughly 8px of spec, or visually equivalent
- [ ] Grid or column count matches at this breakpoint
- [ ] No unintended overflow or clipping

## Components

- [ ] Correct variant (primary versus secondary button, input state)
- [ ] Form fields: label position, helper text, validation state if mocked
- [ ] Lists and tables: column headers, row density

## Visual tokens

- [ ] Background and surface colors match tokens (not raw hex unless there are no tokens)
- [ ] Text color and emphasis (muted versus primary)
- [ ] Border radius and dividers
- [ ] Elevation and shadows on cards and modals

## Out of scope (unless the ticket says otherwise)

- Exact pixel parity on retina versus 1x export
- Placeholder image content versus stock photo crop
- Animation and motion (note it as untested; motion QA is out of scope for this skill)

## Severity guide

Document each mismatch as **critical**, **major**, or **minor** so the user can triage quickly.
