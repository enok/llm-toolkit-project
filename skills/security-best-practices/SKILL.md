---
name: "security-best-practices"
description: "Perform language and framework specific security best-practice reviews and suggest improvements. Trigger only when the user explicitly requests security best practices guidance, a security review/report, or secure-by-default coding help. Trigger only for supported languages (Python, JavaScript/TypeScript, Go, Java). Do not trigger for general code review, debugging, or non-security tasks."
---

# Security Best Practices

## Overview

This skill identifies the languages and frameworks used by the current context, then applies security best practices specific to those stacks. It can write new secure-by-default code, passively detect major issues while working, or produce a formal security report with prioritized findings and fix guidance.

If the user explicitly asks for an OWASP review, OWASP Top 10 assessment, or a formal security findings report, prefer `security-report` as the primary workflow entrypoint and use `owasp-security-review` plus this skill as supporting sources of OWASP coverage and stack-specific secure-default guidance.

## Workflow

The initial step is to identify ALL languages and ALL frameworks in scope. Focus on the primary core frameworks. Often you will want to identify both frontend and backend languages and frameworks.

Then check this skill's references directory (if available) for relevant documentation. The format of the filenames is `<language>-<framework>-<stack>-security.md`. Also check for `<language>-general-<stack>-security.md` which is agnostic to the specific framework.

If working on a web application with both frontend and backend, check reference documents for BOTH sides.

If no relevant reference material is available, apply well-known security best practices for the language and framework.

## Operating Modes

1. **Secure-by-default code** — Use the guidance to write secure code from this point forward. Useful when starting a new project or writing new code.

2. **Passive detection** — While working in the project, flag critical vulnerabilities or major security guidance violations. Focus on the highest-impact issues.

3. **Security report** — When explicitly asked, produce a full report describing where the project fails to follow security best practices. Prioritize by severity and urgency. Offer to work on fixes.

## Workflow Decision Tree

- If the language/framework is unclear, inspect the repo to determine it and list your evidence.
- If matching guidance exists in `references/`, load only the relevant files and follow their instructions.
- If no matching guidance exists, apply known best practices but note that concrete guidance is not available.

## Overrides

Projects may have cases where they need to bypass or override certain best practices. Pay attention to specific rules and instructions in the project's documentation and prompt files. When overriding a best practice, you MAY report it, but do not argue. Suggest adding documentation about the bypass.

## Report Format

When producing a formal security findings report, defer to the `security-report` workflow and the `owasp-security-review` output contract. Default to `docs/security/<repo-or-dir-name>-security-report.md`.

The report should have:
- Short executive summary at the top
- Sections delineated by severity
- Focus on the most critical findings
- Numeric IDs for all findings
- One sentence impact statement for critical findings
- Line numbers for all code references

After writing the report file, summarize the findings to the user and tell them where the report was written.

## Fixes

When producing fixes:
- Fix one finding at a time
- Add concise comments explaining the security best practice and why it matters
- Consider regressions — insecure code is often relied on for other reasons
- Follow the project's normal change and commit flow
- Run normal testing flows to confirm no regressions
- Inform the user of second-order impacts before making changes

## General Security Advice

### Avoid Using Incrementing IDs for Public Resource IDs

When assigning an ID for a resource exposed to the internet, avoid small auto-incrementing IDs. Use UUID4 or random hex strings instead to prevent enumeration.

### A Note on TLS

While TLS is important for production, most development work will be with TLS disabled or provided by a proxy. Be careful about reporting lack of TLS as a security issue. Also be careful with "secure" cookies — they should only be set if the application will actually be over TLS. Provide an env flag to override when needed. Avoid recommending HSTS without understanding the lasting impacts.

## Related Skills

- **security** — general application security principles
- **owasp-security-review** — OWASP-specific audit and findings report
- **security-threat-model** — architectural threat modeling
- **java-best-practices**, **python-best-practices**, **js-ts-best-practices**, **nodejs** — language-specific patterns
