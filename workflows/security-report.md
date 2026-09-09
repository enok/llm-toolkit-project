---
description: OWASP-aligned security review with parallel audit lanes and a single synthesized report
---

# Security report workflow

Use when the user asks for a security report, OWASP-style audit, AppSec review, or vulnerability assessment. Pair with the **security** skill and `rubrics/security.md`. For OWASP-framed audits, use `skills/owasp-security-review/SKILL.md` as the specialist engine and `skills/security-best-practices/SKILL.md` for stack-specific secure defaults.

## Phase 1 — Scope

1. Determine the review surface: repo root, diff, service, frontend, backend, or specific path.
2. Identify runtime components, public entrypoints, trust boundaries, and the active stack.
3. Choose the lens: OWASP Top 10, API Top 10, ASVS, or a mixed review as appropriate.

## Phase 2 — Parallel inspection by default

4. Once scope is known, split independent audit lanes **immediately by default**:
   - authentication, authorization, and trust boundaries
   - injection, file handling, deserialization, and outbound calls
   - secrets, dependencies, config exposure, and operational hardening
   - frontend risks such as XSS, token handling, and client trust
   - shared libraries and type-safety or boundary gaps
5. Do not pause before internal fanout unless there is a user-visible tradeoff or risky external side effect.

## Phase 3 — Synthesize

6. Merge lanes into one report with severity, OWASP mapping, evidence, impact, and remediation.
7. Separate confirmed findings from assumption-backed risks and open questions.
8. Write the report where the user requests; default to the canonical path from `owasp-security-review` (`docs/security/<repo-or-dir-name>-security-report.md`), using clear severity labels and file references.

See `rules/multi-agent-orchestration.md`.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
