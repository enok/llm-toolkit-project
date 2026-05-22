---
description: Deep-dive a Jira ticket before implementation
---

# Ticket Research Workflow

Research a Jira ticket deeply and generate structured documentation to guide implementation. Produces a `docs/jira/<TICKET>/` folder with a `README.md` and `architecture.md`.

The user will provide a **ticket ID** (e.g., `ABC-1234`). Replace `<TICKET>` below with that ID.

---

## Phase 1: Gather Context (read-only, no file creation yet)

### 1. Read the Jira ticket
- Fetch the ticket (via Atlassian CLI, Jira MCP, or user-provided content).
- Extract: summary, description, acceptance criteria, reporter, assignee, labels, components, fix version, linked issues, subtasks, parent epic.
- If the description is vague or missing acceptance criteria, **draft 3-5 targeted questions** (present to user for approval before posting).

### 2. Read linked and related tickets
- Follow every issue link (blocks, is-blocked-by, relates-to, parent, subtasks).
- Search for sibling tickets with similar labels or components.
- For each related ticket, note: key, summary, status, and relationship.

### 3. Check for duplicates
- Search Jira with key terms from the summary/description.
- Search for closed tickets that may have already solved this or attempted it.
- If duplicates found, flag them to the user before proceeding.

### 4. Check existing PRs and branches
- Search GitHub for PRs mentioning `<TICKET>` in the title or body.
- Also search for PRs on related tickets.
- Check if a branch for this ticket already exists.

### 5. Read Confluence documentation
- Search Confluence with key terms from the ticket (feature name, component name, domain concepts).
- Always check the relevant architecture and product documentation spaces for cross-service context.
- Read the top 3-5 most relevant pages.
- Note: page title, space, URL, and a 1-2 sentence summary of relevance.

### 6. Classify the ticket
- **Type**: Bug fix | Feature | Refactor | Chore
- **Scope**: Backend-only | Frontend-only | Full-stack
- **Repos involved**: Which repos need changes?
- **Risk level**: Low (isolated change) | Medium (touches shared code) | High (cross-service, data migration)

---

## Phase 2: Deep Code Analysis

### 7. Identify and read all relevant source files
- Based on the ticket description and Confluence docs, identify the files that need changes.
- **Actually read each file** — do not just list them. Understand:
  - Current behavior
  - Data flow
  - Entry points (REST endpoints, event handlers, UI components)
  - Models/DTOs involved
  - Test coverage
- For files in **external repos**, use GitHub tools to read them remotely.

### 8. Trace the full data/request flow
- Map the end-to-end flow relevant to this ticket:
  - **Backend**: HTTP request → Controller/Resource → Service → Repository → Database
  - **Frontend**: User action → Component → Data hook → API call → Response → UI update
  - **Async flows**: Job submitted → Worker → Processing
- Identify every file touched in this flow.

### 9. Check git history on key files
- Review recent changes to understand who touched the code and what changed.
- **For bugs**: attempt to identify the commit that introduced the regression.
  - Note the commit SHA, author, date, and the PR/ticket it belonged to.
  - Include this in the README under **Root Cause**.

---

## Phase 3: Generate Documentation

### 10. Create the documentation folder
- Create `docs/jira/<TICKET>/` if it doesn't exist.

### 11. Generate `README.md`

```markdown
# <TICKET>: <Summary>

## Ticket Overview
<!-- Table: key, type, priority, status, reporter, assignee, labels, epic, sprint -->

## Problem Statement
<!-- What is broken or missing? Be specific. -->

## Acceptance Criteria
<!-- Copied from ticket, or inferred and marked as [inferred] -->

## Scope & Classification
<!-- Type, scope, repos, risk level -->

## Related Tickets
<!-- Table: ticket, summary, status, relationship -->

## Confluence References
<!-- Table: page title, space, URL, relevance summary -->

## Existing PRs & Branches
<!-- Table: PR number, title, status, key changes -->

## Files to Modify
<!-- Grouped by repo, then by layer (controller, service, model, component, test) -->

## Architecture / Data Flow
<!-- Mermaid diagram showing the relevant flow -->

## Implementation Plan
<!-- Ordered steps with files, changes, why, dependencies -->

## Testing Plan
### Unit tests
### Regression test (bugs only)
### Integration / E2E tests
### Manual QA checklist

## Open Questions
<!-- Anything still unclear. Tag with who should answer. -->
```

### 12. Generate `architecture.md`
- Use **Mermaid diagrams** (not ASCII art) for:
  - System context: how the affected component fits in the overall system
  - Data flow: step-by-step flow through the system for this feature/bug
  - Sequence diagram (if multi-service interactions)
- Include both **current state** (as-is) and **target state** (to-be) if this is a feature.
- **Mermaid color scheme** for consistency:
  - **Red (primary change):** `fill:#e74c3c,color:#fff,stroke:#c0392b,stroke-width:2px`
  - **Orange (review/secondary):** `fill:#f39c12,color:#000,stroke:#d68910,stroke-width:2px`
  - **Green (tests/additions):** `fill:#2ecc71,color:#000,stroke:#27ae60,stroke-width:2px`
  - **Blue (interfaces/read-only):** `fill:#3498db,color:#fff,stroke:#2980b9,stroke-width:2px`
  - **Grey (context-only/external):** `fill:#bdc3c7,color:#000,stroke:#95a5a6,stroke-width:2px`

---

## Phase 4: Validate & Present

### 13. Cross-check completeness
- [ ] Every AC has a matching implementation step
- [ ] Every file to modify has been actually read
- [ ] Backward compatibility verified for stored data, messages, and APIs that other components rely on
- [ ] Breaking changes to shared constants or contracts flagged and coordinated with downstream consumers
- [ ] New configuration keys or env vars propagated to every required environment (per this repo’s conventions)
- [ ] New cross-service message or event fields coordinated with consuming services (names, types, optional vs required)
- [ ] Caching, warm-start, or scheduled paths still behave correctly if this ticket touches them
- [ ] Test plan covers happy path + edge cases
- [ ] Bug tickets: regression commit identified, regression test included
- [ ] No placeholder text remains

### 14. Present summary to the user
- What the ticket is about (1-2 sentences)
- How many files need changes and in which repos
- The highest-risk part of the implementation
- Any open questions or blockers
- Suggested order of implementation

---

## Notes

- **Do NOT guess file paths or code behavior** — always read the actual code.
- **Do NOT create files until Phase 3** — gather all context first.
- If the ticket spans multiple repos, use GitHub tools to read remote files.
- Prefer updating existing docs over creating new files if prior research exists.
