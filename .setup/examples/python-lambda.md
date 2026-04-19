# Python Lambda (Template)

> **This is a template.** Copy, fill in your project's specifics, and place in your IDE's rules directory.

## Project Context

**[project-name]** — AWS Lambda ([Python version]) that [one-line description].

**Jira**: [project key] · **Team**: [team name]

## Tech Stack

Python [version], AWS Lambda, boto3 ([services used]), [other dependencies].
CI/CD: Jenkins (`Jenkinsfile` + `common-utils` shared library `standardPythonLambda`), CodeDeploy.

## Project Layout

```
src/
├── [handler].py                # Lambda handler, initialization
├── [business_logic].py         # Core logic, validation, external service calls
├── [constants].py              # Constants, env var references, error codes
├── [logging].py                # Logger setup
└── [exceptions].py             # Exception hierarchy
cm/
├── requirements.txt            # Python dependencies
└── envs/{dev,qa,stage,prod}/
    └── environment.json        # Per-environment Lambda env vars
docs/
├── *.puml                      # Architecture diagrams (source of truth)
└── *.png                       # Generated diagram images
```

## Lambda Execution Model

- **Cold start**: `initialize()` creates boto3 resources/clients, loads cached data.
- **Warm start**: Reuses cached clients and data. Only reloads if caches are empty.
- **Scheduled Event**: CloudWatch rule triggers cache refresh (e.g., `detail-type: "Scheduled Event"`).
- **[Trigger] Event**: [Describe the trigger — SNS, SQS, API Gateway, etc.] → parse → validate → process → respond.
- boto3 clients that should be cached: [list them]. Clients created per-invocation: [list them].

## Python Patterns

- `from typing import Final` for constants. [Type hints on functions: yes/no — match existing style].
- `global` keyword for module-level state (cached clients, data).
- `json.loads()`/`json.dumps()` for all JSON — never string concatenation.
- `datetime.datetime` with `ZoneInfo("[timezone]")` for timestamps (stdlib `zoneinfo`, not `pytz`).
- Exception classes in `[exceptions].py` — use the project’s established validation and runtime exception hierarchy.
- Logger formatting: [describe pattern — `%s` formatting, f-strings, etc.].

## Error Handling

- **Validation errors** (4xxx): `ValidationException(code, message)` — client/payload issues.
- **Lambda errors** (5xxx): `LambdaException(code, message, type)` — infrastructure/runtime issues.
- **External service errors**: Catch `botocore.exceptions.ClientError`, classify by error type.
- Never swallow exceptions. No empty except blocks. Always log before raising.

## Environment Variables

| Variable | Description | Example (prod) |
|----------|-------------|----------------|
| `[VAR_NAME]` | [description] | `[value]` |

## AWS Resources

| Resource | Name (prod) | Purpose |
|----------|-------------|---------|
| [Service] | `[resource-name]` | [purpose] |

## Backward Compatibility

- **Input format**: [Describe who publishes the input and what format]. Changes must be coordinated with upstream.
- **Output format**: [Describe who consumes the output]. Adding optional fields is safe; renaming/removing existing fields is a **Blocker**.
- **Config**: New env vars need updates to ALL `cm/envs/{env}/environment.json` files.

## Testing

- [Test framework]: pytest + `unittest.mock` or `moto` for boto3 mocking.
- Cover: all validation paths, happy path, external service error handling.
- Named constants, DRY fixtures.

## Never Commit

`.idea/`, `*.iml`, `desktop.ini`, `.env`, `__pycache__/`, `*.pyc`, `.venv/`, files with secrets, local config overrides.
