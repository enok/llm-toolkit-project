# Java Best Practices

Language-specific best practices for Java projects. These apply to any Java codebase regardless of framework.

## Language Fundamentals

### Prefer Immutability
```java
// WRONG — mutable, error-prone
public class User {
    public String name;
    public List<String> roles;
}

// CORRECT — immutable, safe
public final class User {
    private final String name;
    private final List<String> roles;

    public User(String name, List<String> roles) {
        this.name = Objects.requireNonNull(name);
        this.roles = List.copyOf(roles); // defensive copy + unmodifiable
    }

    public String getName() { return name; }
    public List<String> getRoles() { return roles; }
}
```
- Use `final` fields wherever possible.
- Return unmodifiable collections from getters (`Collections.unmodifiableList()` or `List.copyOf()`).
- Prefer `List.of()`, `Map.of()`, `Set.of()` for small immutable collections.

### Null Safety
```java
// WRONG — NPE waiting to happen
String value = map.get(key).toString();

// CORRECT — defensive
String value = Optional.ofNullable(map.get(key))
    .map(Object::toString)
    .orElse("default");

// CORRECT — fail fast with clear message
Objects.requireNonNull(dependency, "dependency must not be null");
```
- Use `Objects.requireNonNull()` in constructors for mandatory dependencies.
- Use `Optional` for return types that may be absent — never for fields or parameters.
- Prefer `isEmpty()` over `size() == 0`. Prefer `isBlank()` over `trim().isEmpty()` (Java 11+).

### String Handling
```java
// WRONG — string concatenation in loops
String result = "";
for (String s : items) { result += s + ","; }

// CORRECT — StringBuilder or joining
String result = String.join(",", items);
String result = items.stream().collect(Collectors.joining(","));
```
- Never use `==` for String comparison — always `.equals()` or `Objects.equals()`.
- Use `String.format()` or `MessageFormat` for complex string building, not `+` chains.

### Collections
- Declare variables using interface types: `List<>`, `Map<>`, `Set<>` — not `ArrayList<>`, `HashMap<>`.
- Use diamond operator: `new ArrayList<>()` not `new ArrayList<String>()`.
- Prefer `isEmpty()` over `size() == 0`.
- Use `Map.getOrDefault()`, `Map.computeIfAbsent()` instead of manual null checks.
- Never modify a collection while iterating — use `Iterator.remove()` or stream-filter-collect.

### Method Design

- **Keep methods small** — a method should do one thing. If you need a comment to explain a block of code inside a method, extract it into a named helper method.
- **Target 10–20 lines per method**. Methods over 30 lines are a strong signal to refactor.
- **One level of abstraction per method** — don't mix high-level orchestration with low-level details in the same method.

```java
// WRONG — does too many things, hard to test individual parts
public void processOrder(Order order) {
    // validate
    if (order.getItems().isEmpty()) throw new ValidationException("No items");
    if (order.getTotal().compareTo(BigDecimal.ZERO) <= 0) throw new ValidationException("Invalid total");
    // calculate discount
    BigDecimal discount = BigDecimal.ZERO;
    for (Item item : order.getItems()) {
        if (item.isOnSale()) discount = discount.add(item.getDiscount());
    }
    // persist
    order.setDiscount(discount);
    orderRepository.save(order);
    // notify
    emailService.sendConfirmation(order);
}

// CORRECT — each method does one thing, independently testable
public void processOrder(Order order) {
    validateOrder(order);
    BigDecimal discount = calculateDiscount(order.getItems());
    order.setDiscount(discount);
    orderRepository.save(order);
    emailService.sendConfirmation(order);
}
```

- **Extract early returns** for validation (guard clauses) — reduces nesting.
- **Boolean method parameters are a code smell** — prefer two clearly named methods or an enum.

### Algorithmic Complexity

- **Avoid nested loops over collections** — `O(n²)` or worse. Use a `Map` or `Set` for lookup instead.

```java
// WRONG — O(n²), scans activeUsers for every order
for (Order order : orders) {
    for (User user : activeUsers) {
        if (user.getId().equals(order.getUserId())) { /* match */ }
    }
}

// CORRECT — O(n), build lookup map first
Map<String, User> userById = activeUsers.stream()
    .collect(Collectors.toMap(User::getId, Function.identity()));
for (Order order : orders) {
    User user = userById.get(order.getUserId());
    if (user != null) { /* match */ }
}
```

