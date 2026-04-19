# Jupyter Notebook Project Context (Template)

> **This is a template.** Copy it and fill in the notebook-specific details for your project.

## Notebook Scope

- **Notebook folders:** [where notebooks live]
- **Primary use:** [EDA, reporting, experiments, tutorials, operational checks]
- **Expected audience:** [engineers, analysts, stakeholders, researchers]

## Data Access

- **Preferred loader modules:** [shared code paths or helper classes]
- **Data locations:** [S3, warehouse, local cache, feature store]
- **Environment setup:** [kernel name, Python version, auth profile, secrets source]
- **Large artifact policy:** [what should not be committed]

## Working Conventions

- Restart and run all before considering a notebook done.
- Keep reusable logic in code, not duplicated across cells.
- Keep markdown explanations close to the analysis they describe.
- Make filtering, sampling, and exclusions explicit.
- Use MathJax-compatible LaTeX when the project includes equations.
- Note how localized notebook text is kept in sync if the project is multilingual.

## Promotion Boundary

- **Promote to code when:** [logic becomes reusable, scheduled, or testable]
- **Testing or validation approach:** [unit tests, smoke checks, data validation]
- **Notebook review checklist:** [output hygiene, metadata, execution order, narrative quality]
