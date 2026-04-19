# Project-Specific Rule Templates

This directory contains **generic templates** for creating project-specific rules. Use these as starting points when adding rules for your own project.

## How to Use

1. Copy any relevant template to your project's rules directory.
2. Replace all placeholder text (`[...]`) with your project's specifics (tech stack, paths, commands, domain concepts).
3. Add the rules to your LLM context (IDE rules, system prompt, or symlinked skills).

## Templates Included

| File | What it demonstrates |
|------|---------------------|
| `project-overview.md` | Project context, tech stack, repo layout, key conventions |
| `data-science-project.md` | Data contracts, notebooks, orchestration, and DS project conventions |
| `ml-engineering-project.md` | Modeling objective, evaluation, feature ownership, and experiment tracking |
| `jupyter-notebook-project.md` | Notebook-specific environment, output, and promotion conventions |
| `java-backend.md` | Java backend code style, patterns, and conventions |
| `python-backend.md` | Python backend code style, patterns, and conventions |
| `infra-deployment.md` | Local environment setup, Docker, database management, CI/CD |
| `api-reference.md` | API endpoints, data flow, controller patterns (glob-triggered) |
| `python-lambda.md` | Python Lambda projects: execution model, boto3 patterns, error handling |

## Structure of a Good Project Rule

```markdown
# Rule Title

## Project Context
<!-- What project this applies to, key identifiers (issue tracker, source repo, etc.) -->

## Tech Stack
<!-- Table of layers and technologies -->

## Repository Layout
<!-- Directory tree showing key areas -->

## Key Patterns
<!-- Code examples showing the project's conventions -->

## Commands
<!-- Common commands developers need to run -->
```