- **Three levels of nesting is a red flag** — extract inner loops into named methods.
- **Use `Set.contains()` for membership checks** — `O(1)` vs `List.contains()` at `O(n)`.
- **Batch external calls** — never call a database or HTTP API inside a loop. Collect IDs, batch-fetch, then process.

### Exception Handling
```java
// WRONG — catch-all, swallowed
try { riskyOperation(); }
catch (Exception e) { /* ignore */ }

// WRONG — catching too broadly, no context
try { parseInput(data); }
catch (Exception e) { log.error("Failed", e); }

// CORRECT — specific, contextual, preserves cause
try { parseInput(data); }
catch (NumberFormatException e) {
    throw new ValidationException("Invalid numeric input: " + data, e);
}
```
- Catch the most specific exception type.
- Always preserve the cause chain (`throw new XException(msg, cause)`).
- Never use exceptions for control flow.
- Clean up resources with try-with-resources (not `finally` blocks).
- Custom exceptions should extend `RuntimeException` unless callers must handle them.

### Logging Exceptions with Context

When logging an exception, the error message should include enough context to diagnose the issue **without** reading the full stack trace:

```java
// WRONG — no business context, useless in CloudWatch
log.error("Operation failed", e);

// CORRECT — business context + root cause summary + full exception
log.error(
    String.format("DynamoDB retrieval failed for requestId %s [root cause: %s]",
        requestId, ExceptionUtils.getRootCauseMessage(e)),
    e);
```

**Pattern**: `log.error(String.format("What failed for key=%s [root cause: %s]", key, ExceptionUtils.getRootCauseMessage(e)), e)`


- **First arg** (`String`): Human-readable message with business context (IDs, operation name) and the root cause message.
- **Second arg** (`Throwable`): The full exception — the logging framework prints the stack trace.
- Use `ExceptionUtils.getRootCauseMessage(e)` (Apache Commons Lang) to include the root cause in the message text for quick log scanning.
- Never include PII in exception messages. Pseudonymous IDs (`requestId`, `orderId`, `userId`) are OK.

### Stack Trace Depth Limits (Log4j)

Configure the logging framework to cap stack trace output and prevent log flooding from deeply nested exceptions:

**Log4j2** — use `%xEx{depth}` in the pattern layout:
```xml
<!-- Limits stack traces to 200 lines — prevents log flooding -->
<Property name="LOG_PATTERN">%d{ISO8601} [%X{correlationId}] [%t] %-5p [%c] %m%n%xEx{200}</Property>
```

**Log4j1** — use `%throwable{depth}`:
```properties
log4j.appender.FILE.layout.ConversionPattern=%d [%X{correlationId}] [%t] %-5p [%c] %m%n%throwable{200}
```

- `%xEx{200}` / `%throwable{200}` — print at most 200 lines of stack trace per exception.
- Without this, a single `Caused by:` chain can produce thousands of lines (especially with Spring/AWS SDK stacks).
- `%xEx` (Log4j2) also prints suppressed exceptions — prefer it over `%ex`.

### MDC / Correlation IDs

Use MDC (Mapped Diagnostic Context) to automatically include correlation IDs in every log line:

```java
// Set at request entry point (filter, controller)
MDC.put("requestId", rid);
try {
    // All log lines within this scope automatically include requestId
    service.process(rid);
} finally {
    MDC.remove("requestId");
}
```

```xml
<!-- Reference in log pattern -->
<PatternLayout pattern="%d [%X{requestId}] [%t] %-5p [%c] %m%n%xEx{200}"/>
```

- Set MDC at the request boundary (servlet filter, Lambda handler entry).
- Always clean up in `finally` — MDC is thread-local and leaks across pooled threads if not cleared.
- Use the correlation ID for cross-service tracing (same `requestId` across all services in the call chain).

### Logging
```java
// WRONG — string concatenation (evaluated even if level disabled)
log.debug("Processing user: " + user.getId() + " with " + items.size() + " items");

// CORRECT — parameterized (lazy evaluation)
log.debug("Processing user: {} with {} items", user.getId(), items.size());
```
- Use SLF4J parameterized logging — never string concatenation.
- Use appropriate levels: ERROR (action needed), WARN (concerning), INFO (milestones), DEBUG (diagnostics).
- Log at method boundaries: entry (DEBUG), result (INFO/DEBUG), exceptions (ERROR/WARN).
- Never log PII, credentials, or full request/response bodies in production.

### Async Logging (Non-Blocking)

Synchronous logging blocks the application thread until the log event is written to disk or network (CloudWatch, Kinesis). Under high throughput, this causes latency spikes. **Wrap appenders in async wrappers** to decouple logging from I/O:

