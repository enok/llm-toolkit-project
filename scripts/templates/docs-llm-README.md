# Repo-Local LLM Configuration

Use this directory for repository-specific LLM guidance that should not live in the shared toolkit links.

## Shared vs local

- Shared toolkit content stays in `.agents/`, `.claude/`, `.codex/`, `.cursor/`, and `.windsurf/`
- Repo-local context stays in `docs/llm/`
- Keep reusable generic guidance in the shared toolkit
- Keep project-specific architecture, domain terms, conventions, and workflow notes here

## Local layout

- `docs/llm/toolkit-selection.txt`: repo-local allowlist for shared toolkit rules and workflows
- `docs/llm/rules/`: project-only rules and conventions
- `docs/llm/workflows/`: project-only workflows and playbooks

## Cursor note

When `.cursor/` is linked to the shared toolkit, do not treat `.cursor/rules/` or `.cursor/workflows/` as repo-local.
Use `docs/llm/toolkit-selection.txt`, `.cursorignore`, and `.cursorindexingignore`
to narrow the local surface without editing shared toolkit files.

## Examples

- Toolkit `rules/examples/` contains shared starting points you can adapt into repo-local files.

## Integrations

- Toolkit `integrations/` contains shared setup guides for optional tools and services.
- Configure only the integrations your repository actually uses.
