---
trigger: always_on
description: LaTeX inside notebooks and technical docs - readable math, renderer compatibility, and maintainable notation
---

# LaTeX In Notebooks

Math-heavy notebooks and technical reports should express equations as editable, reviewable source rather than opaque screenshots or ad hoc notation.

## Notation Discipline

- Define symbols close to the equation that uses them.
- Keep notation consistent with code, dataset column names, and chart labels where practical.
- Prefer a small, stable notation set over clever shorthand that only the author understands.

## Renderer Compatibility

- Use MathJax-friendly LaTeX that renders in Jupyter markdown and common HTML exports.
- Avoid custom macros unless the project documents them and the target renderer supports them.
- Test long equations and aligned environments in the notebook itself, not only in your head.

## Reviewability

- Prefer markdown plus LaTeX over screenshots of formulas.
- Break complex derivations into smaller steps with short prose between them.
- Explain what an equation is doing and why it matters; do not leave raw math without interpretation.

## Export Safety

- If the notebook or doc will be exported to HTML, PDF, or slides, verify the equations render in the intended target.
- When exact notation matters to implementation, keep the equation and the code path easy to cross-reference.
