# Mock Classification Reference (mock_usages Taxonomy)

**Status:** Extraction phase enhancement — Comprehensive mock classification rules and methodology  
**Objective:** Document classification rules for `mock_style` and `target_layer` to enable analysis of mock object design patterns

---

## Overview

Mock objects detected within test fixtures are classified along two dimensions:

1. **mock_style** — The type of mock object and how it's configured
   - Categories: `stub`, `mock`, `spy`, `fake`
2. **target_layer** — The architectural layer being mocked
   - Categories: `boundary`, `infrastructure`, `internal`, `framework`

This classification enables research questions like:
- RQ2: "What types of dependencies do test fixtures mock?" (by target_layer)
- RQ3: "What mock patterns are prevalent?" (by mock_style)

---

## Part 1: mock_style Classification

**Definition:** The technique used to create and configure the mock object.

### Category Definitions

#### 1. `stub`
**Definition:** A minimal implementation that returns canned responses without behavior tracking.

**Characteristics:**
- Returns hardcoded values
- No assertion capability (not verified in test)
- Minimal configuration
- Used to isolate the unit under test from dependencies

**Detection Heuristics:**
- Mock with only `.return_value = ...` or `.thenReturn(...)` configuration
- No `.verify()`, `.assert_called()`, or `.was_called_with()` patterns
- Simple return statements without side effects
- Frameworks: All (mockito, unittest_mock, jest, etc.)

**Examples:**

*Python (unittest_mock):*
```python
@pytest.fixture
def mock_db():
    db = Mock()
    db.query.return_value = [{"id": 1, "name": "test"}]  # stub: only returns value
    return db
```

*Java (Mockito):*
```java
@Before
public void setup() {
    database = mock(Database.class);
    when(database.find(1)).thenReturn(testRecord);  // stub: simple canned response
}
```

#### 2. `mock`
**Definition:** A full spy that records all method calls and optionally verifies them in assertions.

**Characteristics:**
- Records method calls and parameters
- Can verify calling patterns post-test
- May have return values configured
- Used to verify interaction contracts between objects
- Can track call counts, parameters, order of calls

**Detection Heuristics:**
- Contains `.assert_called()`, `.verify()`, `.was_called_with()` patterns
- Uses Mockito `.verify(mock).methodName(...)` patterns
- Jest `.toHaveBeenCalled()` assertions
- Sinon `.calledWith()` assertions
- Configured with response AND verification logic

**Examples:**

*Python (unittest_mock):*
```python
@pytest.fixture
def auth_mock():
    auth = Mock()
    auth.login.return_value = True
    # Test will verify: auth.login.assert_called_once_with("user")
    return auth
```

*Java (Mockito):*
```java
@Before
public void setup() {
    listener = mock(EventListener.class);
    // Later in test: verify(listener).onEvent(any());
}
```

#### 3. `spy`
**Definition:** A partial mock that wraps a real object and records calls while allowing real method execution.

**Characteristics:**
- Wraps real object (not a fake implementation)
- Records method interactions
- Allows selective method stubbing (`.when(...).thenReturn()`)
- Combines benefits of spies and mocks: real behavior + verification
- Used to test that code interacts correctly with existing objects

**Detection Heuristics:**
- Uses spy/wrap creation: `spy(object)`, `Mockito.spy()`, `jest.spyOn()`
- Has both real method calls AND mocked interactions
- Verify patterns present (like mock) but with wrapped object
- Partial mocking: `.when().thenReturn()` on subset of methods

**Examples:**

*Python (unittest_mock):*
```python
@pytest.fixture
def logger_spy():
    logger = logging.getLogger()
    with patch.object(logger, 'warn') as warn_spy:
        warn_spy.return_value = None
        yield warn_spy
    # Real logging still works, but warn() is tracked
```

*Java (Mockito):*
```java
@Before
public void setup() {
    realService = new UserService();
    serviceSpy = spy(realService);  // spy: wraps real object
    doReturn(testUser).when(serviceSpy).getUser(1);  // selectively stub
}
```

