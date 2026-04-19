# LLM Toolkit for Data Science Projects

This repository contains LLM (Large Language Model) tooling configurations, workflows, and skills for assisting with data science, analytics, and thesis projects. **This toolkit is designed to be used locally only and should never be committed to your main project repository.**

## Philosophy

Your main project should remain **clean of any LLM-related files**. This separation ensures:

- **No vendor lock-in** — Your core project doesn't depend on specific LLM tools
- **Clean repository** — No LLM configuration clutter in your project's history
- **Privacy** — LLM interactions remain local to your machine
- **Reproducibility** — Your project can be understood without LLM context

## Repository Structure

```
llm-toolkit-project/
├── skills/                 # CANONICAL skills (source of truth, 65 skills)
│   ├── best-practices/
│   │   ├── SKILL.md        # Summary (loaded on skill activation)
│   │   ├── rules/          # Fine-grained rules (loaded on-demand)
│   │   └── references/     # Deep references (loaded on-demand)
│   ├── python-best-practices/
│   ├── testing/
│   └── ... (62 more skills)
├── workflows/              # CANONICAL workflows (source of truth, 49 workflows)
│   ├── review.md
│   ├── ticket-research.md
│   └── ...
├── .agents/
│   └── skills -> ../skills      # Junction to canonical
├── .claude/
│   └── skills -> ../skills      # Junction to canonical
├── .codex/
│   └── skills -> ../skills      # Junction to canonical
├── .windsurf/
│   └── workflows -> ../workflows # Junction to canonical
├── .cursor/                # Cursor-specific agents
│   └── agents/
├── .setup/                 # Setup templates and integration guides
│   ├── examples/
│   └── integrations/
├── rubrics/                # Review rubrics (architecture, security, checklist)
├── docs/llm/               # Project-specific LLM context
├── scripts/
│   ├── setup-repo.{sh,ps1,cmd} # Setup in consumer repos
│   ├── ensure-symlinks.{sh,ps1,cmd} # Symlink maintenance
│   ├── lib.{sh,ps1}        # Shared library functions
│   └── security-check-toolkit.sh
└── README.md               # This file
```

> **Note:** `AGENTS.md` and `CLAUDE.md` are **not** committed in this toolkit. They are
> generated or written per-consumer repo and gitignored locally there. Use
> `scripts/templates/consumer-AGENTS.md` as the starting template for a new consumer.

## Architecture: Single Source of Truth

Skills and workflows live in exactly ONE place each. Agent directories are **junctions** (no duplication):

- **Canonical skills**: `skills/` (dir-per-skill with `SKILL.md`)
- **Canonical workflows**: `workflows/` (flat `.md` files)
- **All agent paths resolve to the same content** — edit once, all agents see the change

**Progressive disclosure** reduces context/tokens:

| Level | Content | Loaded When | Tokens |
|-------|---------|-------------|--------|
| 1 | Skill metadata (`name`, `description`) | At startup | ~100 each |
| 2 | `SKILL.md` body | Skill activates | <5000 |
| 3 | `rules/*.md`, `references/*.md` | Specifically needed | Varies |

Old `.windsurf/rules/` (always-on) have been dissolved into skills as on-demand references.

## Quick Start

### 1. Clone this repository separately

```bash
git clone <this-repo-url> ~/llm-toolkit
cd ~/llm-toolkit
```

### 2. Run the setup script in your target project

#### Option A: Setup Script (Recommended)

**Linux/macOS/Git Bash:**
```bash
# Navigate to your main project
cd /path/to/your/data-science-project

# Run setup (interactive - select which LLM tools to enable)
~/llm-toolkit/scripts/setup-repo.sh .
```

**Windows PowerShell:**
```powershell
# Navigate to your main project
cd C:\path\to\your\data-science-project

# Run setup (may need Developer Mode or Run as Administrator for symlinks)
..\llm-toolkit\scripts\setup-repo.ps1 .
```

**Windows CMD (as Administrator):**
```cmd
# Navigate to your main project
cd C:\path\to\your\data-science-project

# Run elevated setup
..\llm-toolkit\scripts\setup-repo.cmd .
```

The setup script will:
- Interactively ask which LLM tools to enable (Windsurf, Cursor, Claude Code, Codex)
- Create symlinks from your project to the toolkit
- Scaffold `docs/llm/` with project-specific configuration files
- Generate `AGENTS.md` with LLM context
- Update `.gitignore` to exclude linked files

#### Option B: Legacy Enable Script

For simpler setups, use the legacy `enable-llm.sh`:

```bash
# Enable LLM support (creates symlinks)
~/llm-toolkit/scripts/enable-llm.sh .

# Or copy files instead of symlinking
~/llm-toolkit/scripts/enable-llm.sh . --copy

# Or only link directories (keep AGENTS.md/CLAUDE.md local)
~/llm-toolkit/scripts/enable-llm.sh . --dirs-only

# Or use relative paths for portability
~/llm-toolkit/scripts/enable-llm.sh . --relative
```

### 3. Verify LLM files are gitignored

The setup scripts automatically update `.gitignore`. Ensure your project includes:

```gitignore
# LLM integration - symlinked/generated content (do not commit)
.agents/
.setup/
.windsurf/
.cursor/
.claude/
.codex/

# Keep repo-local visibility filters committed
!.cursorignore
!.cursorindexingignore
```

