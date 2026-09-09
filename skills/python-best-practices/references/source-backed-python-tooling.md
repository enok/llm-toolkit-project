---
title: Source-backed Python tooling and runtime guidance
tags: [python, ruff, uv, mypy, typing, async, notebooks, tooling]
---

# Source-backed Python tooling and runtime guidance

Use this reference for linting, formatting, typing, packaging, async execution,
and notebook behavior. Primary sources:

- [Python typing documentation](https://docs.python.org/3/library/typing.html)
- [PEP 8](https://peps.python.org/pep-0008/)
- [Ruff documentation](https://docs.astral.sh/ruff/)
- [uv documentation](https://docs.astral.sh/uv/)

- Preserve the destination repository's toolchain. Introduce Ruff, mypy,
  Pyright, or uv only when already adopted or explicitly requested.
- Keep formatting/lint changes separate from behavioral fixes unless tooling
  work is the task.
- Type public boundaries; type internal helpers when it clarifies behavior or
  catches real defects.
- Use `Protocol` or ABC boundaries where external collaborators need stable
  test doubles.
- In async code, verify awaiting, cancellation, isolation of blocking work, and
  timeouts at external boundaries.
- Inspect notebook provenance and contents before execution. Execute only an
  explicitly trusted notebook into temporary output, in an isolated,
  credential-free, network-restricted environment with resource limits. Keep
  environment-specific values outside committed cells.

Match the repository's formatter, dependency manager, test runner, and
supported Python versions rather than importing a team style guide wholesale.