*JavaScript (Jest):*
```javascript
function mockRepository() {
    const repo = new UserRepository();
    jest.spyOn(repo, 'findById').mockResolvedValue(testUser);
    return repo;
}
```

#### 4. `fake`
**Definition:** A simplified, functional implementation that provides working behavior but without actual production side effects.

**Characteristics:**
- Has actual implementation logic (not just canned responses)
- Provides realistic interface (implements same contract as real object)
- Much simpler than production implementation
- No external dependencies (in-memory, filesystem-free, etc.)
- Examples: in-memory database, FileSystem mock, in-memory cache

**Detection Heuristics:**
- Mock with complex logic or multiple method implementations
- Custom implementation classes (not framework-provided Mock objects)
- In-memory implementations (dict, list used as database)
- Method calls that have branching logic (if/then)
- Manual custom implementations: `class FakeRepository implements Repository`

**Examples:**

*Python:*
```python
class FakeDatabase:  # fake: custom implementation
    def __init__(self):
        self.data = {}  # in-memory storage
    
    def query(self, sql):
        # Custom logic, not just return_value
        return [v for v in self.data.values() if v["active"]]
    
    def insert(self, record):
        self.data[record["id"]] = record

@pytest.fixture
def db():
    return FakeDatabase()
```

*Java:*
```java
class InMemoryUserRepository implements UserRepository {  // fake: custom impl
    private List<User> users = new ArrayList<>();
    
    @Override
    public User findById(int id) {
        return users.stream().filter(u -> u.getId() == id).findFirst().orElse(null);
    }
    
    @Override
    public void save(User user) {
        users.add(user);
    }
}
```

---

### mock_style Detection Algorithm

```python
def classify_mock_style(fixture_code: str, mock_framework: str) -> Optional[str]:
    """
    Classify a single mock instance based on configuration patterns.
    
    Classification priority:
    1. fake: Check for custom class definition
    2. spy: Check for spy/wrap patterns
    3. mock: Check for verify/assertion patterns
    4. stub: Default (only return_value patterns)
    """
    
    # Priority 1: Fake objects (custom implementations)
    if has_custom_implementation(fixture_code):
        return "fake"
    
    # Priority 2: Spy (wrap/spy patterns)
    if mock_framework == "unittest_mock" and "patch.object" in fixture_code:
        return "spy"
    if mock_framework == "mockito" and re.search(r"spy\s*\(", fixture_code):
        return "spy"
    if mock_framework == "jest" and "spyOn" in fixture_code:
        return "spy"
    if mock_framework == "sinon" and "spy(" in fixture_code:
        return "spy"
    
    # Priority 3: Mock (verify/assert patterns)
    verify_patterns = [
        r"\.verify\s*\(",  # Mockito
        r"assert_called",  # unittest_mock
        r"\.toHaveBeenCalled",  # Jest
        r"calledWith\(",  # Sinon
        r"was_called_with",  # Mockito
    ]
    if any(re.search(p, fixture_code) for p in verify_patterns):
        return "mock"
    
    # Default: Stub (only return value configured)
    return "stub"


def has_custom_implementation(snippet: str) -> bool:
    """Check if mock is a custom class implementation (fake)."""
    # Look for class definition or complex branching logic
    if re.search(r"^class\s+\w+", snippet, re.MULTILINE):
        return True  # Custom class definition found
    if re.search(r"(if |for |while |switch )", snippet):
        return True  # Complex logic suggests implementation, not stub
    return False
```

---

## Part 2: target_layer Classification

**Definition:** The architectural layer or system component being mocked.

### Architectural Layers

#### 1. `boundary`
**Definition:** External system interfaces and third-party integrations.

**Characteristics:**
- HTTP APIs, REST services, web services
- Third-party SDKs and libraries
- Payment gateways, authentication services
- Cloud services (AWS, Azure, GCP)
- Email services, messaging services (Twilio, SendGrid)