### 4. Use LLM assistance

Now you can use Windsurf, Cursor, Claude Code, or other LLM tools with your project, and they will have access to the relevant context and workflows.

## Disabling LLM Support

To remove LLM files from your project (e.g., before committing or sharing):

**Using the legacy enable script:**
```bash
~/llm-toolkit/scripts/enable-llm.sh /path/to/your/project --clean
```

**Manual cleanup:**
```bash
rm -rf .agents .setup .windsurf .cursor .claude .codex
rm -f AGENTS.md CLAUDE.md .cursorignore .cursorindexingignore
rm -rf docs/llm scripts/sync-llm-configs.*
```

This removes all LLM-related files and restores your project to a clean state.

## Available Tools

### Workflows

- `project-execution-main.md` — Orchestrate all technical work (infra, code, notebooks, pipelines)
- `thesis-writing-main.md` — Orchestrate thesis writing and formatting
- `data-source-ingestion.md` — Data ingestion workflows
- `pipeline-change.md` — Bronze/Silver/Gold pipeline modifications
- `review.md` — Code review workflows

### Skills

- `document-conversion/SKILL.md` — Convert between document formats (PDF, DOCX, PPTX, XLSX)
- `thesis-bibliography/SKILL.md` — Bibliography management

### Rules

- `analytics-discipline.md` — Best practices for analytical work
- `bilingual-doc-sync.md` — Keep bilingual docs synchronized
- `data-pipeline-contracts.md` — Data pipeline contract guidelines
- `notebook-discipline.md` — Jupyter notebook best practices
- `security.md` — Security guidelines
- And many more...

## Customizing for Your Project

### Adding Project-Specific Workflows

Create new workflows in your project's `docs/llm/workflows/` directory:

```bash
# After enabling LLM support
cd /path/to/your/project
mkdir -p docs/llm/workflows
cp ~/llm-toolkit/docs/llm/workflows/template.md docs/llm/workflows/my-custom-workflow.md
```

### Modifying Existing Rules

If you need project-specific modifications to rules:

1. Copy the rule file to your project's `docs/llm/rules/`
2. Modify it there (it will override the toolkit version for that project)

## Security Best Practices

1. **Never commit LLM files** — Always ensure `.gitignore` excludes them
2. **Keep API keys in `.env`** — Never hardcode credentials in LLM configuration
3. **Review LLM suggestions** — Always verify code and configurations suggested by LLMs
4. **Local processing preferred** — Use local tools when possible (e.g., local document conversion)

## Project Separation Checklist

Before committing your main project, ensure:

- [ ] No `.windsurf/` directory in git
- [ ] No `.cursor/` directory in git
- [ ] No `.agents/` directory in git
- [ ] No `AGENTS.md` in git
- [ ] No `CLAUDE.md` in git
- [ ] `.gitignore` properly excludes LLM files
- [ ] `docs/llm/` is gitignored or contains only non-sensitive project documentation

## Troubleshooting

### LLM tools not finding configuration

Ensure you've run the enable script from your project directory:

```bash
cd /path/to/your/project
~/llm-toolkit/scripts/enable-llm.sh .
```

### Changes to toolkit not reflecting

If using `--copy` mode, you'll need to re-run the enable script after toolkit updates:

```bash
~/llm-toolkit/scripts/enable-llm.sh . --clean
~/llm-toolkit/scripts/enable-llm.sh . --copy
```

If using default symlink mode, changes should reflect immediately.

### Permission denied on Windows

On Windows, symlinks require **Developer Mode** or **Administrator privileges**:

**Option 1: Enable Developer Mode (Recommended)**
1. Settings → System → For developers
2. Enable "Developer Mode"
3. Run PowerShell normally: `..\llm-toolkit\scripts\setup-repo.ps1 .`

**Option 2: Run as Administrator**
1. Open Command Prompt as Administrator
2. Run: `..\llm-toolkit\scripts\setup-repo.cmd .`

**Option 3: Use copy mode (legacy script)**
```bash
~/llm-toolkit/scripts/enable-llm.sh . --copy
```
Note: Copy mode requires re-running the script after toolkit updates.

## Contributing

To add new workflows or rules to the toolkit:

1. Add files to the appropriate directory in this repository
2. Run the security check before committing:
   ```bash
   ./scripts/security-check-toolkit.sh
   ```
3. Test with the setup script in a test project
4. Commit and push to the toolkit repository
5. All projects using the toolkit will get the updates (if using symlink mode)

### Scripts Overview

| Script | Purpose | Platform |
|--------|---------|----------|
| `setup-repo.sh` | Full setup with interactive tool selection | Linux/macOS/Git Bash |
| `setup-repo.ps1` | PowerShell version of setup | Windows |
| `setup-repo.cmd` | Elevated CMD wrapper | Windows (Admin) |
| `ensure-symlinks.sh` | Repair/verify symlinks | Linux/macOS/Git Bash |
| `ensure-symlinks.ps1` | Repair/verify symlinks | Windows |
| `lib.sh` / `lib.ps1` | Shared script functions | Both |
| `security-check-toolkit.sh` | Pre-commit security validation | Linux/macOS/Git Bash |

## License

This toolkit is provided as-is for educational and development purposes. The main project retains its own license independently of this toolkit.

---

**Remember**: Your main project should never contain LLM-related files. Keep them separate and local-only!
