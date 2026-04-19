# Testing Best Practices

Universal testing discipline that applies to any project and tech stack. Expanded from rules/testing.md with detailed code examples across Java, Python, and TypeScript.

## Test Discipline — Non-Negotiables

### Never Commit Without Tests Passing

- **Never commit code without ALL related tests passing at 100%.**
- **You are responsible for running and verifying tests** — never ask the user to test on your behalf.
- **Every new or modified method requires test coverage** — happy path + edge cases + exceptions.
- **Always create tests for edge cases** — null/empty inputs, boundary values (zero, negative, max), single-element and large collections, off-by-one, concurrent access, and unexpected types. Edge case tests catch the bugs that happy-path tests miss.
- **Create test file if none exists** — mirror the source path under the test directory.
- **Keep tests DRY** — use named constants, shared builders, reusable fixtures.

### Read Source Before Writing Tests

Always read the actual source code before writing tests. Verify:
- Method signatures (parameter types, return types)
- Overloaded methods (don't test the wrong overload)
- Exception types thrown
- Default values and null behavior

## AC-to-Test Traceability

For every ticket, map each acceptance criterion (AC) to its test(s) **before writing code**. This prevents untested ACs — one of the main drivers of endless review cycles.

### Template

Add as a comment at the top of the primary test file for the ticket:

```
// AC Coverage for ABC-123:
// AC-1: "User can create an order with valid items" → testCreateOrder_validItems()
// AC-2: "Order fails if no items provided" → testCreateOrder_emptyItems_throwsValidation()
// AC-3: "Email sent after successful order" → testCreateOrder_sendsConfirmationEmail()
// AC-4: "Concurrent orders don't corrupt inventory" → [MISSING — add before merge]
```

### Rules

- Each AC maps to **one or more** test names.
- If an AC has no test yet, mark it `[MISSING]` — this is a **merge blocker**.
- If an AC is untestable as written, flag it to the ticket author **before starting implementation**.
- E2E tests count as AC coverage for user-facing, integration-level ACs.

## Test Structure & Patterns

### Arrange-Act-Assert (Given-When-Then)

Every test has exactly three phases, clearly separated.

```java
// Java — JUnit 5
@Test
void placeOrder_validItems_savesAndNotifies() {
    // Arrange
    Order order = OrderBuilder.create()
        .withItem("SKU-001", 2)
        .withCustomerId("customer-123")
        .build();

    // Act
    OrderResult result = orderService.placeOrder(order);

    // Assert
    assertThat(result.isSuccess()).isTrue();
    verify(orderRepository).save(order);
    verify(notificationService).orderPlaced(order);
}
```

```python
# Python — pytest
def test_place_order_valid_items_saves_and_notifies(order_service, mock_repo, mock_notifier):
    # Arrange
    order = build_order(items=[("SKU-001", 2)], customer_id="customer-123")

    # Act
    result = order_service.place_order(order)

    # Assert
    assert result.is_success
    mock_repo.save.assert_called_once_with(order)
    mock_notifier.order_placed.assert_called_once_with(order)
```

```typescript
// TypeScript — Vitest
it("saves and notifies on placeOrder", async () => {
  // Arrange
  const order = buildTestOrder({ items: [{ sku: "SKU-001", qty: 2 }] });

  // Act
  await orderService.placeOrder(order);

  // Assert
  expect(mockRepo.save).toHaveBeenCalledWith(order);
  expect(mockNotifier.sendOrderConfirmation).toHaveBeenCalledWith(order);
});
```

### Named Constants Over Magic Literals

```java
// WRONG — magic values scattered throughout tests
@Test
void testOrder() {
    Order order = new Order("abc", "xyz", 3, 29.99);
    assertThat(order.getTotal()).isEqualTo(89.97);
}

// CORRECT — named constants explain intent
private static final String CUSTOMER_ID = "customer-123";
private static final String SKU = "SKU-001";
private static final int QUANTITY = 3;
private static final BigDecimal UNIT_PRICE = new BigDecimal("29.99");
private static final BigDecimal EXPECTED_TOTAL = new BigDecimal("89.97");

@Test
void placeOrder_calculatesTotal() {
    Order order = OrderBuilder.create()
        .withCustomerId(CUSTOMER_ID)
        .withItem(SKU, QUANTITY, UNIT_PRICE)
        .build();

    assertThat(order.getTotal()).isEqualTo(EXPECTED_TOTAL);
}
```

### One Behavior Per Test

```python
# WRONG — testing multiple unrelated behaviors in one test
def test_order_service():
    result = service.place_order(valid_order)
    assert result.is_success                     # behavior 1: success
    assert repo.save.called                      # behavior 2: persistence
    assert notifier.send.called                  # behavior 3: notification
    with pytest.raises(ValidationError):         # behavior 4: validation
        service.place_order(invalid_order)

# CORRECT — one test per behavior
def test_place_order_succeeds_with_valid_items():
    result = service.place_order(valid_order)
    assert result.is_success

def test_place_order_persists_order():
    service.place_order(valid_order)
    repo.save.assert_called_once_with(valid_order)

def test_place_order_sends_notification():
    service.place_order(valid_order)
    notifier.send.assert_called_once_with(valid_order)

def test_place_order_rejects_empty_items():
    with pytest.raises(ValidationError, match="at least one item"):
        service.place_order(empty_order)
```

### DRY Fixtures — Builders and Factories

```typescript
// Shared test builder — used across all tests in the module
function buildTestOrder(overrides: Partial<Order> = {}): Order {
  return {
    id: "order-001",
    customerId: "customer-123",
    items: [{ sku: "SKU-001", quantity: 1, price: 29.99 }],
    status: "pending",
    createdAt: new Date("2026-01-01"),
    ...overrides,
  };
}

// Tests use the builder with only the relevant overrides
it("rejects empty items", async () => {
  const order = buildTestOrder({ items: [] });
  await expect(service.placeOrder(order)).rejects.toThrow(ValidationError);
});

it("calculates total correctly", async () => {
  const order = buildTestOrder({
    items: [
      { sku: "A", quantity: 2, price: 10.0 },
      { sku: "B", quantity: 1, price: 5.0 },
    ],
  });
  const result = await service.placeOrder(order);
  expect(result.total).toBe(25.0);
});
```

## Mocking & Test Isolation

### Mock at the Interface Boundary

```java
// WRONG — mocking internal implementation details
@Mock private DynamoDBClient dynamoClient;
@Mock private PutItemRequest putRequest;
// Fragile — breaks when you switch from DynamoDB to PostgreSQL

// CORRECT — mock the interface
@Mock private OrderRepository orderRepository;
// Survives infrastructure changes — only the infra layer test changes
```

### Never Mock Private Methods

```python
# WRONG — testing/mocking internal implementation
with mock.patch.object(service, "_calculate_discount"):  # private method
    ...

# CORRECT — test through the public API
result = service.place_order(order_with_discount)
assert result.total == expected_discounted_total
```

### Verify Mock Interactions

```typescript
// Verify the mock was called with the right arguments
expect(mockRepo.save).toHaveBeenCalledWith(
  expect.objectContaining({
    customerId: "customer-123",
    status: "confirmed",
  })
);

// Verify call count
expect(mockNotifier.send).toHaveBeenCalledTimes(1);

// Verify NOT called (negative test)
expect(mockNotifier.send).not.toHaveBeenCalled();
```

## Coverage & Test Pyramid

### The Test Pyramid

```
        /\
       /  \          E2E Tests (few, slow, expensive)
      /____\         - Full stack, browser, real services
     /      \
    /________\       Integration Tests (moderate)
   /          \      - Service + real DB, API contracts
  /____________\
 /              \    Unit Tests (many, fast, cheap)
/________________\   - Single class/function, mocked deps
```

| Level | Count | Speed | What to test |
|-------|-------|-------|-------------|
| **Unit** | Many | Fast | Business logic, edge cases, error paths |
| **Integration** | Moderate | Medium | DB queries, API contracts, service interactions |
| **E2E** | Few | Slow | Critical user journeys, happy paths |

### Coverage Checklist

For every new/modified method, verify:

- [ ] **Happy path** — valid input, expected output
- [ ] **Null/empty inputs** — guard clauses tested
- [ ] **Collection edge cases** — empty list, single element, large list
- [ ] **Exception paths** — verify exception type and message
- [ ] **Boundary conditions** — zero, negative, max values, off-by-one
- [ ] **Async behavior** — await assertions, timeout scenarios (if applicable)

### Test Naming Convention

Tests should read as specifications:

```
// Pattern: methodName_condition_expectedBehavior
placeOrder_validItems_returnsSuccess
placeOrder_emptyItems_throwsValidationError
placeOrder_duplicateSku_mergesQuantities
calculateDiscount_bulkOrder_appliesTierDiscount
```

## Related Skills

This skill provides **universal testing discipline**. Pair it with language-specific testing patterns:

- **java-best-practices** — JUnit 5, Mockito, `assertThrows`, mock-at-interface patterns for Java
- **python-best-practices** — pytest, `Mock(spec=ABC)`, fixtures, given/when/then patterns for Python
- **js-ts-best-practices** — Vitest/Jest, `vi.fn()`, async test patterns, mock-at-interface for TypeScript
- **best-practices** — Architecture patterns (layered, SOLID) that make code testable in the first place
- **security** — Security-specific test cases: injection attempts, auth bypass, PII exposure