**Log4j2** — use `<Async>` wrapper appenders:
```xml
<!-- Synchronous appender (writes to file) -->
<RollingFile name="appLog" fileName="app.log" ...>
    <PatternLayout pattern="${LOG_PATTERN}"/>
</RollingFile>

<!-- Async wrapper — application threads return immediately -->
<Async name="asyncAppLog" bufferSize="8192" blocking="false" includeLocation="true">
    <AppenderRef ref="appLog"/>
</Async>

<!-- Use the async wrapper in loggers, not the raw appender -->
<Logger name="com.myapp" level="INFO">
    <AppenderRef ref="asyncAppLog"/>  <!-- NOT ref="appLog" -->
</Logger>
```

**Key settings:**
- **`bufferSize`** — ring buffer size (default 1024). Increase for high-throughput services (4096–8192). Must be a power of 2.
- **`blocking="false"`** — if the buffer is full, discard events instead of blocking the application thread. Use `true` only if log loss is unacceptable (at the cost of potential thread blocking).
- **`includeLocation="true"`** — preserves `[%F:%L]` (file:line) in log output. Has a small perf cost (stack walking), but critical for debugging. Set to `false` only in extreme high-throughput scenarios.

**When to use async:**
- **Always** for network appenders (CloudWatch, Kinesis, Logstash) — network I/O latency is unpredictable.
- **Recommended** for file appenders under moderate-to-high throughput.
- **Optional** for console appenders in dev/test (low volume, immediate feedback preferred).

**Alternative — Log4j2 `AsyncLogger`** (LMAX Disruptor-based, higher performance than `<Async>` wrapper):
```xml
<!-- In log4j2.xml: make ALL loggers async (highest throughput) -->
<Configuration>
    <Loggers>
        <AsyncLogger name="com.myapp" level="INFO">
            <AppenderRef ref="appLog"/>
        </AsyncLogger>
    </Loggers>
</Configuration>
```
Requires `disruptor` dependency. Use `AsyncLogger` for maximum throughput; use `<Async>` wrapper for selective async without extra dependencies.

### Logging Exception Stack Traces (Critical Gotcha)

**SLF4J** (`org.slf4j.Logger`) has these `error()` overloads — there is **no** `error(String, Object..., Throwable)` combined form:

```java
void error(String msg);                              // plain message
void error(String format, Object arg);               // one placeholder
void error(String format, Object arg1, Object arg2); // two placeholders
void error(String format, Object... arguments);      // varargs placeholders
void error(String msg, Throwable t);                 // message + stack trace
```

SLF4J 1.6+ special-cases the **last** varargs argument if it is a `Throwable` — it prints the stack trace. But this is implicit and fragile:

```java
// WORKS (SLF4J 1.6+) — last arg is Throwable, stack trace IS printed
log.error("Failed for requestId={}", requestId, exception);

// SAFER — explicit two-arg form, intent is clear
log.error(String.format("Failed for requestId=%s", requestId), exception);

// WRONG — Throwable buried in the middle, stack trace NOT printed
log.error("Failed for requestId={} at step={}", requestId, exception, stepName);
```

**Prefer the explicit `error(String, Throwable)` form** when logging exceptions. Build the message string first (via `String.format()` or concatenation), then pass the `Throwable` as the second argument. This works identically across SLF4J and Commons Logging.

**Commons Logging** (`org.apache.commons.logging.Log`) has **no** parameterized logging — only:

```java
void error(Object message);              // plain message
void error(Object message, Throwable t); // message + stack trace
```

For Commons Logging, always build the full message string before calling `error()`:

```java
// CORRECT — Commons Logging
log.error("Failed for requestId=" + requestId, exception);
log.error(String.format("Failed for requestId=%s", requestId), exception);
```

## Design Patterns

### Dependency Injection (DI) — The Core Principle

**Every class receives its external collaborators as interfaces through the constructor.** The application configuration layer (Spring context, Guice module, manual wiring) is the only place that knows which concrete implementation to bind. This is the single most important pattern for testability, loose coupling, and maintainability.

#### The Rule

1. **Define an interface** for every external dependency (database, HTTP client, message publisher, cache, file system, third-party SDK).
2. **Accept interfaces in the constructor** — never instantiate collaborators inside a class.
3. **Let the configuration layer bind** the concrete implementation to the interface.
4. **In tests, pass a mock** — no framework magic needed.

#### Full Example

