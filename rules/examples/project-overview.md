# Project Overview (Template)

> **This is a template.** Copy and fill in your project's details.

## Project: [Your Project Name]

[One-line description of what the project does.]

**Issue Tracker:** [Jira project key, Linear team, GitHub Issues, etc.]
**Source Code:** [GitHub org/repo, GitLab group, etc.]

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | [e.g., Java 17, Spring Boot, Python/FastAPI, Node/Express, Go] |
| Frontend | [e.g., React 18, TypeScript, Next.js, Vue, Angular] |
| Databases | [e.g., PostgreSQL, MySQL, MongoDB, Redis, Elasticsearch] |
| Testing | [e.g., JUnit, Jest, pytest, Cypress, Playwright] |
| Build/CI | [e.g., GitHub Actions, GitLab CI, Jenkins, Docker] |

### Repository Layout

```
your-repo/
├── src/                    # [describe]
│   ├── api/                # [describe]
│   ├── services/           # [describe]
│   ├── models/             # [describe]
│   └── utils/              # [describe]
├── client/                 # [describe]
│   ├── src/
│   │   ├── components/     # [describe]
│   │   ├── hooks/          # [describe]
│   │   ├── pages/          # [describe]
│   │   └── utils/          # [describe]
├── tests/                  # [describe]
├── migrations/             # [describe]
└── e2e/                    # [describe]
```

### Key Domain Concepts

- **[Term 1]**: [What it means in this project]
- **[Term 2]**: [What it means in this project]
- **[Term 3]**: [What it means in this project]

### State Management (Frontend)

- **[Pattern 1]** — [when to use, e.g., "server state for new features"]
- **[Pattern 2]** — [when to use, e.g., "global state for existing features"]
- **[Pattern 3]** — [when to use, e.g., "local component state"]

### REST API Pattern

```
[Show your project's standard endpoint pattern. Examples for common stacks:]

# Java / Spring Boot
@RestController
@RequestMapping("/api/v1/entity")
public class EntityController {
    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('VIEW_ENTITY')")
    public ResponseEntity<EntityDto> getById(@PathVariable Long id) { ... }
}

# Python / FastAPI
@router.get("/api/v1/entity/{entity_id}")
async def get_entity(entity_id: int, user: User = Depends(get_current_user)):
    return entity_service.get_by_id(entity_id)

# Node / Express
router.get("/api/v1/entity/:id", authorize("VIEW_ENTITY"), async (req, res) => {
    const entity = await entityService.getById(req.params.id);
    res.json(entity);
});
```

### Async Jobs (if applicable)

[Describe how long-running operations are handled — message queues, background workers, etc.]

### API Type Generation (if applicable)

```bash
[Command to regenerate API types after backend changes, e.g.:]
npm run generate-api-types
```
