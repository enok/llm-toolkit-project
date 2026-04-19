# Infrastructure & Deployment (Template)

> **This is a template.** Copy and fill in your project's infrastructure and deployment details.

## Services

| Service | Purpose | Port(s) |
|---------|---------|--------|
| [database] | [e.g., PostgreSQL 15] | [e.g., 5432] |
| [cache] | [e.g., Redis 7] | [e.g., 6379] |
| [search] | [e.g., Elasticsearch 8] | [e.g., 9200] |
| [backend] | [e.g., API server] | [e.g., 8080] |
| [frontend] | [e.g., Dev server] | [e.g., 3000] |

## Initial Setup

```bash
# [Your project's setup commands]
# Example:
docker compose up -d
npm install
npm run db:migrate
npm run dev
```

## Common Commands

```bash
# [List your project's frequently used commands]
# Container status
docker compose ps

# Stop all
docker compose down

# Full reset (nuclear option)
docker compose down -v && docker compose up -d
```

## Database Management

```bash
# [Your project's database commands]
# Run migrations
npm run db:migrate          # or: make migrate-dbs, rails db:migrate, alembic upgrade head

# Seed data
npm run db:seed

# Reset database
npm run db:reset
```

## Deployment

- **CI/CD**: [e.g., GitHub Actions, GitLab CI, Jenkins]
- **Artifacts**: [e.g., Docker images to ECR/GCR/Artifactory]
- **Infrastructure**: [e.g., Kubernetes, ECS, Lambda]
- **Deployment trigger**: [e.g., merge to main, manual, tag-based]

## CI/CD Pipeline

**Build stages:**
1. [e.g., Lint and type check]
2. [e.g., Unit tests]
3. [e.g., Build artifacts]
4. [e.g., Integration tests]
5. [e.g., Deploy to staging]
6. [e.g., E2E tests]

## Pre-commit Hooks (if applicable)

| Hook | Purpose |
|------|---------|
| [hook name] | [what it does] |
| [hook name] | [what it does] |

## Troubleshooting

```bash
# [Common issues and their fixes]

# Build fails — clear cache
# [your cache clear command]

# Type errors after API change
# [your type regeneration command]

# Full environment reset
# [your nuclear reset command]
```
