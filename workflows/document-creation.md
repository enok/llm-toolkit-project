---
description: Create or update architecture docs, diagrams, and Confluence pages
---

# Documentation Creation Workflow

Create or update architecture documentation — diagrams, README files, and external docs (e.g., Confluence).

---

## Before Starting

1. **Read existing documentation** in the target `docs/` folder (diagrams, READMEs).
2. **Read source code** to verify service names, technology stacks, and data flows.
3. **Check external docs** (Confluence, wiki) for existing pages that may need updating.
4. **Check Jira** for related tickets if the documentation is tied to a feature.

---

## Principles

1. **Source of truth**: Diagram source files (PlantUML `.puml`, Mermaid `.md`) are the source of truth. Images (SVG, PDF, PNG) are generated artifacts.
2. **Evidence-based labels**: Use names proven by code, config, infrastructure, or existing docs. Do not invent components.
3. **Technology accuracy**: Verify stack labels against actual source and build files.
4. **Consistency**: All diagrams in a folder should share the same notation and export path.
5. **Right-sized completeness**: Cover the scope being documented; split diagrams when a single view becomes dense.
6. **Deterministic diagram system**: Apply `skills/diagram-authoring/references/deterministic-diagram-system.md` before drafting or validating C4, AWS, sequence, or flow diagrams.
7. **Mandatory 100% image inspection**: Every generated/exported image artifact must pass `skills/image-quality-inspection/references/image-quality-gate.md`; fix and re-render until acceptable. If an image cannot be inspected after export, the documentation task is blocked.
8. **Mandatory documentation review**: Documentation created or changed by any
   agent, chat, automation, script, or human must pass
   `documentation-reviewer` before completion.

---

## Diagram Types

Architecture documentation must use the standard view set from `skills/diagram-authoring/references/diagram-type-standards.md`:

| View | Required type | Shows | Must not replace |
|------|---------------|-------|------------------|
| **Components** | C4 component diagram | Software components, ownership, boundaries, dependencies | AWS topology or runtime ordering |
| **Architecture** | AWS architecture diagram | Cloud resources, networking, deployment/runtime boundaries, storage, messaging, observability | Application internals, code/package details, or numbered runtime steps |
| **Details** | Sequence diagram | Request/message lifecycle, retries, branches, failures, callbacks | Static structure or cloud topology |

Create or update all three views when documenting a system or feature that has component, infrastructure, and runtime detail. If a view is not applicable, state why in the surrounding doc. Use unified flowcharts only as optional summaries after the standard views exist.

Put overview diagrams in `docs/architecture.md` or the destination repo's documented architecture path. Put flow-specific detail diagrams under `docs/flows/`.

---

## Mermaid Diagram Standards

Use **Mermaid diagrams** in Markdown for sequence/detail or simple non-architecture diagrams unless the destination repo already standardizes on PlantUML or another diagram format. For C4 component and AWS architecture diagrams, prefer PlantUML when the renderer is available so notation, icons, legends, and layout remain standardized.

For detailed authoring rules, use `skills/diagram-authoring/SKILL.md`,
`skills/diagram-authoring/references/deterministic-diagram-system.md`, and
`skills/project-discovery/references/diagram-conventions.md`.

---

## PlantUML Standards (if project uses PlantUML)

- **AWS Icons**: Use `aws-icons-for-plantuml` with a pinned release tag (for example, `!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v23.0/dist`). If maintaining an existing diagram set, keep its current pinned release unless intentionally upgrading all related diagrams.
- **C4 Components**: Use C4-PlantUML component notation for software component views when PlantUML is available.
- **Theme**: Use the deterministic sequence template/defaults unless the destination repo has a checked-in PlantUML theme. Custom skinparams for component diagrams must match the deterministic palette or repo standard.
- **AWS style**: For AWS-heavy diagrams, follow `skills/diagram-authoring/references/aws-plantuml-style.md` and `skills/diagram-authoring/references/aws-architecture-quality-control.md`.
- **Participant aliases**: Must match exactly between declaration and usage — mismatched aliases create ghost participants.
- **Width control**: Keep `nodesep` ≤ 80 for sequence diagrams with many participants. Use `-DPLANTUML_LIMIT_SIZE=32768` when exporting wide or detailed diagrams.
- **Naming**: Files use `PascalCase_With_Underscores` matching diagram content.
- **Numbered arrows**: Use numbered labels only in sequence/detail views when they clarify execution order. Do not use numbered arrows in AWS architecture diagrams; use verb-labeled topology relations and put ordering in a sequence diagram.
- **Compile gate**: Always compile changed `*.puml` files with PlantUML before considering the documentation change complete.
- **Image export**: Always re-export images after any source file change when the destination repo versions generated images. Prefer SVG/PDF; when PNG/JPG is required, render from source at high resolution and verify dimensions.
- **Rendered review**: Open every exported PNG/SVG/PDF and visually inspect readability, spacing, grouping, labels, and arrow direction; improve and re-export if the rendered result is unclear. This post-export quality-control step is mandatory.
- **Image QA**: Apply `skills/image-quality-inspection/references/image-quality-gate.md` to generated diagram images, screenshots, PDF page renders, wiki attachments, and document/slide renders before completion. Uninspected exported output is a blocker.

---

## README Standards

### Root `README.md` — minimum sections:
- Title, one-line description, links to external docs (Confluence, Jira).
- **Overview**: What the service does.
- **Architecture**: Link to diagrams in `docs/`.
- **Project Structure**: File tree with descriptions.
- **Data Flow**: Text or diagram showing the request/data pipeline.
- **Deployment**: CI/CD pipeline, environments.
- **Related**: Links to related services, Confluence pages.

### `docs/` folder `README.md` — additional sections:
- **System Components** table: service, repo, production name, stack, role.
- **AWS Resources** table: resource type, production name, publisher/consumer.
- **Key Design Decisions** table: decision → rationale.
- **Generating Diagrams**: Commands to export from source files, including high-resolution/vector export flags.

---

## External Documentation (Confluence)

- After updating README or diagrams, update the corresponding Confluence page.
- Use Confluence MCP tools or manual update.
- Keep Confluence in sync with repo documentation — repo is source of truth for code-level docs.

---

## Common Mistakes

- **Wrong technology labels** — always verify against actual source code.
- **Generic service names** — use actual production hostnames/resource names.
- **Missing components** — every participant referenced must be declared.
- **Uncompiled PlantUML** — always run PlantUML against changed `*.puml` files; do not rely on visual inspection alone.
- **Stale diagrams** — re-export images after every source change.
- **Unchecked rendered output** — compilation can pass while the image is cramped or misleading; always inspect every exported/generated image.
- **Sampled image review** — checking only one page, one slide, or one diagram is not enough when multiple images were generated/exported.
- **Optional image QA** — post-export quality control is mandatory; if the image cannot be inspected, report a blocker.
- **Low-resolution exports** — prefer vector output and verify dimensions for required raster images.
- **Forgetting render flags** — wide PlantUML diagrams need `-DPLANTUML_LIMIT_SIZE=32768`.

---

## Final Step — Self-improvement

Run `documentation-reviewer` against the final docs and generated/exported
artifacts before closeout.

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
