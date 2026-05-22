---
description: Add a new REST endpoint, service, or backend feature
---

# New Backend Feature Workflow

Step-by-step workflow for adding a new backend feature such as a new endpoint, service integration, async worker path, or data-processing capability.

---

## Step 1: Read the task and existing patterns

1. Run the **ticket-research** workflow first if not already done.
2. Identify the domain area.
3. Read an existing endpoint, service, handler, or worker in that domain to understand the pattern.

---

## Step 2: Implement the logic

- Keep business logic separate from transport or framework wiring.
- Validate inputs before executing side effects.
- Follow the project’s existing error, logging, and constant conventions.
- Do not add project-wide utility patterns inline if an established abstraction already exists.

---

## Step 3: Update entry points and contracts

- If adding a new request field, event payload attribute, or API shape, update all producers and consumers that depend on that contract.
- Verify backward compatibility for optional fields and missing attributes.
- If the feature adds a persistence or message-schema change, check downstream readers before merging.

---

## Step 4: Update documentation

- Update `README.md`, architecture docs, diagrams, or runbooks if the behavior or operating model changed.
- Update environment configuration docs if new settings or secrets are required.

---

## Step 5: Update configuration and permissions

- Add required environment variables, secret references, feature flags, or configuration entries in every supported environment.
- Update permissions, IAM, service accounts, or role policies when the feature needs new access.
- Keep secret material out of source control.

---

## Step 6: Verify lifecycle and caching behavior

- If the feature depends on initialization-time state, verify startup, warm-cache, and refresh behavior.
- If new clients, connections, or background resources are introduced, follow the project’s lifecycle-management pattern.
- Confirm scheduled, async, or retry paths still behave correctly.

---

## Step 7: Verify storage and integration changes

- For database or storage changes, confirm whether migrations, compatibility shims, or fallback handling are required.
- Never rename or remove externally consumed fields without coordinated downstream changes.
- If the storage system is schema-less, still treat persisted field names and shapes as contracts once readers depend on them.

---

## Step 8: Write Unit Tests

- Create test file mirroring the source path.
- Cover: happy path, not-found, null inputs, edge cases, error conditions.
- Use the project's standard test framework and patterns.

---

## Step 9: Run and verify tests

Run the narrowest meaningful test set first, then broaden as the feature surface grows. Do not stop with known failing related tests.

---

## Step 10: Build and verify compilation

Run the relevant build, typecheck, packaging, or compilation steps for the affected backend surface.

---

## Checklist Before PR

- [ ] Logic lives in the correct service or application layer
- [ ] Input validation, error handling, and logging match project conventions
- [ ] Backward compatibility reviewed for changed contracts
- [ ] Required config, permissions, and docs updated
- [ ] Tests added or updated for the changed behavior
- [ ] Relevant validation commands pass
- [ ] No generated junk, secrets, or local-only artifacts are included

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