```java
// 1. INTERFACE — defines the contract. Lives in the service/domain layer.
public interface OrderRepository {
    Optional<Order> findByUserId(String userId);
    void save(Order order);
}

public interface NotificationClient {
    void sendOrderConfirmation(Order order);
}

// 2. IMPLEMENTATION — lives in the infrastructure layer. Knows about DynamoDB.
public class DynamoDbOrderRepository implements OrderRepository {
    private final DynamoDBMapper mapper;

    public DynamoDbOrderRepository(DynamoDBMapper mapper) {
        this.mapper = Objects.requireNonNull(mapper);
    }

    @Override
    public Optional<Order> findByUserId(String userId) {
        return Optional.ofNullable(mapper.load(Order.class, userId));
    }

    @Override
    public void save(Order order) {
        mapper.save(order);
    }
}

// 3. SERVICE — depends ONLY on interfaces. Knows nothing about DynamoDB, HTTP, etc.
public class OrderService {
    private final OrderRepository orderRepository;
    private final NotificationClient notificationClient;

    public OrderService(OrderRepository orderRepository, NotificationClient notificationClient) {
        this.orderRepository = Objects.requireNonNull(orderRepository);
        this.notificationClient = Objects.requireNonNull(notificationClient);
    }

    public void placeOrder(Order order) {
        validateOrder(order);
        orderRepository.save(order);
        notificationClient.sendOrderConfirmation(order);
    }
}

// 4. CONFIGURATION — the ONLY place that knows which implementation to use.
// Spring example:
@Configuration
public class AppConfig {
    @Bean
    public OrderRepository orderRepository(DynamoDBMapper mapper) {
        return new DynamoDbOrderRepository(mapper);
    }

    @Bean
    public NotificationClient notificationClient(HttpClient httpClient) {
        return new HttpNotificationClient(httpClient);
    }

    @Bean
    public OrderService orderService(OrderRepository repo, NotificationClient client) {
        return new OrderService(repo, client);
    }
}

// Guice example:
public class AppModule extends AbstractModule {
    @Override
    protected void configure() {
        bind(OrderRepository.class).to(DynamoDbOrderRepository.class);
        bind(NotificationClient.class).to(HttpNotificationClient.class);
    }
}

// 5. TEST — trivial to mock, no framework needed.
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock private OrderRepository orderRepository;
    @Mock private NotificationClient notificationClient;
    private OrderService orderService;

    @BeforeEach
    void setUp() {
        orderService = new OrderService(orderRepository, notificationClient);
    }

    @Test
    void placeOrder_savesAndNotifies() {
        Order order = buildTestOrder();
        orderService.placeOrder(order);
        verify(orderRepository).save(order);
        verify(notificationClient).sendOrderConfirmation(order);
    }
}
```

#### Anti-Patterns (Never Do This)

```java
// WRONG — field injection. Hidden dependency, mutable, hard to test without framework.
@Service
public class OrderService {
    @Autowired private OrderRepository orderRepository;  // hidden, mutable
}

// WRONG — instantiating a concrete dependency inside the class. Untestable, tightly coupled.
public class OrderService {
    private final OrderRepository repo = new DynamoDbOrderRepository();  // coupled to DynamoDB
}

// WRONG — depending on a concrete class instead of an interface.
public class OrderService {
    private final DynamoDbOrderRepository repo;  // tied to implementation
}
```

#### Why This Matters

- **Testability** — swap real implementations for mocks in one line.
- **Loose coupling** — service logic never changes when you switch databases, HTTP clients, or message brokers.
- **Explicit dependencies** — the constructor signature is the dependency manifest. No hidden surprises.
- **Immutability** — `final` fields set once in the constructor. Thread-safe by default.
- This is the **Gateway** / **Repository** / **Adapter** pattern from Clean Architecture.

### Builder Pattern (for Complex Objects)
```java
Order order = Order.builder()
    .userId(uid)
    .status(status)
    .createdAt(Instant.now())
    .build();
```
- Use for objects with 4+ fields or optional parameters.
- Lombok `@Builder` is acceptable if the project uses Lombok.

### Strategy Pattern (Instead of Switch/If Chains)
```java
// WRONG — growing switch statement
switch (type) {
    case "A": handleA(); break;
    case "B": handleB(); break;
    // ... grows forever
}

// CORRECT — strategy map
Map<String, Handler> handlers = Map.of("A", new HandlerA(), "B", new HandlerB());
handlers.getOrDefault(type, defaultHandler).handle(request);
```

## External Resource Access

### Database Connections

