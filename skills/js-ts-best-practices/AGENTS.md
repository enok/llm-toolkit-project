# JavaScript / TypeScript Best Practices

Language-specific best practices for JavaScript and TypeScript projects. These apply to any JS/TS codebase regardless of framework — Node.js backends, full-stack apps, serverless functions, CLI tools, etc.

## Type Safety

### Strict TypeScript Configuration

Always enable strict mode and additional safety flags:

```jsonc
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  }
}
```

- `strict: true` enables `strictNullChecks`, `noImplicitAny`, `strictFunctionTypes`, etc.
- `noUncheckedIndexedAccess` — array/object index returns `T | undefined`, preventing silent undefined access.
- `exactOptionalPropertyTypes` — `{ name?: string }` means `string | undefined`, not `string | undefined | missing`.

### Never Use `any`

```typescript
// WRONG — defeats the type system entirely
function process(data: any): any {
  return data.items.map((item: any) => item.name);
}

// CORRECT — use unknown + narrowing
function process(data: unknown): string[] {
  if (!isValidResponse(data)) {
    throw new ValidationError("Invalid response shape");
  }
  return data.items.map((item) => item.name);
}

// CORRECT — use generics when the type varies
function identity<T>(value: T): T {
  return value;
}
```

- Use `unknown` for values of uncertain type, then narrow with type guards.
- Use generics when the function works with any type parametrically.
- Use `as` type assertions only when you've verified the type externally (e.g., after JSON schema validation).

### Discriminated Unions and Type Narrowing

```typescript
// WRONG — string status with no exhaustiveness checking
interface ApiResponse {
  status: string;
  data?: unknown;
  error?: string;
}

// CORRECT — discriminated union with exhaustive matching
type ApiResponse =
  | { status: "success"; data: OrderData }
  | { status: "error"; error: string; statusCode: number }
  | { status: "loading" };

function handleResponse(response: ApiResponse): string {
  switch (response.status) {
    case "success":
      return response.data.orderId;  // TS knows data exists
    case "error":
      throw new AppError(response.error, response.statusCode);
    case "loading":
      return "Loading...";
    default:
      const _exhaustive: never = response;  // compile error if case missed
      throw new Error(`Unhandled status: ${_exhaustive}`);
  }
}
```

### Readonly and Immutable Types

```typescript
// WRONG — mutable object, caller can corrupt it
function getConfig(): Config {
  return { timeout: 3000, retries: 3 };
}
const config = getConfig();
config.timeout = 0;  // silent mutation

// CORRECT — readonly prevents mutation
function getConfig(): Readonly<Config> {
  return { timeout: 3000, retries: 3 } as const;
}
const config = getConfig();
config.timeout = 0;  // TS compile error

// CORRECT — readonly arrays
function getIds(): ReadonlyArray<string> {
  return ["a", "b", "c"];
}
const ids = getIds();
ids.push("d");  // TS compile error
```

### Branded Types for Domain IDs

```typescript
// WRONG — string IDs are interchangeable, easy to mix up
function getOrder(orderId: string, userId: string): Order { ... }
getOrder(userId, orderId);  // compiles fine, but WRONG — args swapped

// CORRECT — branded types prevent mixups at compile time
type OrderId = string & { readonly __brand: "OrderId" };
type UserId = string & { readonly __brand: "UserId" };

function orderId(id: string): OrderId { return id as OrderId; }
function userId(id: string): UserId { return id as UserId; }

function getOrder(orderId: OrderId, userId: UserId): Order { ... }
getOrder(userId("u-1"), orderId("o-1"));  // TS compile error — types don't match
```

## Async & Concurrency

### Promise.all() for Independent Operations