**Detection Heuristics:**
- Mock target contains framework names: `requests`, `httplib`, `urllib`, `axios`, `fetch`
- Service names: `PaymentService`, `EmailService`, `AuthService`, `ApiClient`
- Third-party libraries: `stripe`, `github`, `google`, `aws_sdk`
- URL patterns in target_identifier

**Examples:**
```python
# mock_style=stub, target_layer=boundary
with patch('requests.get') as mock_req:  # External HTTP API
    mock_req.return_value.json.return_value = {"status": "ok"}

with patch('stripe.Charge.create') as mock_charge:  # External payment service
    mock_charge.return_value = {"id": "ch_123"}

# mock_style=mock, target_layer=boundary
mock_auth = Mock()
verify(mock_auth).authenticate(user)  # Verifying interaction with auth service
```

#### 2. `infrastructure`
**Definition:** System infrastructure and persistence layers.

**Characteristics:**
- Databases (SQL, NoSQL, document stores)
- Caches (Redis, Memcached)
- Message queues (RabbitMQ, Kafka)
- File systems
- Logging systems
- Configuration stores

**Detection Heuristics:**
- Mock target contains: `database`, `db`, `cache`, `redis`, `mongo`, `sql`, `logger`
- Contains data persistence keywords: `repository`, `dao`, `store`
- File operations: `file`, `filesystem`, `path`, `os.path`
- Message queue names: `queue`, `kafka`, `rabbitmq`, `pubsub`

**Examples:**
```python
# mock_style=fake, target_layer=infrastructure
class FakeDatabase:  # Custom in-memory database
    def query(self, sql):
        return self.records

# mock_style=stub, target_layer=infrastructure
with patch('redis.Redis') as mock_redis:
    mock_redis.get.return_value = b"cached_value"

# mock_style=mock, target_layer=infrastructure
mock_repo = Mock(Repository)
mock_repo.save.return_value = user
verify(mock_repo).save(user)
```

#### 3. `internal`
**Definition:** Internal application components and domain logic.

**Characteristics:**
- Service classes (UserService, OrderService)
- Repository patterns for application data
- Business logic components
- Domain models
- Application-specific utilities
- Helper classes

**Detection Heuristics:**
- Mock target matches application namespace/package
- Contains domain concepts: `User`, `Order`, `Product`, `Customer`
- Service class names ending with `Service` (within same codebase)
- No external framework dependency names
- Intra-application imports

**Examples:**
```python
# mock_style=mock, target_layer=internal
user_service = Mock(UserService)
user_service.create.return_value = User(id=1, name="test")
verify(user_service).create(user_data)

# mock_style=stub, target_layer=internal
email_service = Mock()
email_service.send.return_value = True

# Real example: mocking OrderRepository (internal)
order_repo_mock = Mock(OrderRepository)
order_repo_mock.find_by_customer.return_value = [order1, order2]
```

#### 4. `framework`
**Definition:** Core testing and application framework components.

**Characteristics:**
- Testing frameworks themselves (pytest fixtures, JUnit rules)
- Application framework services (Spring, Django, FastAPI)
- Dependency injection containers
- HTTP request/response objects
- Database connection handling frameworks
- ORM framework components (SQLAlchemy, JPA)

**Detection Heuristics:**
- Framework package names: `pytest`, `unittest`, `junit`, `spring`, `django`, `fastapi`
- Contains framework classes: `Request`, `Response`, `Session`, `Engine`
- Mock target includes framework names in fully-qualified name
- Framework-specific mocking patterns

**Examples:**
```python
# mock_style=stub, target_layer=framework
mock_request = Mock()
mock_request.headers = {"Authorization": "Bearer token"}

# mock_style=mock, target_layer=framework
@patch('django.http.HttpResponse')
def test_view(mock_response):
    # Testing against Django framework response
    verify(mock_response).status_code = 200

# Spring framework example
@Mock
private MockMvc mockMvc;  // target_layer=framework
```