- **Always use a connection pool** — HikariCP (JDBC), AWS SDK client (DynamoDB). Never create connections per-request.
- **Configure timeouts** — connection timeout, socket timeout, and idle timeout to prevent connection leaks.
- **Close resources** — use try-with-resources for `Connection`, `PreparedStatement`, `ResultSet`.
- **Use parameterized queries** — never concatenate user input into SQL/DynamoDB expressions.

```java
// WRONG — no pool, no timeout, resource leak risk
Connection conn = DriverManager.getConnection(url);
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery("SELECT * FROM users WHERE id = '" + id + "'");

// CORRECT — pooled, parameterized, auto-closed
try (Connection conn = dataSource.getConnection();
     PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?")) {
    stmt.setString(1, id);
    try (ResultSet rs = stmt.executeQuery()) {
        // process results
    }
}
```

- **DynamoDB / NoSQL** — reuse `AmazonDynamoDB` / `DynamoDBMapper` as singleton beans (AWS SDK clients are thread-safe).
- **Batch operations** — use `batchGetItem` / `batchWriteItem` instead of single-item calls in a loop.
- **Limit result sets** — always set `withLimit()` on queries. Never scan an entire table.

### HTTP Connections

- **Reuse HTTP clients** — create one `HttpClient` / `CloseableHttpClient` / `RestTemplate` instance and share it (singleton bean). Never create per-request.
- **Configure timeouts** — connect timeout (establish connection), socket/read timeout (wait for data), and connection request timeout (wait for pooled connection).

```java
// Apache HttpClient with timeouts and pooling
RequestConfig requestConfig = RequestConfig.custom()
    .setConnectTimeout(3000)            // 3s to establish connection
    .setSocketTimeout(5000)             // 5s to wait for response data
    .setConnectionRequestTimeout(2000)  // 2s to wait for pooled connection
    .build();

PoolingHttpClientConnectionManager connManager = new PoolingHttpClientConnectionManager();
connManager.setMaxTotal(100);           // max total connections
connManager.setDefaultMaxPerRoute(20);  // max per host

CloseableHttpClient httpClient = HttpClients.custom()
    .setDefaultRequestConfig(requestConfig)
    .setConnectionManager(connManager)
    .build();
```

- **Retry with exponential backoff** — for transient failures (5xx, timeout). Use a library (`spring-retry`, AWS SDK built-in retry). Cap retries (typically 3).
- **Circuit breaker** — for dependencies that may be down for extended periods. Fail fast instead of waiting for timeouts.
- **Close response bodies** — unclosed HTTP responses leak connections from the pool.
- **Never trust external input** — validate response status, content type, and body before processing.

### Caching

Use caching to avoid redundant calls to external resources, reduce latency, and protect downstream services:

```java
// In-memory cache with Guava (Java 8 compatible)
LoadingCache<String, AppConfig> configCache = CacheBuilder.newBuilder()
    .maximumSize(100)
    .expireAfterWrite(10, TimeUnit.MINUTES)
    .build(new CacheLoader<String, AppConfig>() {
        @Override
        public AppConfig load(String configId) {
            return configService.fetchFromRemote(configId);
        }
    });

// Usage — automatically fetches on cache miss
AppConfig config = configCache.get(configId);
```

- **Cache-aside pattern** — check cache first, fetch from source on miss, populate cache.
- **Always set a TTL** (time-to-live) — stale data is usually acceptable for a few minutes. Never cache forever.
- **Bound the cache size** — use `maximumSize()` to prevent unbounded memory growth.
- **Use `ConcurrentHashMap.computeIfAbsent()`** for simple cases that don't need TTL or eviction.
- **Cache at the right layer** — cache in the service/helper layer, not in the controller or DAO.
- **Protection against thundering herd** — `LoadingCache` (Guava) and `Caffeine` handle concurrent loads for the same key automatically (only one thread fetches, others wait).
- **Cache invalidation** — prefer TTL-based expiry over manual invalidation. If you must invalidate, use `cache.invalidate(key)` — never clear the entire cache unless necessary.

## Performance