```typescript
// WRONG — sequential, 3 round trips
const user = await fetchUser(id);
const orders = await fetchOrders(id);
const preferences = await fetchPreferences(id);

// CORRECT — parallel, 1 round trip
const [user, orders, preferences] = await Promise.all([
  fetchUser(id),
  fetchOrders(id),
  fetchPreferences(id),
]);

// CORRECT — fault-tolerant (some may fail, others succeed)
const results = await Promise.allSettled([
  fetchUser(id),
  fetchOrders(id),
  fetchPreferences(id),
]);
const succeeded = results.filter(r => r.status === "fulfilled").map(r => r.value);
const failed = results.filter(r => r.status === "rejected").map(r => r.reason);
```

### Never Fire-and-Forget Async Calls

```typescript
// WRONG — unhandled rejection will crash Node.js
app.post("/orders", (req, res) => {
  processOrder(req.body);  // missing await — error is silently lost
  res.send("OK");
});

// CORRECT — await and handle errors
app.post("/orders", async (req, res, next) => {
  try {
    await processOrder(req.body);
    res.send("OK");
  } catch (error) {
    next(error);
  }
});

// CORRECT — if intentionally fire-and-forget, explicitly catch
void sendAnalytics(event).catch((err) =>
  logger.warn("Analytics failed: %s", err.message)
);
```

### Race Conditions: Shared Mutable State Across Async Boundaries

JavaScript is single-threaded but NOT free of race conditions. Async operations interleave at `await` points.

```typescript
// WRONG — race condition. Two concurrent requests can both read balance=100,
// both deduct 60, and write 40. One deduction lost.
let balance = 100;

async function debit(amount: number): Promise<void> {
  const current = balance;          // read
  await verifyFunds(current);       // yield — another call can interleave here
  balance = current - amount;       // write stale value
}

// CORRECT — use a mutex/lock for async critical sections
import { Mutex } from "async-mutex";
const balanceMutex = new Mutex();

async function debit(amount: number): Promise<void> {
  const release = await balanceMutex.acquire();
  try {
    await verifyFunds(balance);
    balance -= amount;
  } finally {
    release();
  }
}
```

**Key insight:** Every `await` is a potential interleave point. If shared mutable state is read before an `await` and written after, another async operation can modify it in between.

### AbortController for Cancellation and Timeouts

```typescript
// WRONG — no timeout, no cancellation
const response = await fetch(url);

// CORRECT — timeout with AbortController
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 5000);

try {
  const response = await fetch(url, { signal: controller.signal });
  return await response.json();
} catch (error) {
  if (error instanceof DOMException && error.name === "AbortError") {
    throw new TimeoutError(`Request to ${url} timed out after 5s`);
  }
  throw error;
} finally {
  clearTimeout(timeoutId);
}
```

### Never Block the Event Loop

```typescript
// WRONG — blocks event loop, all other requests stall
app.get("/hash", (req, res) => {
  const hash = crypto.pbkdf2Sync(password, salt, 100000, 64, "sha512");
  res.send(hash);
});

// CORRECT — offload to worker thread
import { Worker } from "worker_threads";

app.get("/hash", async (req, res) => {
  const hash = await runInWorker("./hash-worker.js", { password, salt });
  res.send(hash);
});

// CORRECT — use async version if available
import { pbkdf2 } from "crypto";
import { promisify } from "util";
const pbkdf2Async = promisify(pbkdf2);

app.get("/hash", async (req, res) => {
  const hash = await pbkdf2Async(password, salt, 100000, 64, "sha512");
  res.send(hash);
});
```

## Error Handling

### Custom Error Classes with Context

```typescript
// WRONG — plain Error with no structured metadata
throw new Error("Order not found");

// CORRECT — custom error with typed properties
class AppError extends Error {
  constructor(
    message: string,
    public readonly statusCode: number,
    public readonly context?: Record<string, unknown>,
    public readonly isOperational = true,
  ) {
    super(message);
    this.name = this.constructor.name;
    Error.captureStackTrace?.(this, this.constructor);
  }
}

class NotFoundError extends AppError {
  constructor(resource: string, id: string) {
    super(`${resource} not found: ${id}`, 404, { resource, id });
  }
}

class ValidationError extends AppError {
  constructor(message: string, public readonly fields: string[]) {
    super(message, 400, { fields });
  }
}

// Usage
throw new NotFoundError("Order", orderId);
```