---

### target_layer Detection Algorithm

```python
def classify_target_layer(target_identifier: str, mock_framework: str, fixture_code: str) -> str:
    """
    Classify mock target by architectural layer.
    
    Classification priority:
    1. framework: Check for framework packages/classes
    2. boundary: Check for external service patterns
    3. infrastructure: Check for persistence layer patterns
    4. internal: Default (application domain classes)
    """
    
    target_lower = target_identifier.lower()
    
    # Priority 1: Framework layer
    framework_keywords = [
        'pytest', 'unittest', 'junit', 'spring', 'django', 'fastapi',
        'request', 'response', 'session', 'engine', 'httpresponse',
        'servletrequest', 'httpservletresponse', 'mockmvc'
    ]
    if any(kw in target_lower for kw in framework_keywords):
        return "framework"
    
    # Priority 2: Boundary (external services)
    boundary_keywords = [
        'requests', 'urllib', 'httplib', 'axios', 'fetch',
        'stripe', 'paypal', 'aws', 'azure', 'gcp',
        'gmail', 'email', 'twilio', 'sendgrid',
        'github', 'gitlab', 'apikey', 'api_'
    ]
    if any(kw in target_lower for kw in boundary_keywords):
        return "boundary"
    
    # Priority 3: Infrastructure (persistence/storage)
    infrastructure_keywords = [
        'database', 'db', 'cache', 'redis', 'mongo', 'sql', 'postgres',
        'repository', 'dao', 'store', 'logger',
        'file', 'filesystem', 'path', 'queue', 'kafka', 'rabbitmq'
    ]
    if any(kw in target_lower for kw in infrastructure_keywords):
        return "infrastructure"
    
    # Default: Internal (application domain)
    return "internal"
```

---

## Part 3: Integration with Detection Pipeline

### Current State

Mock detection occurs in `detector.py`:

```python
def _extract_mocks(node, src_bytes: bytes) -> list[MockResult]:
    """Extract mock framework calls and basic metadata."""
    # Returns MockResult(framework, target_identifier, num_interactions_configured, raw_snippet)
```

Currently, `mock_style` and `target_layer` are stored in database schema but **not populated** during detection.

### Phase 3 Implementation Plan

**Task 1: Add classification to MockResult dataclass**
```python
@dataclass
class MockResult:
    framework: str
    target_identifier: str
    num_interactions_configured: int
    raw_snippet: str
    mock_style: Optional[str] = None  # NEW: stub/mock/spy/fake
    target_layer: Optional[str] = None  # NEW: boundary/infra/internal/framework
```

**Task 2: Implement classification functions in detector.py**
```python
def classify_mock_style(snippet: str, framework: str) -> str:
    """Classify mock object type (stub/mock/spy/fake)."""
    # See algorithm above

def classify_target_layer(target_id: str, framework: str, snippet: str) -> str:
    """Classify mocked target layer (boundary/infrastructure/internal/framework)."""
    # See algorithm above
```

**Task 3: Update _extract_mocks to populate classifications**
```python
def _extract_mocks(node, src_bytes: bytes) -> list[MockResult]:
    # ... existing detection code ...
    
    for m in re.finditer(pattern, text):
        # ... extract basic info ...
        
        # NEW: Classify mock_style and target_layer
        mock_style = classify_mock_style(snippet, framework)
        target_layer = classify_target_layer(target, framework, snippet)
        
        found.append(
            MockResult(
                framework=framework,
                target_identifier=target,
                num_interactions_configured=interactions,
                raw_snippet=snippet,
                mock_style=mock_style,  # NEW
                target_layer=target_layer,  # NEW
            )
        )
```

**Task 4: Update database insertion to save classifications**
```python
def insert_mock_usage(conn, fixture_id: int, repo_id: int, mock: MockResult):
    conn.execute(
        """INSERT INTO mock_usages 
           (fixture_id, repo_id, framework, mock_style, target_layer, ...)
           VALUES (?, ?, ?, ?, ?, ...)""",
        (fixture_id, repo_id, mock.framework, mock.mock_style, mock.target_layer, ...)
    )
```

