---
name: zoom-meeting-sdk
description: Secure defaults for embedding Zoom meetings with the Zoom Meeting SDK. This skill should be used when embedding or joining Zoom meetings inside a web application, implementing the server-side SDK JWT signature endpoint, wiring Zoom credentials, or debugging Meeting SDK join failures. Triggers on "embed zoom meeting", "meeting sdk", "zoom signature", "zoom join failed", "zoom sdk key", or adding Zoom to a webapp. Encodes auth/config defaults; pair with the security and testing skills.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# Zoom Meeting SDK - Secure Defaults

Secure guidance for embedding the Zoom Meeting SDK. This skill encodes auth, secret-handling, environment, and stack defaults so every Zoom integration starts consistent. Generic upstream Zoom knowledge (platform SDK details, samples) remains at https://developers.zoom.us/docs/meeting-sdk/.

## When to Apply

Reference these defaults when:
- Embedding a Zoom meeting join experience in a web application
- Implementing or reviewing the server-side SDK JWT signature endpoint
- Wiring Zoom SDK credentials into local, dev, stage, or prod environments
- Reviewing a PR that touches Zoom SDK init, join, or signature code
- Debugging join failures, signature errors, or waiting-room issues

## Hard Rules (Non-Negotiable)

1. **The SDK Secret never leaves the server.** No SDK Secret in frontend bundles, JSP/HTML, browser storage, logs, or git. Signatures are generated only by a backend endpoint. (See `skills/security/rules/secrets-no-hardcoded.md`.)
2. **No secrets or PII in logs.** Never log the signature, SDK Secret, or attendee names/emails. Log meeting number and correlation ID only. (See `skills/security/rules/logging-debug-redaction.md`.)
3. **Signature TTL defaults to 2 hours** (`exp = iat + 7200`), with `iat` backdated 30 seconds to absorb clock skew.
4. **Role is server-decided.** The client requests a join; the backend decides role 0 (attendee) vs 1 (host) from its own auth context. Never trust a role value posted from the browser.

## Credential And Environment Defaults

| Key | Purpose | Notes |
|-----|---------|-------|
| `ZOOM_MEETING_SDK_KEY` | SDK Key (Client ID) from Marketplace app | Safe to expose to the client with the signature response |
| `ZOOM_MEETING_SDK_SECRET` | SDK Secret used to sign the JWT | Server-side only, never logged |

Storage per environment (matches toolkit secret conventions):

| Environment | Store |
|-------------|-------|
| `local` | `.env` file (gitignored) |
| `dev` / `stage` / `prod` | Managed secret store, e.g. AWS Secrets Manager or SSM Parameter Store for AWS projects, with secret ID `<app>/zoom/meeting-sdk` loaded at startup |

Validate at startup and fail fast if either key is missing (see `skills/js-ts-best-practices/rules/resource-env-validation.md`; same principle applies to Java config wiring). Use separate Marketplace apps (separate key/secret pairs) for non-prod and prod.

## Backend Signature Endpoint (Default: Java / Spring MVC)

Default backend example: Java + Spring MVC with XML/Java DI, Log4j2/SLF4J, JUnit 4 + Mockito. Default pattern:

- Endpoint: `POST /api/zoom/signature` accepting `{ "meetingNumber": "..." }`
- Constructor-injected `ZoomSignatureService` behind an interface; register the controller in `spring-servlet.xml` (verify XML wiring; no broad component scanning)
- JWT: HS256 via `jjwt`; payload claims `sdkKey`/`appKey`, `mn` (digits only), `role`, `iat`, `exp`, `tokenExp`
- Response: `{ "signature": "...", "sdkKey": "..." }`
- Errors: invalid meeting number returns a safe 400 with structured log (no payload dump); follow the consuming repo's error-response conventions for client-facing endpoints

Full Java implementation, the Node.js variant for JS/TS services, and required tests: see `references/signature-service.md`.

### Testing expectations

Per the `testing` skill: JUnit 4 + Mockito tests must cover the happy path, meeting-number sanitization, role derivation (never from client input), expiry-window claims, and the missing-credential startup failure. Mock the clock via an injected interface; do not assert on wall time.

## Frontend Embed Defaults (Web)

Default choice: **Component View** (`@zoom/meetingsdk` via npm, `ZoomMtgEmbedded`, Promise-based) - it embeds in a div and coexists with the host app shell. Use **Client View** (CDN, `ZoomMtg`, full-page) only when a full-page takeover is explicitly acceptable.

Rules for either view:
- Fetch `{ signature, sdkKey }` from the backend endpoint at join time; never compute in the browser.
- No global CSS resets on pages hosting Zoom (`* { margin: 0 }` breaks Zoom UI); scope styles to the app container.
- For Client View in SPA-like pages, pin `#zmmtg-root` with high `z-index` and hide the app shell via a `meeting-active` body class.
- Display names passed to `join()` must come from the authenticated session, not free-text input, and must not be logged.

## Troubleshooting Order

1. Signature claims: decode the JWT (locally, never in prod logs) and check `sdkKey`, `mn` digits-only, `role`, `iat`/`exp` window.
2. Key mismatch: `sdkKey` in the signature must equal the key passed to `join()` and belong to the same Marketplace app/environment.
3. Clock skew: confirm `iat` backdating; server time drift breaks joins.
4. Waiting room / join-before-host: role 0 joins before host require meeting settings that allow it.
5. CSS/DOM conflicts (web): check global resets and z-index before blaming the SDK.

## Related Skills

- **security** - secrets handling, logging redaction (hard rules above derive from it)
- **java-best-practices** - DI, logging, and testing patterns for the signature service
- **js-ts-best-practices** - env validation and async patterns for Node variants and the frontend
- **testing** - AC traceability and coverage expectations for the endpoint

## References

- `references/signature-service.md` - full Java (Spring MVC) and Node.js signature endpoint implementations with tests
- Upstream docs: https://developers.zoom.us/docs/meeting-sdk/
