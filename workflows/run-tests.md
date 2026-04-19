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

## Step 2: Run the appropriate tests

### All Tests (default — run from repo root)
```bash
pytest
```

### Single test file
```bash
pytest tests/test_<module>.py -v
pytest path/to/test_file.py -v
```

### Single test class
```bash
pytest tests/test_<module>.py::TestClassName -v
pytest path/to/test_file.py::TestClassName -v
```

### Single test method
```bash
pytest tests/test_<module>.py::TestClassName::test_case_name -v
```

### With coverage
```bash
pytest --cov=src --cov-report=term-missing
```

---

## Step 3: Which tests to run for a given change

| Changed area | Tests to run |
|---|---|
| One source file | The closest matching test file or module tests |
| Shared constants or core utilities | All dependent tests, often module-wide or suite-wide |
| Test fixtures, bootstrap, or global config | Full suite: `pytest` |
| New feature touching multiple modules | Module-level tests first, then broader suite |

---

## Step 4: Verify results

- **All tests must pass** before proceeding.
- If a test fails, diagnose the root cause and fix before continuing.
- Re-run after every fix to confirm.

---

## Troubleshooting

### Import errors (`ModuleNotFoundError`)
- Verify the repo’s test bootstrap is being loaded correctly.
- Run from repo root unless the project explicitly documents another entry point.

### Missing env vars (`KeyError` on import)
- Ensure test fixtures or env setup run before application imports.
- Provide the minimum required test configuration documented by the project.

### External dependencies not mocked or stubbed
- Verify the project’s mocking or fixture pattern is active for SDK clients, databases, queues, or HTTP calls.
- Reset shared module-level state between tests when the code caches clients or configuration.