---

## Part 4: Validation & Testing

### Test Cases

Mock classification test suite should cover:

1. **mock_style classification:**
   - Stub detection: simple return_value patterns
   - Mock detection: verify/assert patterns
   - Spy detection: spy/wrap patterns
   - Fake detection: custom implementation classes

2. **target_layer classification:**
   - Boundary: external service mocks (Stripe, requests, etc.)
   - Infrastructure: database/cache/logger mocks
   - Internal: application domain mocks (UserService, etc.)
   - Framework: testing framework and dependency injection mocks

3. **Integration tests:**
   - Mocks detected in real test fixtures
   - Classification consistency across frameworks
   - Handling of complex multi-layered mocks

### Known Limitations

1. **Heuristic-based classification:** Regex patterns may have false positives/negatives
   - Workaround: Manual verification on random sample
   - Future: Machine learning classifier if accuracy issues arise

2. **Custom implementations:** Detecting fake objects requires AST analysis
   - Current approach: Look for class definitions and branching logic
   - Limitation: May miss implicit fakes

3. **Ambiguous cases:** Some mocks span multiple layers
   - Guidance: Classify by primary responsibility
   - Example: Spring MockMvc spans framework + boundary layers → classify as framework

4. **Framework-specific patterns:** Each framework has unique syntax
   - All frameworks covered: mockito, unittest_mock, pytest_mock, jest, sinon, gomock, testify
   - Limitation: New frameworks would require pattern additions

---

## Usage Examples

### Example 1: Fixture with Multiple Mock Styles

```python
@pytest.fixture
def user_service():
    # Fake: Custom in-memory implementation
    class FakeUserDb:
        def __init__(self):
            self.users = {}
        def get(self, id):
            return self.users.get(id)
        def save(self, user):
            self.users[user.id] = user
    
    # Stub: External service with return_value only
    auth_service = Mock()
    auth_service.validate_token.return_value = True
    
    # Spy: Real service with one method mocked
    email_service = Mock()
    email_service.send.return_value = True
    
    service = UserService(
        db=FakeUserDb(),  # target_layer=infrastructure, mock_style=fake
        auth=auth_service,  # target_layer=boundary, mock_style=stub
        email=email_service  # target_layer=boundary, mock_style=spy
    )
    return service
```

**Classification Results:**
| Mock | Framework | mock_style | target_layer | Rationale |
|------|-----------|-----------|-------------|-----------|
| FakeUserDb | unittest_mock | fake | infrastructure | Custom implementation of persistence layer |
| auth_service | unittest_mock | stub | boundary | External auth service, only return_value |
| email_service | unittest_mock | spy | boundary | Partial real behavior, one method mocked |

### Example 2: Complex Mock with Verification

```java
@Fixture
public void testOrderProcessing() {
    // Mock: Customer repository with verification
    customerRepo = mock(CustomerRepository.class);
    when(customerRepo.findById(1)).thenReturn(testCustomer);
    
    // Later in test:
    verify(customerRepo).findById(1);  // → mock_style = "mock"
    
    // → target_layer = "internal" (CustomerRepository is app domain)
}
```

---

## References

**Related Documentation:**
- [04-data-collection.md](../data/04-data-collection.md) — Tool versions for mock framework detection
- [11-detection.md](../architecture/11-detection.md) — Complete detection methodology including mock extraction
- [16-fixture-patterns-reference.md](16-fixture-patterns-reference.md) — Fixture type reference
- [14-testing.md](14-testing.md) — Testing approach and validation

**Academic Context:**
For research papers discussing mock object patterns, use this section to explain:
- How mock styles were classified (heuristic algorithm with XYZ accuracy)
- What architectural layers were analyzed (all 4 major layers)
- Validation approach (manual verification on N% sample)
- Limitations and threats to validity
