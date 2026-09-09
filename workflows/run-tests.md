---
description: Run the right tests for a given change
---

# Run Tests Workflow

Run the right tests for a given change. The user will specify what changed or what they want to verify.

---

## Step 1: Identify what changed

Determine the scope of changes:
- **Specific file(s)** — run tests for those files
- **Specific feature/module** — run module-level tests
- **Ticket changes** — run all tests related to the ticket's scope
- **Full suite** — run everything

---

## Step 2: Detect the test stack

Detect the project's build/test tooling from its manifest before running anything. Prefer the repo's documented test command (`AGENTS.md`, `README.md`, CI workflow) over defaults.

| Manifest | Stack | Default command |
|---|---|---|
| `pom.xml` | Java (Maven) | `mvn test` (module: `mvn -pl <module> test`) |
| `build.gradle`/`build.gradle.kts` | Java/Kotlin (Gradle) | `./gradlew test` |
| `package.json` | JS/TS | `npm test` / `pnpm test` / `yarn test` (match the lockfile) |
| `pytest.ini`, `pyproject.toml`, `setup.cfg`, `requirements*.txt` | Python | `pytest` |
| `template.yaml` + `tests/` | AWS SAM | project's documented test command, usually `pytest` or `npm test` |

---

## Step 3: Run the appropriate tests

Examples per stack (run from repo root unless the project documents another entry point):

### All tests (default)
```bash
mvn test          # Maven
pytest            # Python
npm test          # Node
```

### Single test file / class / method
```bash
# Maven
mvn test -Dtest=ClassName
mvn test -Dtest='ClassName#methodName'

# pytest
pytest path/to/test_file.py -v
pytest path/to/test_file.py::TestClassName::test_case_name -v

# Node (jest/vitest)
npm test -- path/to/file.test.ts
npm test -- -t "test name"
```

### With coverage
```bash
mvn verify                                   # Maven (JaCoCo/Clover when configured)
pytest --cov=src --cov-report=term-missing   # Python
npm test -- --coverage                       # Node
```

---

## Step 4: Which tests to run for a given change

| Changed area | Tests to run |
|---|---|
| One source file | The closest matching test file or module tests |
| Shared constants or core utilities | All dependent tests, often module-wide or suite-wide |
| Test fixtures, bootstrap, or global config | Full suite for the detected stack |
| New feature touching multiple modules | Module-level tests first, then broader suite |

---

## Step 5: Verify results

- **All tests must pass** before proceeding.
- If a test fails, diagnose the root cause and fix before continuing.
- Re-run after every fix to confirm.

---

## Troubleshooting

### Import/classpath errors (`ModuleNotFoundError`, `NoClassDefFoundError`, `Cannot find module`)
- Verify the repo’s test bootstrap is being loaded correctly.
- Run from repo root unless the project explicitly documents another entry point.
- For Maven multi-module builds, `mvn install -pl <dependency-module>` may be required before testing a downstream module.

### Missing env vars (`KeyError` on import)
- Ensure test fixtures or env setup run before application imports.
- Provide the minimum required test configuration documented by the project.

### External dependencies not mocked or stubbed
- Verify the project’s mocking or fixture pattern is active for SDK clients, databases, queues, or HTTP calls.
- Reset shared module-level state between tests when the code caches clients or configuration.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
