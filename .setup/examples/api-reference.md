# API Reference (Template)

> **This is a template.** Copy, fill in your project's API endpoints, and place in your IDE's rules directory with a glob trigger so it activates only when editing API-related files.

## Trigger Configuration

For IDEs that support glob-triggered rules (e.g., Windsurf), configure the trigger:

```yaml
trigger: glob
description: REST API endpoint details and data flow for [your-project]
globs:
  - "src/main/java/**/controller/**/*.java"
  - "src/routes/**/*.ts"
  - "app/api/**/*.py"
```

## Endpoints

### [METHOD] `/path`
- **Controller/Handler**: `[ClassName]`
- **Purpose**: [What this endpoint does]
- **Params**: [Key parameters and their meaning]
- **Key logic**: [Important business logic, validations, integrations]

### [METHOD] `/another-path`
- **Controller/Handler**: `[ClassName]`
- **Purpose**: [What this endpoint does]
- **Params**: [Key parameters]
- **Returns**: [Response format]

## Controller/Handler Pattern

```
[Show your project's standard controller/handler pattern with annotations, logging, error handling]
```

## Data Flow

```
[Map the end-to-end flow for key operations, e.g.:]

User Request → /endpoint
    → Controller
    → Service (business logic)
    → Repository / External API
    → Response
```

## Running Tests

```bash
# [Your project's test commands for API tests]
```
