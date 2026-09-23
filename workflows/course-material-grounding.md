---
description: Ground a task in the local USP MBA course corpus (class material, slides, notebooks) before applying generic best practices
---

# Course Material Grounding Workflow

Use this workflow when a task should be grounded in the USP MBA class corpus under `<path-to-course-materials>`, not just in generic best practices.

## Steps

1. Classify the request:
   - class summary or study support
   - thesis method selection
   - repository implementation guidance
   - governance, writing, or presentation support
2. Read `usp-mba-course-map` reference first and identify the closest course anchors.
3. If the request falls outside the curated map or spans several modules, inspect `usp-mba-course-inventory` reference to locate the missing course folder and representative assets.
4. Separate generic guidance from class-specific guidance:
   - reusable Data Science guidance should come from shared `dev-tools` skills, rules, and workflows
   - course-specific framing, terminology, and method bias should come from local `docs/llm/`
5. For thesis or deliverable work, also review:
   - `usp-mba-course-context` skill
   - `tcc-deliverables` skill
   - `tcc-method-selection.md`
   - `tcc-analysis-and-writing-sync.md`
6. Name the exact class modules that support the recommendation, and call out any meaningful gap between the class material and the proposed approach.

## Exit Criteria

- The answer identifies which course modules are relevant.
- Generic guidance and class-specific guidance are clearly separated.
- The recommendation is consistent with both the repository context and the available course material.
