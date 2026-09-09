---
title: Zoom Meeting SDK signature service reference implementations
tags: [zoom, meeting-sdk, jwt, java, spring, nodejs, security]
---

# Zoom Meeting SDK Signature Service - Reference Implementations

Secure defaults: HS256 SDK JWT, 2-hour TTL, 30-second `iat` backdating, server-decided role, secrets from environment or a secret manager only. See `../SKILL.md` for the hard rules.

## JWT Payload (both stacks)

| Claim | Value |
|-------|-------|
| `sdkKey` / `appKey` | `ZOOM_MEETING_SDK_KEY` (set both for SDK version compatibility) |
| `mn` | Meeting number, digits only |
| `role` | 0 attendee / 1 host - derived server-side from the caller's auth context |
| `iat` | `now - 30s` |
| `exp` | `iat + 7200` |
| `tokenExp` | Same as `exp` |

## Java (Spring MVC) - Primary Stack

Dependency (`pom.xml`):

```xml
<dependency>
  <groupId>io.jsonwebtoken</groupId>
  <artifactId>jjwt-api</artifactId>
  <version>0.12.6</version>
</dependency>
<dependency>
  <groupId>io.jsonwebtoken</groupId>
  <artifactId>jjwt-impl</artifactId>
  <version>0.12.6</version>
  <scope>runtime</scope>
</dependency>
<dependency>
  <groupId>io.jsonwebtoken</groupId>
  <artifactId>jjwt-jackson</artifactId>
  <version>0.12.6</version>
  <scope>runtime</scope>
</dependency>
```

Service interface + implementation (constructor injection, injected clock for testability):

```java
public interface ZoomSignatureService {
    ZoomSignature createSignature(String meetingNumber, int role);
}

public class JwtZoomSignatureService implements ZoomSignatureService {

    private static final Logger LOG = LoggerFactory.getLogger(JwtZoomSignatureService.class);
    private static final long TTL_SECONDS = 7200L;
    private static final long CLOCK_SKEW_SECONDS = 30L;

    private final String sdkKey;
    private final SecretKey signingKey;
    private final Clock clock;

    public JwtZoomSignatureService(String sdkKey, String sdkSecret, Clock clock) {
        if (sdkKey == null || sdkKey.isEmpty() || sdkSecret == null || sdkSecret.isEmpty()) {
            // Fail fast at wiring time; never default silently.
            throw new IllegalStateException("Zoom Meeting SDK credentials are not configured");
        }
        this.sdkKey = sdkKey;
        this.signingKey = Keys.hmacShaKeyFor(sdkSecret.getBytes(StandardCharsets.UTF_8));
        this.clock = clock;
    }

    @Override
    public ZoomSignature createSignature(String meetingNumber, int role) {
        String mn = meetingNumber == null ? "" : meetingNumber.replaceAll("\\D", "");
        if (mn.isEmpty()) {
            throw new IllegalArgumentException("meetingNumber must contain digits");
        }
        long iat = clock.instant().getEpochSecond() - CLOCK_SKEW_SECONDS;
        long exp = iat + TTL_SECONDS;

        String jwt = Jwts.builder()
                .claim("sdkKey", sdkKey)
                .claim("appKey", sdkKey)
                .claim("mn", mn)
                .claim("role", role)
                .claim("iat", iat)
                .claim("exp", exp)
                .claim("tokenExp", exp)
                .signWith(signingKey, Jwts.SIG.HS256)
                .compact();

        // Structured, safe logging: no signature value, no attendee data.
        LOG.info("zoom_signature_issued mn={} role={} expEpoch={}", mn, role, exp);
        return new ZoomSignature(jwt, sdkKey);
    }
}
```

Controller (Spring MVC, registered in `spring-servlet.xml`; keep XML constructor args in sync):

```java
@Controller
public class ZoomSignatureController {

    private final ZoomSignatureService signatureService;

    public ZoomSignatureController(ZoomSignatureService signatureService) {
        this.signatureService = signatureService;
    }

    @RequestMapping(value = "/api/zoom/signature", method = RequestMethod.POST)
    @ResponseBody
    public ResponseEntity<?> signature(@RequestBody ZoomSignatureRequest request,
                                       HttpServletRequest httpRequest) {
        // Role is derived from server-side auth context, never from the request body.
        int role = resolveRoleFromSession(httpRequest);
        try {
            ZoomSignature sig = signatureService.createSignature(request.getMeetingNumber(), role);
            return ResponseEntity.ok(sig);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                    .body(Collections.singletonMap("error", "invalid meetingNumber"));
        }
    }
}
```

XML wiring sketch (`spring-servlet.xml`):

```xml
<bean id="zoomSignatureService" class="com.example.zoom.JwtZoomSignatureService">
    <constructor-arg value="${ZOOM_MEETING_SDK_KEY}"/>
    <constructor-arg value="${ZOOM_MEETING_SDK_SECRET}"/>
    <constructor-arg ref="systemUtcClock"/>
</bean>
<bean id="zoomSignatureController" class="com.example.zoom.ZoomSignatureController">
    <constructor-arg ref="zoomSignatureService"/>
</bean>
```

In deployed environments, resolve `${ZOOM_MEETING_SDK_SECRET}` from AWS Secrets Manager, SSM Parameter Store, or the destination project's secret manager at startup (property source or bootstrap loader) - never from a committed properties file.

### Required JUnit 4 + Mockito coverage

- Happy path: digits-only `mn`, `role` claim present, `exp - iat == 7200`, `iat` backdated 30s (fixed `Clock`)
- Sanitization: `"123-456-7890"` -> `mn=1234567890`; empty/non-digit input -> `IllegalArgumentException` -> 400
- Role: client-supplied role in the body is ignored; role comes from session resolution
- Wiring failure: missing key or secret throws `IllegalStateException` at construction
- No secret leakage: assert log/capture output contains no signature or secret material

## Node.js Variant (for JS/TS services)

```javascript
// zoomSignature.js - validate env at startup, fail fast (resource-env-validation)
const { SignJWT } = require('jose');

const SDK_KEY = requireEnv('ZOOM_MEETING_SDK_KEY');
const SDK_SECRET = requireEnv('ZOOM_MEETING_SDK_SECRET');
const secret = new TextEncoder().encode(SDK_SECRET);

async function createSignature(meetingNumber, role) {
  const mn = String(meetingNumber ?? '').replace(/\D/g, '');
  if (!mn) throw new InvalidMeetingNumberError();
  const iat = Math.floor(Date.now() / 1000) - 30;
  const exp = iat + 7200;
  const signature = await new SignJWT({ sdkKey: SDK_KEY, appKey: SDK_KEY, mn, role, iat, exp, tokenExp: exp })
    .setProtectedHeader({ alg: 'HS256', typ: 'JWT' })
    .sign(secret);
  return { signature, sdkKey: SDK_KEY };
}
```

Route handler: derive `role` from the authenticated session, return 400 on `InvalidMeetingNumberError`, and log only `{ mn, role, exp }` via the structured logger (`logging-structured`, `logging-no-secrets`).

## Frontend Consumption (Component View default)

```javascript
import ZoomMtgEmbedded from '@zoom/meetingsdk/embedded';

const client = ZoomMtgEmbedded.createClient();
await client.init({ zoomAppRoot: document.getElementById('zoom-container'), language: 'en-US' });

const res = await fetch('/api/zoom/signature', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ meetingNumber }),
});
const { signature, sdkKey } = await res.json();

await client.join({
  sdkKey,
  signature,
  meetingNumber,
  userName: sessionDisplayName, // from authenticated session, never free text
  password: meetingPasscode,
});
```
