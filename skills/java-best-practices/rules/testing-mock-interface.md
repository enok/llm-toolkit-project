---
title: Mock at the Interface Boundary
impact: MEDIUM
impactDescription: Clean tests that survive implementation changes
tags: java, testing, mockito, interfaces, unit-test
---

## Mock at the Interface Boundary

Mock the interface, not the concrete implementation or low-level internals.

**Incorrect (mocking concrete class internals):**

```java
@Mock private DynamoDBMapper mapper;  // tied to DynamoDB implementation
```

**Correct (mocking the interface):**

```java
@Mock private OrderRepository orderRepository;
given(orderRepository.findById("order-123")).willReturn(Optional.of(testOrder));

@Mock private ExternalApiClient externalApiClient;
given(externalApiClient.fetchData(request)).willReturn(expectedResponse);

@Mock private EventPublisher eventPublisher;
verify(eventPublisher).publish(any(OrderEvent.class));
```

- This is why Interface-Based Isolation matters — testability
- Never mock `final` classes, static methods, or constructors — refactor to use interfaces
- Use `@Mock` + `given().willReturn()` (BDDMockito) for stubbing, `verify()` for interactions
