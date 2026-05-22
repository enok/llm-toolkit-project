# LLM Config Setup Prompt

Copy and paste the **Prompt** section below into a new IDE session for any consumer project.

---

## Prerequisites

Before running this prompt, ensure the following:

1. **Clone the shared toolkit repo** as a sibling of this repo (same parent directory):
   ```
   code/
   ├── <toolkit-repo>/       ← shared LLM toolkit
   ├── <reference-repo>/     ← optional reference implementation
   └── <your-project>/       ← the repo you are setting up
   ```
   If not cloned yet: `git clone <toolkit-repository-url>`

2. If your organization has a **reference consumer repo**, clone it as a sibling so you can compare expected `AGENTS.md`, `.gitignore`, and local scaffold sections.

3. **The project must already have an `AGENTS.md`** with project-specific content (architecture, stack, conventions). If it does not exist yet, create one describing the project before running this prompt.

4. **Tooling for ticket workflows** — the `ticket-research` workflow requires all three:

   **a) Atlassian CLI (`acli`)** — Jira ticket fetching, search, and linked issue traversal:
   - macOS: `brew tap atlassian/homebrew-acli && brew install acli`
   - Linux: see [Install ACLI](https://developer.atlassian.com/cloud/acli/guides/install-acli/)
   - Windows: see [Install ACLI](https://developer.atlassian.com/cloud/acli/guides/install-acli/) (download binary or use Scoop/Chocolatey if available)
   - Authenticate: `acli jira auth login --web` (complete the browser flow)
   - Verify: `acli jira workitem view <TICKET-ID> --json --fields summary`

   **b) GitHub CLI (`gh`)** — PR search, branch checks, CI status:
   - macOS: `brew install gh`
   - Linux: `sudo apt install gh` (Debian/Ubuntu) or `sudo dnf install gh` (Fedora) — see [cli.github.com](https://cli.github.com/)
   - Windows: `winget install GitHub.cli`
   - Authenticate: `gh auth login` (follow prompts, select GitHub.com, HTTPS, browser)
   - Verify: `gh pr list --repo <org>/<repo> --limit 1`

   **c) Confluence MCP (`mcp-atlassian`)** — documentation search and page reading:
   - This is an MCP server configured in your IDE (Windsurf/Cursor), not a standalone CLI
   - Follow your IDE's MCP server setup to add `mcp-atlassian` with your Atlassian credentials
   - Verify: the IDE should show Confluence tools available (search, get_page, etc.)

5. **Directory links** (OS-specific — no manual action needed, the prompt handles it):
   - **Windows**: uses junctions (`New-Item -ItemType Junction`) — no admin or Developer Mode required
   - **macOS / Linux**: uses regular symlinks (`ln -s`) — no special permissions needed

6. **IDE**: open the target project as the active workspace in Windsurf (or Cursor) before pasting the prompt.

---

## Prompt

Clean up and re-setup all LLM tool configurations for this project:

1. **Remove** all existing LLM junctions/symlinks: `.agents`, `.claude`, `.codex`, `.cursor`, `.windsurf`, `.setup`

2. **Recreate** all 6 directory links pointing to the sibling toolkit repo in the same parent directory:
   - `.agents`, `.claude`, `.codex`, `.cursor`, `.windsurf`, `.setup`
   - Resolve the toolkit path relative to this repo: `<this-repo>/../<toolkit-repo>/<dir>`
   - **Windows**: use `New-Item -ItemType Junction` (not symlinks — avoids admin/Developer Mode)
   - **macOS / Linux**: use `ln -s`

3. **Scaffold missing workspace artifacts** (all gitignored):
   - `docs/llm/` with `README.md`, `toolkit-selection.txt`, `rules/README.md`, `workflows/README.md`
   - `scripts/sync-llm-configs.sh` and `scripts/sync-llm-configs.ps1`
   - `.cursorignore` and `.cursorindexingignore`

4. **Update `.gitignore`**: ensure all 6 junction dirs, `.cursorignore`, `.cursorindexingignore`, `docs/llm/`, `docs/jira`, and `scripts/sync-llm-configs.*` are ignored — plus negation lines `!.cursorignore` and `!.cursorindexingignore` so those stay committed

5. **Read `AGENTS.md`** and adjust:
   - Remove any ticket-specific content (`<TICKET-ID>`, Active Ticket, Changes applied, ticket-specific `docs/jira/` paths)
   - Update the LLM Dev Tools section to list junctioned directories, committed LLM files, repo-local docs, and sync script references
   - Keep all project-specific architecture, domain, stack, and convention sections intact

6. **Run full LLM config validation**: junction health, toolkit parity (skills/rules/workflows/agents counts match source), no broken symlinks, .gitignore coverage, no CRLF, no ticket refs in AGENTS.md, all scaffolded files present

Use your organization’s reference consumer repo, when available, as the template for `AGENTS.md` and `.gitignore` LLM Dev Tools section structure.