### Result Pattern for Expected Failures

```typescript
// Instead of try/catch for expected outcomes, use a Result type
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };

function parseConfig(raw: string): Result<Config, ValidationError> {
  try {
    const parsed = JSON.parse(raw);
    if (!isValidConfig(parsed)) {
      return { ok: false, error: new ValidationError("Invalid config shape", []) };
    }
    return { ok: true, value: parsed };
  } catch {
    return { ok: false, error: new ValidationError("Invalid JSON", []) };
  }
}

// Caller handles both paths explicitly — no surprise exceptions
const result = parseConfig(rawInput);
if (!result.ok) {
  logger.warn("Config parse failed: %s", result.error.message);
  return defaultConfig;
}
return result.value;
```

### Exhaustive Error Handling

```typescript
// WRONG — catch-all hides bugs
try {
  await processOrder(order);
} catch (e) {
  res.status(500).send("Something went wrong");
}

// CORRECT — handle specific error types
try {
  await processOrder(order);
} catch (error) {
  if (error instanceof ValidationError) {
    res.status(400).json({ error: error.message, fields: error.fields });
  } else if (error instanceof NotFoundError) {
    res.status(404).json({ error: error.message });
  } else if (error instanceof AppError && error.isOperational) {
    res.status(error.statusCode).json({ error: error.message });
  } else {
    logger.error("Unexpected error in processOrder: %O", error);
    res.status(500).json({ error: "Internal server error" });
  }
}
```

## Dependency Injection (DI) — The Core Principle

**The Rule:** Every class/module receives its external collaborators as interfaces through the constructor. The composition root is the only place that knows which concrete implementation to use.

### Full Example

```typescript
// 1. INTERFACE — defines the contract. Lives in the service/domain layer.
interface OrderRepository {
  findByUserId(userId: string): Promise<Order | null>;
  save(order: Order): Promise<void>;
}

interface NotificationClient {
  sendOrderConfirmation(order: Order): Promise<void>;
}

// 2. IMPLEMENTATION — lives in the infrastructure layer. Knows about DynamoDB.
class DynamoDbOrderRepository implements OrderRepository {
  constructor(private readonly client: DynamoDBDocumentClient) {}

  async findByUserId(userId: string): Promise<Order | null> {
    const result = await this.client.send(
      new GetCommand({ TableName: "orders", Key: { userId } })
    );
    return (result.Item as Order) ?? null;
  }

  async save(order: Order): Promise<void> {
    await this.client.send(
      new PutCommand({ TableName: "orders", Item: order })
    );
  }
}

// 3. SERVICE — depends ONLY on interfaces. Knows nothing about DynamoDB, HTTP, etc.
class OrderService {
  constructor(
    private readonly orderRepo: OrderRepository,
    private readonly notificationClient: NotificationClient,
  ) {}

  async placeOrder(order: Order): Promise<void> {
    this.validateOrder(order);
    await this.orderRepo.save(order);
    await this.notificationClient.sendOrderConfirmation(order);
  }
}

// 4. COMPOSITION ROOT — the ONLY place that knows which implementation to use.
// NestJS example:
@Module({
  providers: [
    { provide: "OrderRepository", useClass: DynamoDbOrderRepository },
    { provide: "NotificationClient", useClass: HttpNotificationClient },
    OrderService,
  ],
})
export class AppModule {}

// Plain factory example:
function createOrderService(): OrderService {
  const dynamoClient = DynamoDBDocumentClient.from(new DynamoDBClient({}));
  const repo = new DynamoDbOrderRepository(dynamoClient);
  const notifier = new HttpNotificationClient(process.env.NOTIFICATION_URL!);
  return new OrderService(repo, notifier);
}

// 5. TEST — trivial to mock, no framework needed.
describe("OrderService", () => {
  it("saves and notifies on placeOrder", async () => {
    const mockRepo: OrderRepository = {
      findByUserId: vi.fn(),
      save: vi.fn().mockResolvedValue(undefined),
    };
    const mockNotifier: NotificationClient = {
      sendOrderConfirmation: vi.fn().mockResolvedValue(undefined),
    };
    const service = new OrderService(mockRepo, mockNotifier);

    await service.placeOrder(testOrder);

    expect(mockRepo.save).toHaveBeenCalledWith(testOrder);
    expect(mockNotifier.sendOrderConfirmation).toHaveBeenCalledWith(testOrder);
  });
});
```

