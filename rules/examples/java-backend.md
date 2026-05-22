# Java Backend Rules (Template)

> **This is a template.** Copy and fill in your project's Java backend conventions.

## Code Style

[Define your project's brace style, spacing, and naming conventions.]

```java
// Example: Allman braces
if (condition)
{
    doSomething();
}

// Example: K&R braces
if (condition) {
    doSomething();
}
```

**Collections:**
```java
List<String> items = new ArrayList<>();  // use diamond operator
items.isEmpty();                          // NOT items.size() == 0
```

## Annotation Usage

[List annotations commonly used in your project, e.g.:]

```java
// Lombok (if used)
@Data           // getters + setters + equals + hashCode + toString
@Builder        // builder pattern
@Slf4j          // logger

// Spring (if used)
@Service
@Repository
@RestController
```

## REST Endpoint Pattern

```java
// [Show your project's standard REST pattern]
@RestController
@RequestMapping("/api/v1/entity")
public class EntityController {

    private final EntityService entityService;

    @GetMapping("/{id}")
    @PreAuthorize("hasAuthority('VIEW_ENTITY')")  // always add authorization
    public ResponseEntity<EntityDto> getById(@PathVariable Long id) {
        return ResponseEntity.ok(entityService.getById(id));
    }
}
```

## Service Layer Pattern

```java
@Service
public class EntityServiceImpl implements EntityService {

    private final EntityRepository entityRepository;
    private final EntityMapper entityMapper;

    @Override
    public EntityDto getById(Long id) {
        Entity entity = entityRepository.findById(id)
            .orElseThrow(() -> new NotFoundException("Entity not found: " + id));
        return entityMapper.toDto(entity);
    }
}
```

## Multi-tenancy (if applicable)

[Describe how tenant isolation works in your project, e.g.:]

```java
// All queries must filter by tenant
Long tenantId = securityContext.getTenantId();
List<Entity> results = entityRepository.findByTenantId(tenantId);
```

## Feature Flags (if applicable)

```java
if (featureFlags.isEnabled("MY_FEATURE")) {
    // new behavior
}
```

## Database Migrations

- **Location:** `[your migration directory]`
- **Naming:** `V{timestamp}__{description}.sql`
- **Run:** `[your migration command]`
- **Never modify existing migration files**

## Testing

```java
// [Show your project's test pattern]
@ExtendWith(MockitoExtension.class)
class EntityServiceTest {

    private static final Long TEST_ID = 42L;

    @Mock private EntityRepository entityRepository;
    @Mock private EntityMapper entityMapper;

    private EntityServiceImpl entityService;

    @BeforeEach
    void setUp() {
        entityService = new EntityServiceImpl(entityRepository, entityMapper);
    }

    @Test
    void getById_returnsDto() { ... }
}
```

## Running Tests

```bash
# [Your project's test commands]
# Maven:  mvn test -pl module -Dtest=TestClass
# Gradle: ./gradlew :module:test --tests "TestClass"
```
