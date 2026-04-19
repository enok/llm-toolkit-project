# AWS SAM Lambda Project Rules

Project-specific rules for AWS SAM-based Lambda services. Copy and customize for your repo.

## Tech Stack

- **Runtime**: Java 17 / Python 3.12 (adjust per repo)
- **Framework**: AWS SAM (`template.yaml`)
- **Build**: Maven / pip (adjust per repo)
- **Deploy**: SAM CLI (`sam build && sam deploy`)
- **Infrastructure**: SAM template.yaml (CloudFormation superset)

## SAM Template Conventions

- Use `Globals` section for shared function properties (Runtime, MemorySize, Timeout, Environment).
- Define environment-specific config via `Parameters` with `AllowedValues` for each stage.
- Use `!Sub` for dynamic ARN construction — never hardcode account IDs or region.
- Prefer `AWS::Serverless::Function` over raw `AWS::Lambda::Function` unless SAM transforms are insufficient.
- Every function must have explicit `Timeout` (never rely on default 3s for non-trivial work).
- Use `Layers` for shared dependencies across functions in the same template.

## Lambda Best Practices

- Keep handler methods thin — delegate to service classes for testability.
- Use environment variables for all external configuration (table names, queue URLs, bucket names).
- Validate all event input at the handler boundary — fail fast with clear error messages.
- Use structured JSON logging for CloudWatch discoverability.
- Set reserved concurrency when the downstream dependency has a connection limit.
- Use dead-letter queues (DLQ) for async invocations.

## Testing

- Unit tests mock AWS SDK clients — never call real AWS services.
- Use `sam local invoke` for local integration testing with Docker.
- Use `sam local start-api` for local API Gateway testing.
- Template validation: `sam validate --lint` before committing.

## Security

- IAM policies follow least privilege — scope to specific resources, not `*`.
- Never log event payloads that may contain PII.
- Use AWS Secrets Manager or SSM Parameter Store for secrets — never environment variables for sensitive values.
- Enable X-Ray tracing for production functions.

## Build & Deploy

```bash
# Validate template
sam validate --lint

# Build
sam build

# Deploy (guided first time, then use samconfig.toml)
sam deploy --guided

# Local testing
sam local invoke FunctionName -e events/event.json
```

## Key Commands

```bash
# Run unit tests
mvn test                          # Java
pytest tests/                     # Python

# Package and deploy
sam build && sam deploy --no-confirm-changeset --stack-name <stack>

# View logs
sam logs -n FunctionName --stack-name <stack> --tail
```