### Anti-Patterns

```typescript
// ANTI-PATTERN 1: Importing concrete implementation in service code
import { DynamoDbOrderRepository } from "../infra/dynamo-repo";
class OrderService {
  private repo = new DynamoDbOrderRepository();  // tightly coupled, untestable
}

// ANTI-PATTERN 2: Module-level singletons as hidden dependencies
const repo = new DynamoDbOrderRepository();
export function placeOrder(order: Order) {
  repo.save(order);  // hidden dependency, hard to test
}

// ANTI-PATTERN 3: Barrel file re-exports that couple everything
// index.ts that re-exports all concrete implementations
export { DynamoDbOrderRepository } from "./dynamo-repo";
export { HttpNotificationClient } from "./http-notifier";
// Now every consumer imports concrete classes
```

## Language Fundamentals

### Prefer Immutability

```typescript
// WRONG — mutable, error-prone
const config = { timeout: 3000, retries: 3 };
config.timeout = 0;  // silent mutation somewhere else

const ids: string[] = ["a", "b"];
ids.push("c");  // mutates in place

// CORRECT — immutable
const config = { timeout: 3000, retries: 3 } as const;
config.timeout = 0;  // TS compile error

const ids: readonly string[] = ["a", "b"];
ids.push("c");  // TS compile error

// For objects that need to change, create new copies
const newConfig = { ...config, timeout: 5000 };
const newIds = [...ids, "c"];
```

### Nullish Coalescing and Optional Chaining

```typescript
// WRONG — falsy check catches 0, "", false
const timeout = config.timeout || 3000;  // 0 is a valid timeout, but this returns 3000

// CORRECT — nullish coalescing only catches null/undefined
const timeout = config.timeout ?? 3000;  // 0 stays as 0

// WRONG — verbose null checking
if (user && user.address && user.address.city) {
  return user.address.city;
}

// CORRECT — optional chaining
return user?.address?.city;
```

### Guard Clauses (Early Return)

```typescript
// WRONG — deeply nested conditions
function processOrder(order: Order | null): Result {
  if (order) {
    if (order.items.length > 0) {
      if (order.status === "pending") {
        return doProcess(order);
      } else {
        throw new ValidationError("Order not pending");
      }
    } else {
      throw new ValidationError("Order has no items");
    }
  } else {
    throw new ValidationError("Order is null");
  }
}

// CORRECT — guard clauses, flat structure
function processOrder(order: Order | null): Result {
  if (!order) throw new ValidationError("Order is null");
  if (order.items.length === 0) throw new ValidationError("Order has no items");
  if (order.status !== "pending") throw new ValidationError("Order not pending");

  return doProcess(order);
}
```

### Use Map/Set for O(1) Lookups

```typescript
// WRONG — O(n²)
for (const order of orders) {
  const user = users.find((u) => u.id === order.userId);  // O(n) per order
}

// CORRECT — O(n) total
const userById = new Map(users.map((u) => [u.id, u]));
for (const order of orders) {
  const user = userById.get(order.userId);  // O(1) per order
}
```

## Logging

### Structured JSON Logging

