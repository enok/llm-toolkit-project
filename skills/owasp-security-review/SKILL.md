---
name: "owasp-security-review"
description: "Run an OWASP-style application security review for Java, JavaScript, TypeScript, Node.js, Python, and React projects. Use when the user asks for an OWASP review, OWASP Top 10 assessment, AppSec audit, vulnerability report, or hardening findings document. Inspect access control, authentication, injection, secrets and crypto, dependency risk, SSRF, deserialization, XSS/CSRF, insecure configuration, and logging gaps, then generate a prioritized Markdown report with file and line evidence plus fix guidance. Do not trigger for general code review unless the request is explicitly security-focused."
---

# OWASP Security Review

Use this skill as the specialist engine behind the `security-report` workflow when the user wants a security-focused review framed as an OWASP audit or wants a written findings report for a Java, JavaScript, TypeScript, Node.js, Python, or React codebase.

## Workflow

1. Establish scope first.
   - Identify the target repo, the active stacks, the runtime boundaries, and whether the user wants audit-only output or audit-plus-fixes.
   - If the request is broad, start from the reachable app surfaces: auth, APIs, forms, uploads, background jobs, config, third-party calls, and dependency manifests.

2. Load the right guidance before making findings.
   - Read `references/owasp-top-10-review-map.md` if bundled.
   - Read the relevant sections of `references/stack-review-cues.md` for the active stack: Java, JavaScript, TypeScript, Node.js, Python, React.
   - Read `references/report-template.md` before writing the final report.
   - When you need cross-checks or fix guidance, merge this skill with `security`, `security-best-practices`, and the relevant language skill such as `java-best-practices`, `js-ts-best-practices`, `nodejs`, `python-best-practices`, or `react-best-practices`.

3. Audit the codebase through an OWASP lens.
   - Trace user-controlled input to storage, rendering, command execution, deserialization, outbound network calls, and privileged operations.
   - Inspect authentication, authorization, session or token handling, password reset flows, account recovery, role checks, and admin-only paths.
   - Inspect file upload, XML or YAML or JSON parsing, template rendering, DOM sinks, redirects, webhooks, and third-party integrations.
   - Inspect dependency manifests, lockfiles, secrets handling, build or CI scripts, and environment or deployment config when they affect attack surface.

4. Keep the findings bar high.
   - Prefer concrete, evidence-backed findings over speculative advice.
   - Separate confirmed findings from weaker observations or items needing runtime validation.
   - Include exploitability context and business impact, not just rule violations.
   - When evidence is incomplete, say that clearly instead of overstating certainty.

5. Write the report as a committed Markdown artifact unless the user asks otherwise.
   - Default path: `docs/security/<repo-or-dir-name>-security-report.md` when the repo already has or can reasonably host docs.
   - Fallback path if that is not appropriate: `<repo-or-dir-name>-security-report.md` at the repo root.
   - Every finding must include:
     - a stable finding ID
     - OWASP category mapping
     - severity
     - impacted files with line references
     - short exploit or impact statement
     - recommended fix direction
     - confidence or validation notes when applicable

6. If the user wants fixes, sequence them conservatively.
   - Start with the highest-risk confirmed findings.
   - Preserve behavior unless the security risk requires a breaking change.
   - Run the smallest relevant validation after each fix lane.
   - Update the report status as findings are fixed, deferred, or require broader design changes.

## Report Expectations

- Executive summary first.
- Group findings by severity.
- Map each finding to OWASP Top 10 categories where applicable.
- Include a short coverage section describing what was and was not inspected.
- Call out dependency or runtime checks you could not perform locally.
- End with prioritized next steps.

## Fix Boundaries

- Do not invent exploitability if you do not have evidence.
- Do not recommend disruptive controls like blanket CSP rewrites or auth redesigns without grounding them in the current app architecture.
- For frontend-only issues, distinguish clearly between true client risk and server-side enforcement gaps.
- For dependency findings, prefer precise package and version evidence over generic "update dependencies" advice.

## Related Skills

- **security** — general application security principles
- **security-best-practices** — language/framework-specific secure defaults
- **security-threat-model** — architectural threat modeling
- **java-best-practices**, **python-best-practices**, **js-ts-best-practices**, **nodejs** — language-specific fix guidance
