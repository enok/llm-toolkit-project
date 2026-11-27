# Architecture Rubric

Severity calls for architecture findings that reviewers tend to over-escalate. Severity levels: **Blocker** must be fixed before merge;
**Suggestion** should be addressed but can be deferred with explicit justification.

---

## Suggestion, not Blocker

| Signal | Severity | Why |
|--------|----------|-----|
| Abstraction/interface with a single implementation and no anticipated variation (e.g. one `Notifier`) | Suggestion - simplify | Extra indirection, no correctness or safety risk |
| Non-idempotent GET or DELETE (a GET that mutates state) | Suggestion | Contract smell to fix, but deferrable; escalate only if it causes data loss or a security hole |