```typescript
// WRONG — console.log with string concatenation
console.log("Processing order " + orderId + " for user " + userId);

// CORRECT — structured logger with context
import pino from "pino";
const logger = pino({ level: process.env.LOG_LEVEL ?? "info" });

logger.info({ orderId, userId, itemCount: order.items.length }, "Processing order");
logger.error({ orderId, err }, "Order processing failed");
```

- Use `pino` (fastest) or `winston` for structured JSON logs.
- Include correlation IDs (requestId) in every log line via async context or middleware.
- Appropriate levels: `error` (action needed), `warn` (concerning), `info` (milestones), `debug` (diagnostics).
- Never log tokens, PII, or full request/response bodies in production.

### Correlation IDs

```typescript
import { AsyncLocalStorage } from "async_hooks";

const asyncLocalStorage = new AsyncLocalStorage<{ requestId: string }>();

// Middleware — set at request boundary
app.use((req, res, next) => {
  const requestId = req.headers["x-request-id"] as string ?? crypto.randomUUID();
  asyncLocalStorage.run({ requestId }, () => next());
});

// Logger — automatically includes requestId
const logger = pino({
  mixin() {
    const store = asyncLocalStorage.getStore();
    return store ? { requestId: store.requestId } : {};
  },
});
```

## Testing

### Mock at the Interface Boundary

```typescript
// WRONG — mocking module internals (fragile, coupled to implementation)
vi.mock("@aws-sdk/client-dynamodb", () => ({
  DynamoDBClient: vi.fn().mockImplementation(() => ({
    send: vi.fn().mockResolvedValue({ Item: testOrder }),
  })),
}));

// CORRECT — mock the interface (clean, survives implementation changes)
const mockRepo: OrderRepository = {
  findByUserId: vi.fn().mockResolvedValue(testOrder),
  save: vi.fn().mockResolvedValue(undefined),
};
const service = new OrderService(mockRepo, mockNotifier);
```

### Async Test Patterns

```typescript
// WRONG — assertion runs before async completes
it("should save order", () => {
  service.placeOrder(order);
  expect(mockRepo.save).toHaveBeenCalled();  // may fail — not awaited
});

// CORRECT — await the async operation
it("should save order", async () => {
  await service.placeOrder(order);
  expect(mockRepo.save).toHaveBeenCalledWith(order);
});

// CORRECT — test async errors
it("should throw on invalid order", async () => {
  await expect(service.placeOrder(invalidOrder)).rejects.toThrow(ValidationError);
});
```

### Arrange-Act-Assert Structure

```typescript
describe("OrderService", () => {
  // Arrange (shared)
  let service: OrderService;
  let mockRepo: OrderRepository;

  beforeEach(() => {
    mockRepo = { findByUserId: vi.fn(), save: vi.fn().mockResolvedValue(undefined) };
    const mockNotifier = { sendOrderConfirmation: vi.fn().mockResolvedValue(undefined) };
    service = new OrderService(mockRepo, mockNotifier);
  });

  it("saves and notifies on placeOrder", async () => {
    // Arrange
    const order = buildTestOrder();

    // Act
    await service.placeOrder(order);

    // Assert
    expect(mockRepo.save).toHaveBeenCalledWith(order);
  });
});
```

## External Resource Access

### HTTP Client Reuse and Timeouts

```typescript
// WRONG — no timeout, no reuse
const response = await fetch(`https://api.example.com/data/${id}`);

// CORRECT — reusable client with timeouts and retries
import axios from "axios";

const apiClient = axios.create({
  baseURL: "https://api.example.com",
  timeout: 5000,
  headers: { "Content-Type": "application/json" },
});

// Or with native fetch + AbortController
async function fetchWithTimeout(url: string, timeoutMs = 5000): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { signal: controller.signal });
  } finally {
    clearTimeout(timeoutId);
  }
}
```

### Environment Variable Validation at Startup

```typescript
// WRONG — crash at runtime when first used, hours after deploy
const dbUrl = process.env.DATABASE_URL;  // might be undefined

// CORRECT — validate at startup, fail fast with clear message
import { z } from "zod";