- **Avoid premature optimization** — measure first with profiling tools.
- **Lazy initialization**: For expensive resources, initialize on first use, not at startup (unless startup time doesn't matter).
- **Streams vs loops**: Streams are readable but can be slower for simple operations. Use loops for performance-critical hot paths. Never use parallel streams unless measured and justified.
- **String interning**: Don't manually `intern()` strings. JVM handles literal interning.
- **Boxing/unboxing**: Prefer primitive types (`int`, `long`) over wrapper types (`Integer`, `Long`) in tight loops and large collections.
- **Batch external calls** — never call a database or HTTP API inside a loop. Collect IDs, batch-fetch, then process.

## Testing

- **One assertion concept per test**: Test one behavior per method. Multiple assertions are OK if they verify one logical outcome.
- **Test naming**: `should[ExpectedBehavior]_when[Condition]` or `methodName_condition_expectedResult`.
- **Given/When/Then**: Structure tests clearly with setup, action, and verification phases.
- **Mock only what you own**: Don't mock third-party libraries directly — wrap them in your own interface.
- **Test behavior, not implementation**: Tests should survive refactoring if behavior doesn't change.

### Unit Tests vs Integration Tests

| Aspect | Unit Tests | Integration Tests |
|--------|-----------|------------------|
| **Scope** | Single class/method in isolation | Multiple components or external systems |
| **Dependencies** | All external deps mocked/stubbed | Real or embedded external deps |
| **Speed** | Milliseconds per test | Seconds to minutes per test |
| **When to run** | Every build, every commit | CI pipeline, pre-merge |
| **Naming** | `*Test.java` | `*IT.java` (Maven Failsafe convention) |
| **Maven phase** | `test` (Surefire) | `verify` (Failsafe) |

- **Unit tests are the foundation** — they should cover all business logic, validation paths, and error handling.
- **Integration tests verify wiring** — that components work together with real infrastructure.
- **Never mix them** — unit tests must not depend on databases, network, or file system.

### Mocking External Dependencies

```java
// Database — mock the repository interface (not the DB driver)
@Mock private OrderRepository orderRepository;
given(orderRepository.findById("order-123")).willReturn(Optional.of(testOrder));

// HTTP API — mock the client interface (not HttpClient internals)
@Mock private ExternalApiClient externalApiClient;
given(externalApiClient.fetchData(request)).willReturn(expectedResponse);

// Message queue — mock the publisher interface
@Mock private EventPublisher eventPublisher;
verify(eventPublisher).publish(any(OrderEvent.class));
```

- **Mock at the interface boundary** — this is why the "Interface-Based Isolation" pattern matters.
- **Never mock `final` classes, static methods, or constructors** — refactor the code to use interfaces instead.
- **Use `@Mock` + `given().willReturn()`** (BDDMockito) for stubbing, `verify()` for interaction checks.

### Integration Testing External Resources

**Databases:**
- Use embedded/in-memory databases for integration tests (H2 for SQL, DynamoDB Local for DynamoDB).
- Use `@Before`/`@After` to set up and tear down test data — never share state between tests.
- Use Testcontainers for production-equivalent databases when in-memory isn't sufficient.

**HTTP APIs:**
- Use WireMock or MockServer to simulate external HTTP endpoints.
- Verify request shape (URL, headers, body) and simulate error responses (400, 500, timeout).

```java
// WireMock example
@Rule public WireMockRule wireMock = new WireMockRule(8089);

@Test
public void shouldHandleTimeoutFromRecommendationApi() {
    stubFor(post("/recommend")
        .willReturn(aResponse().withFixedDelay(10000).withStatus(200)));

    // Should throw or return fallback, not hang forever
    assertThrows(TimeoutException.class,
        () -> client.getRecommendation(request));
}
```

**Message queues:**
- Use embedded brokers (LocalStack for SNS/SQS) or mock the publisher interface in unit tests.

### Testing Exceptions

**JUnit 4** — use `@Test(expected = ...)` for simple "must throw this type" checks:

```java
@Test(expected = NullPointerException.class)
public void shouldThrowWhenDependencyIsNull() {
    new OrderService(null, notificationService);
}
```

- **Good for**: concise one-liner tests where the *type* of exception is all you need to verify.
- **Limitation**: it does not verify *which line* throws or the exception *message*. If setup code accidentally throws the same exception type, the test falsely passes.

When you need to verify the exception **message** or **cause**, use try-catch + `fail()`:

```java
@Test
public void shouldThrowWithContextWhenModelNotFound() {
    try {
        service.getModel("unknown-id");
        fail("Expected ModelNotFoundException");
    } catch (ModelNotFoundException e) {
        assertThat(e.getMessage(), containsString("unknown-id"));
    }
}
```

**JUnit 5** — prefer `assertThrows()` (also available in JUnit 4.13+):

```java
ModelNotFoundException ex = assertThrows(ModelNotFoundException.class,
    () -> service.getModel("unknown-id"));
assertThat(ex.getMessage(), containsString("unknown-id"));
```

## Concurrency

### First Defense: Immutability

The simplest way to prevent race conditions is to **make objects immutable** — if state can't change, it can't be corrupted by concurrent access.

```java
// THREAD-SAFE — immutable object. No synchronization needed. Can be freely shared.
public final class OrderSnapshot {
    private final String orderId;
    private final BigDecimal total;
    private final List<String> itemIds;

    public OrderSnapshot(String orderId, BigDecimal total, List<String> itemIds) {
        this.orderId = orderId;
        this.total = total;
        this.itemIds = List.copyOf(itemIds);  // defensive copy + unmodifiable
    }

    public String getOrderId() { return orderId; }
    public BigDecimal getTotal() { return total; }
    public List<String> getItemIds() { return itemIds; }  // safe — list is unmodifiable
}
```

- **`final` class** — prevents subclasses from adding mutable state.
- **`final` fields** — set once in constructor, visible to all threads after construction (Java Memory Model guarantee).
- **`List.copyOf()`** — defensive copy + unmodifiable. The caller can't mutate the internal list.
- **No setters** — once constructed, the object never changes.

**Rule of thumb**: If an object is shared across threads, make it immutable. If it can't be immutable, synchronize it.

### Race Conditions: Read-Modify-Write

The most common race condition is **read-modify-write** — two threads read the same value, both modify it, and one write overwrites the other.

```java
// WRONG — race condition. Two threads can read count=5, both write 6. One increment lost.
private int count = 0;
public void increment() {
    count++;  // NOT atomic: read count → add 1 → write count
}

// CORRECT — atomic operation. Guaranteed single-threaded increment.
private final AtomicInteger count = new AtomicInteger(0);
public void increment() {
    count.incrementAndGet();  // atomic read-modify-write
}

// WRONG — check-then-act race. Another thread can put between containsKey and put.
if (!map.containsKey(key)) {
    map.put(key, computeValue());
}

// CORRECT — atomic check-then-act.
map.computeIfAbsent(key, k -> computeValue());  // ConcurrentHashMap: atomic and thread-safe
```

### Race Conditions: Shared Mutable Objects

When an object's fields are modified by multiple threads, **every access** (read and write) must be synchronized on the same lock.

```java
// WRONG — unsynchronized mutable state. Thread A calls setStatus() while Thread B calls getStatus().
// Thread B may see a partially updated or stale value.
public class OrderProcessor {
    private String status = "NEW";
    private List<String> errors = new ArrayList<>();

    public void setStatus(String s) { this.status = s; }
    public String getStatus() { return this.status; }
    public void addError(String e) { errors.add(e); }  // ArrayList is not thread-safe
    public List<String> getErrors() { return errors; }  // caller can mutate the list
}

// CORRECT — private lock, synchronized access, defensive copies on reads.
public class OrderProcessor {
    private final Object lock = new Object();
    private String status = "NEW";
    private final List<String> errors = new ArrayList<>();

    public void setStatus(String s) {
        synchronized (lock) { this.status = s; }
    }

    public String getStatus() {
        synchronized (lock) { return this.status; }
    }

    public void addError(String e) {
        synchronized (lock) { errors.add(e); }
    }

    public List<String> getErrors() {
        synchronized (lock) { return List.copyOf(errors); }  // defensive copy
    }
}
```

**Key rules:**
- **Never `synchronized(this)`** — external code can also lock on your instance, causing deadlocks or contention. Use a **private `final Object lock`**.
- **Synchronize both reads and writes** — synchronizing only writes is a bug. Without synchronized reads, the reading thread may see stale cached values (CPU cache / JVM optimization).
- **Return defensive copies** from synchronized getters — returning a mutable reference lets callers modify the object outside the lock.

### Concurrent Collections and Atomics

Prefer `java.util.concurrent` over manual `synchronized`:

| Need | Use | Not |
|------|-----|-----|
| Thread-safe map | `ConcurrentHashMap` | `Collections.synchronizedMap(new HashMap<>())` |
| Thread-safe counter | `AtomicInteger` / `AtomicLong` | `synchronized` + `int` |
| Thread-safe reference swap | `AtomicReference<T>` | `synchronized` + field |
| Thread-safe list (read-heavy) | `CopyOnWriteArrayList` | `Collections.synchronizedList()` |
| Thread-safe queue | `ConcurrentLinkedQueue` / `LinkedBlockingQueue` | manual lock + ArrayList |
| Coordinating threads | `CountDownLatch` / `CyclicBarrier` | `wait()` / `notify()` |

```java
// AtomicReference — thread-safe swap of an immutable snapshot
private final AtomicReference<OrderSnapshot> currentSnapshot = new AtomicReference<>();

public void updateSnapshot(OrderSnapshot newSnapshot) {
    currentSnapshot.set(newSnapshot);  // atomic, visible to all threads
}

public OrderSnapshot getSnapshot() {
    return currentSnapshot.get();  // always sees latest value
}
```

### Thread-Safe Lazy Initialization

```java
// WRONG — race condition. Two threads may both see instance == null and create two instances.
private static ExpensiveResource instance;
public static ExpensiveResource getInstance() {
    if (instance == null) {
        instance = new ExpensiveResource();  // two threads can enter here
    }
    return instance;
}

// CORRECT — thread-safe lazy init using holder pattern (recommended).
// JVM guarantees class loading is synchronized — no explicit locks needed.
public class ExpensiveResourceHolder {
    private static class Holder {
        static final ExpensiveResource INSTANCE = new ExpensiveResource();
    }
    public static ExpensiveResource getInstance() {
        return Holder.INSTANCE;
    }
}
```

### Async Work

- **Prefer `CompletableFuture`** over raw `Thread` or `Runnable` for async work.
- **Use `ExecutorService`** — never create unbounded threads. Always use a pool with a bounded size.
- **Handle exceptions** in async tasks — unhandled exceptions in `CompletableFuture` are silently swallowed unless you call `.join()` or `.get()`.

### Common Concurrency Pitfalls

| Pitfall | Example | Fix |
|---------|---------|-----|
| **Non-atomic read-modify-write** | `count++` on a shared `int` | `AtomicInteger.incrementAndGet()` |
| **Check-then-act** | `if (!map.containsKey(k)) map.put(k, v)` | `map.computeIfAbsent(k, ...)` |
| **Publishing mutable object** | Returning an internal `List` reference | Return `List.copyOf()` |
| **Synchronizing on `this`** | `synchronized(this) { ... }` | Private `final Object lock` |
| **Synchronizing writes but not reads** | Only `set` is synchronized | Synchronize both `get` and `set` |
| **Double-checked locking (broken)** | `if (x == null) { synchronized { if (x == null) ... } }` without `volatile` | Holder pattern or `volatile` field |
| **Modifying a collection while iterating** | `for (Item i : list) list.remove(i)` | `Iterator.remove()` or collect-then-remove |

## Operational Best Practices

### Dynamic Log Levels for Production Troubleshooting

When troubleshooting in production, temporarily change log levels from WARN/ERROR to INFO or DEBUG to get more diagnostic detail:

**Log4j2** — use `monitorInterval` for hot-reload without restart:
```xml
<!-- Checks for config changes every 30 seconds — no restart needed -->
<Configuration monitorInterval="30">
```

To troubleshoot: update the log config file on the server (or via S3/SSM), and Log4j2 picks up the change within `monitorInterval` seconds. **No application restart required.**

**Procedure:**
1. Change the target logger level from `ERROR` → `INFO` (or `DEBUG` for deep investigation).
2. Wait for `monitorInterval` to elapse (or trigger a config reload via JMX).
3. Reproduce the issue and collect logs.
4. **Revert immediately** — INFO/DEBUG in production generates massive log volume and can impact performance and costs.

```xml
<!-- Normal production config -->
<Logger name="com.myapp.service" level="ERROR"/>

<!-- Temporary troubleshooting config -->
<Logger name="com.myapp.service" level="INFO"/>
<!-- Or for deep debugging of a specific class: -->
<Logger name="com.myapp.service.OrderService" level="DEBUG"/>
```

- **Always revert** after troubleshooting — leaving DEBUG on in production causes log flooding, performance degradation, and increased storage costs.
- **Prefer narrow scope** — change the level for a specific class or package, not the root logger.
- **JMX** — Log4j2 exposes logger levels via JMX MBeans, allowing runtime changes without touching config files.
- **Log4j1** — does not support `monitorInterval`. Use `DOMConfigurator.configureAndWatch()` or restart the application.

## Related Skills

- **best-practices** — SOLID principles, layered architecture, resilience patterns (language-agnostic foundations that Java implements)
- **security** — Injection prevention (parameterized queries), auth, secrets management, PII — applies to all Java endpoints handling user data
- **testing** — AC-to-test traceability, test pyramid, coverage checklist — universal testing discipline beyond Java-specific JUnit/Mockito patterns
