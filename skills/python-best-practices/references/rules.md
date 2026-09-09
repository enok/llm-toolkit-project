---
trigger: always_on
description: Python language patterns, logging, testing, concurrency
---

# Python Best Practices

Compact always-on summary of the Python baseline. The full guide with expanded examples is `AGENTS.md` in this skill; individual `rules/*.md` files cover the highest-impact rules in depth.

## Language Fundamentals

- **PEP 8**: 4-space indentation, `snake_case` functions/variables, `PascalCase` classes, `UPPER_SNAKE_CASE` constants; match the project's formatter line length (Black 88, many projects 120).
- **Imports**: stdlib, third-party, local — separated by blank lines; no wildcard imports outside `__init__.py` re-exports; remove unused imports.
- **Type hints** on public signatures; `Final` for constants; match the codebase's existing typing level rather than adding hints selectively.
- **Strings**: f-strings in code, `%s` placeholders in logger calls (lazy evaluation).
- **Collections**: comprehensions over `map`/`filter`, `dict.get()` with defaults, `defaultdict`/`Counter`/`deque` for specialized needs.
- **Method design**: small single-responsibility functions, guard clauses, early validation; no mutable default arguments.
- **Algorithmic**: avoid O(n²) nested loops — build a `dict`/`set` lookup first.
- **Null safety**: `is None` checks, defensive chaining, validate at the boundary.

## Error Handling

- Catch the **most specific** exception; never bare `except:` or silent `except Exception: pass`.
- Preserve the cause: `raise DomainError(...) from e`.
- Use `with` (context managers) for every resource needing cleanup; `contextlib.contextmanager` for custom resources.
- Fail securely: on validation error raise, do not persist partial data; on external-service error classify and re-raise.

## Logging

- `logger.info("Processing %s items for %s", count, user_id)` — never f-strings in logger calls.
- Log exceptions with business context and `exc_info=True`; no PII, tokens, or credentials in logs.
- Propagate correlation/request IDs with a `logging.Filter`; use a JSON formatter for production/cloud logs.
- Support dynamic log levels (env var or a parameter store) for production troubleshooting.

## Design Patterns

- **Dependency injection**: accept every external dependency as an ABC/`Protocol` via `__init__`; wire concrete implementations only at the entry point (app factory, Lambda bootstrap). Never instantiate dependencies inside a class, import concrete infrastructure into domain code, or hide dependencies in module globals.
- Centralize magic values in a constants module with `Final`.
- Use `@dataclass(frozen=True)` for structured, immutable data.

## Testing

- pytest with Given/When/Then (or arrange/act/assert) and named constants over magic literals.
- Mock at the interface boundary: `Mock(spec=SomeABC)`; never patch deep internals.
- Cover happy path, null/empty inputs, boundaries, exception paths, and collection edge cases; run the tests yourself after every change.

## External Resources

- Reuse connection pools (SQLAlchemy) and SDK clients (boto3) at module or app scope; parameterized queries only.
- Reuse `requests.Session` with explicit timeouts; never call without a timeout.
- Cache with bounded size and TTL (`TTLCache`, `lru_cache(maxsize=...)`).

## Concurrency

- The GIL does **not** make compound operations atomic; `counter += 1` and check-then-act need a `threading.Lock`.
- First defense is immutability (frozen dataclasses, tuples); second is one lock guarding **all** reads and writes of shared mutable state.
- Prefer `queue.Queue`, `threading.local()`, and lock-guarded dicts; use double-checked locking for lazy initialization.
- In async code, await everything, isolate blocking work, and set timeouts at external boundaries.

## Notebooks

- Execute notebooks to a temporary output file during repair loops; use `--inplace` only for final runs.
- Load environment-specific values (profiles, buckets, tokens) from environment variables or a gitignored local config, never from committed cells; never print secrets — outputs get committed.
- Inspect notebook provenance before executing; run only trusted notebooks, in an isolated, credential-free environment.

## Tooling

- Preserve the destination repository's toolchain (Ruff, mypy, Pyright, uv, Black, Poetry); introduce new tools only when adopted or requested.
- Keep formatting/lint changes separate from behavioral fixes.

See `references/source-backed-python-tooling.md` for primary sources and the **best-practices**, **security**, and **testing** skills for the language-agnostic baseline.