const envSchema = z.object({
  DATABASE_URL: z.string().url(),
  NOTIFICATION_URL: z.string().url(),
  LOG_LEVEL: z.enum(["error", "warn", "info", "debug"]).default("info"),
  PORT: z.coerce.number().int().positive().default(3000),
});

export const env = envSchema.parse(process.env);
// Throws immediately on startup with clear validation error if any env var is missing/invalid
```

### Connection Pooling

```typescript
// WRONG — new connection per query
async function getUser(id: string) {
  const client = new Client(process.env.DATABASE_URL);
  await client.connect();
  const result = await client.query("SELECT * FROM users WHERE id = $1", [id]);
  await client.end();
  return result.rows[0];
}

// CORRECT — connection pool, reused across requests
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

async function getUser(id: string) {
  const result = await pool.query("SELECT * FROM users WHERE id = $1", [id]);
  return result.rows[0];
}
```

## Concurrency

### Race Conditions in Single-Threaded JS

JavaScript's event loop is single-threaded but concurrent. Every `await` yields control, creating interleave points.

```typescript
// WRONG — stale read across await boundary
let cache: Map<string, Data> = new Map();

async function getOrFetch(key: string): Promise<Data> {
  if (cache.has(key)) return cache.get(key)!;
  const data = await fetchFromApi(key);  // another call with same key can enter here
  cache.set(key, data);  // both calls set — wasted work, possible inconsistency
  return data;
}

// CORRECT — deduplication with in-flight promise tracking
const inFlight = new Map<string, Promise<Data>>();

async function getOrFetch(key: string): Promise<Data> {
  if (cache.has(key)) return cache.get(key)!;
  if (inFlight.has(key)) return inFlight.get(key)!;

  const promise = fetchFromApi(key).then((data) => {
    cache.set(key, data);
    inFlight.delete(key);
    return data;
  });
  inFlight.set(key, promise);
  return promise;
}
```

### Common Concurrency Pitfalls

| Pitfall | Example | Fix |
|---------|---------|-----|
| **Stale read across await** | Read → await → write on shared state | Mutex (`async-mutex`) or dedup map |
| **Fire-and-forget** | `processAsync()` without await | `await` or explicit `.catch()` |
| **Unhandled rejection** | Missing `.catch()` on promise chain | Global handler + local catches |
| **Event loop blocking** | `JSON.parse(hugeString)` in request handler | Worker thread or streaming parser |
| **Concurrent cache writes** | Two requests fetch + write same cache key | In-flight promise dedup |
| **forEach with async** | `array.forEach(async (item) => ...)` | `Promise.all(array.map(...))` or `for...of` |

## Security

- **Never log** secrets, tokens, PII, or full request payloads in production.
- **Validate all inputs** with a schema library (zod, joi, ajv) — never trust `req.body` or `req.params`.
- **Parameterize queries** — never concatenate user input into SQL or NoSQL expressions.
- **Pin dependencies** in `package-lock.json` — run `npm audit` regularly.
- **Use `helmet`** for Express to set security headers.
- **Sanitize error messages** returned to clients — never expose stack traces or internal details.

> For comprehensive security guidance (injection, auth, XSS/CSRF/SSRF, secrets, PII, threat modeling), see the **security** skill.
> For Node.js-specific hardening (helmet, rate limiting, CORS, cookies, trust proxy), see the **nodejs** skill.

## Related Skills

- **nodejs** — Node.js runtime: process lifecycle, Express/Fastify middleware, streams, Docker deployment (runtime companion to this language-level skill)
- **react-best-practices** — React/Next.js performance optimization (frontend companion)
- **best-practices** — SOLID principles, layered architecture, resilience patterns (language-agnostic foundations)
- **security** — Comprehensive injection prevention, auth, secrets, XSS/CSRF/SSRF, PII rules
- **testing** — AC-to-test traceability, test pyramid, coverage checklist (universal testing discipline)
