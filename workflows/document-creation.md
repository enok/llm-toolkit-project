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

1. **Source of truth**: Diagram source files (PlantUML `.puml`, Mermaid `.md`) are the source of truth. Images (PNG, SVG) are generated artifacts.
2. **Production names**: Always use real production resource names — not shorthand or generic labels.
3. **Technology accuracy**: Verify stack labels against actual code (e.g., don't say "Spring Boot" if it's "Spring MVC").
4. **Consistency**: All diagrams in a folder should share the same theme, skinparams, and icon library version.
5. **Completeness**: Every endpoint, service, and data flow should be documented. Don't omit components for brevity.

---

## Diagram Types

| Type | Purpose | Shows |
|------|---------|-------|
| **Component** | Architecture / static structure | Services, resources, connections, packages |
| **Sequence** | Runtime flow / dynamic behavior | Request lifecycle, message passing, error handling |
| **Unified Flow** | End-to-end overview | All phases as a single diagram — the "executive summary" |

For each service or endpoint, create **both** a component and a sequence diagram.

**Unified Flow diagrams** belong in the root `README.md` for immediate visibility. Per-service diagrams go in `docs/`.

---

## Mermaid Diagram Standards

Use **Mermaid diagrams** (not ASCII art) with this color palette for consistency:

- **Red (primary change):** `fill:#e74c3c,color:#fff,stroke:#c0392b,stroke-width:2px`
- **Orange (review/secondary):** `fill:#f39c12,color:#000,stroke:#d68910,stroke-width:2px`
- **Green (tests/additions):** `fill:#2ecc71,color:#000,stroke:#27ae60,stroke-width:2px`
- **Blue (interfaces/read-only):** `fill:#3498db,color:#fff,stroke:#2980b9,stroke-width:2px`
- **Grey (context-only/external):** `fill:#bdc3c7,color:#000,stroke:#95a5a6,stroke-width:2px`

---

## PlantUML Standards (if project uses PlantUML)

- **AWS Icons**: Use `aws-icons-for-plantuml` latest stable (`!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v20.0/dist`).
- **Theme**: `!theme aws-orange` for sequence diagrams. Custom skinparams for component diagrams.
- **Participant aliases**: Must match exactly between declaration and usage — mismatched aliases create ghost participants.
- **Width control**: Keep `nodesep` ≤ 80 for sequence diagrams with many participants. Use `-DPLANTUML_LIMIT_SIZE=16384` when exporting.
- **Naming**: Files use `PascalCase_With_Underscores` matching diagram content.
- **Numbered arrows**: Use circled Unicode digits (①②③…) on arrow labels to show execution sequence.
- Always re-export images after any source file change.

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
- **Generating Diagrams**: Commands to export from source files.

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
- **Stale diagrams** — re-export images after every source change.
- **Forgetting render flags** — wide PlantUML diagrams need `-DPLANTUML_LIMIT_SIZE=16384`.
