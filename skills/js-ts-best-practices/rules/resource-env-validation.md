---
title: Validate Environment Variables at Startup
impact: LOW-MEDIUM
impactDescription: Fail fast with clear message instead of crashing hours later
tags: javascript, typescript, environment, zod, validation, startup
---

## Validate Environment Variables at Startup

Never access `process.env` directly throughout code. Validate once at startup with a schema.

**Incorrect (crash at runtime when first used, hours after deploy):**

```typescript
const dbUrl = process.env.DATABASE_URL;  // might be undefined
```

**Correct (validate at startup, fail fast):**

```typescript
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  NOTIFICATION_URL: z.string().url(),
  LOG_LEVEL: z.enum(["error", "warn", "info", "debug"]).default("info"),
  PORT: z.coerce.number().int().positive().default(3000),
});

export const env = envSchema.parse(process.env);
// Throws immediately on startup if any env var is missing/invalid
```

- Single source of truth for all env vars
- Type-safe access: `env.PORT` is `number`, not `string | undefined`
- Clear error messages on misconfiguration
